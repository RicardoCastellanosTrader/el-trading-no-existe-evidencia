"""Estudio de Capacidad de Información — FASE 1 (batería D1-D6) + FASE 2 (tabla + veredicto).

READ-ONLY. Sin GPU. Sin imports de live/*. Solo parsea métricas YA computadas:
  - Nivel 1 (screen, N~13.5k): regime_wf/*_specialist_configs.json (45 productivos).
  - Nivel 2 (ancla, N=60): bloque2c_smoke_c_results.csv + bloque2c_fase_a_results.csv.

Pre-registro CONGELADO 2026-06-16 (T3.1): m=6 primarios, FDR-BH q=0.10 + Bonferroni ref,
unidad = ρ Spearman within (símbolo,clúster) -> media de ~135 ρ; CI por bootstrap de SÍMBOLOS.
Interpretación N1 asimétrica: ρ≈0 => MUERTA; señal => CANDIDATA (no confirmada).
"""
import os, sys, json, glob, csv
import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # combolab/
RNG = np.random.default_rng(20260616)  # semilla fija registrada
N_BOOT = 10000

# ---------- estadística (sin scipy) ----------
def spearman(x, y):
    x = np.asarray(x, float); y = np.asarray(y, float)
    n = len(x)
    if n < 4 or np.all(x == x[0]) or np.all(y == y[0]):
        return np.nan
    rx = _rankdata(x); ry = _rankdata(y)
    rx -= rx.mean(); ry -= ry.mean()
    d = np.sqrt((rx**2).sum() * (ry**2).sum())
    return float((rx*ry).sum()/d) if d > 0 else np.nan

def _rankdata(a):
    order = np.argsort(a, kind="mergesort")
    ranks = np.empty(len(a), float)
    sa = a[order]
    i = 0
    while i < len(a):
        j = i
        while j+1 < len(a) and sa[j+1] == sa[i]:
            j += 1
        ranks[order[i:j+1]] = (i + j)/2.0 + 1
        i = j+1
    return ranks

def auc_mwu(scores, labels):
    """AUC = P(score|pos > score|neg). labels: 1=evento(fracaso), 0=no."""
    scores = np.asarray(scores, float); labels = np.asarray(labels, int)
    pos = scores[labels == 1]; neg = scores[labels == 0]
    if len(pos) == 0 or len(neg) == 0:
        return np.nan
    r = _rankdata(np.concatenate([pos, neg]))
    auc = (r[:len(pos)].sum() - len(pos)*(len(pos)+1)/2.0) / (len(pos)*len(neg))
    return float(auc)

def kruskal_eps2(values, groups):
    """epsilon^2 del efecto de 'groups' sobre 'values' (Kruskal-Wallis). [0,1]."""
    values = np.asarray(values, float); groups = np.asarray(groups)
    n = len(values)
    uniq = np.unique(groups)
    if n < 6 or len(uniq) < 2:
        return np.nan
    r = _rankdata(values)
    H = 12.0/(n*(n+1)) * sum(len(r[groups==g])*(r[groups==g].mean())**2 for g in uniq) - 3*(n+1)
    return float(max(0.0, (H - (len(uniq)-1)) / (n - len(uniq)))) if n > len(uniq) else np.nan

# ---------- carga Nivel 1: JSONs productivos ----------
FIELDS = ["pf_tr","trades_tr","pnl_tr","sqn_combined","sqn_p5","sqn_n_neighbors",
          "pf_robustness","plateau_ratio","cross_cluster_survival","adjacent_worst_pf",
          "maxdd_worst","ci_width","specialist_score","pf_fwd","pf_fwd_ci_low",
          "pf_fwd_ci_high","pnl_fwd","trades_fwd"]

def load_n1():
    rows = []
    files = sorted(glob.glob(os.path.join(ROOT, "regime_wf", "*_specialist_configs.json")))
    files = [f for f in files if "_pre_" not in os.path.basename(f) and "backup" not in f]
    for f in files:
        d = json.load(open(f, encoding="utf-8"))
        sym = d.get("symbol", os.path.basename(f).split("_")[0]).replace("/","")
        for cl_id, c in d.get("clusters", {}).items():
            for cfg in c.get("top_configs", []):
                r = {"symbol": sym, "cluster": int(cl_id)}
                for k in FIELDS:
                    v = cfg.get(k, np.nan)
                    if isinstance(v, bool): v = int(v)
                    r[k] = v
                rows.append(r)
    return rows, len(files)

# ---------- bootstrap por símbolo del estimador within-cell ----------
def within_cell_rho(rows, xcol, ycol):
    """Media de ρ Spearman within (símbolo,clúster). Devuelve (media, lista_de_rhos, mapa_sym->rhos)."""
    by_sym = {}
    for r in rows:
        by_sym.setdefault(r["symbol"], {}).setdefault(r["cluster"], []).append(r)
    sym_rhos = {}
    for sym, cls in by_sym.items():
        rs = []
        for cl, group in cls.items():
            x = [g[xcol] for g in group]; y = [g[ycol] for g in group]
            rho = spearman(x, y)
            if not np.isnan(rho): rs.append(rho)
        if rs: sym_rhos[sym] = rs
    allr = [v for rs in sym_rhos.values() for v in rs]
    return (float(np.mean(allr)) if allr else np.nan), allr, sym_rhos

def boot_by_symbol(sym_rhos, reps=N_BOOT):
    """CI95 + p two-sided remuestreando SÍMBOLOS. Estadístico = media de los ρ within-cell."""
    syms = list(sym_rhos.keys())
    if not syms: return (np.nan, np.nan, np.nan)
    means = np.empty(reps)
    for b in range(reps):
        pick = RNG.choice(len(syms), len(syms), replace=True)
        vals = [v for i in pick for v in sym_rhos[syms[i]]]
        means[b] = np.mean(vals)
    lo, hi = np.percentile(means, [2.5, 97.5])
    p = 2*min((means > 0).mean(), (means < 0).mean())
    return float(lo), float(hi), float(min(1.0, p))

def boot_by_symbol_stat(rows, statfn, reps=N_BOOT):
    """Bootstrap de SÍMBOLOS para un estadístico pooled-per-symbol arbitrario (AUC, eps2)."""
    by_sym = {}
    for r in rows: by_sym.setdefault(r["symbol"], []).append(r)
    syms = list(by_sym.keys())
    obs_vals = [statfn(by_sym[s]) for s in syms]
    obs_vals = [v for v in obs_vals if not np.isnan(v)]
    obs = float(np.mean(obs_vals)) if obs_vals else np.nan
    means = []
    for b in range(reps):
        pick = RNG.choice(len(syms), len(syms), replace=True)
        vals = [statfn(by_sym[syms[i]]) for i in pick]
        vals = [v for v in vals if not np.isnan(v)]
        if vals: means.append(np.mean(vals))
    means = np.array(means)
    if len(means) == 0:
        return obs, np.nan, np.nan, means
    lo, hi = np.percentile(means, [2.5, 97.5])
    return obs, float(lo), float(hi), means

# ---------- multiplicidad ----------
def fdr_bh(pvals, q=0.10):
    p = np.array(pvals, float); m = len(p)
    order = np.argsort(p); thresh = q*(np.arange(1, m+1))/m
    passed = p[order] <= thresh
    kmax = np.where(passed)[0].max()+1 if passed.any() else 0
    out = np.zeros(m, bool)
    if kmax > 0:
        cut = p[order][kmax-1]
        out = p <= cut
    return out, (0.05/m)

# ================= EJECUCIÓN =================
def main():
    print("="*90)
    print("ESTUDIO DE CAPACIDAD DE INFORMACIÓN — FASE 1+2 (read-only, sin GPU)")
    print("="*90)

    rows, nfiles = load_n1()
    print(f"\nNivel 1: {nfiles} JSONs productivos -> {len(rows)} configs (45 sym x 3 clúster x ~100)")

    # higiene: pf_fwd finito, trades_fwd>0
    clean = []
    n_inf = n_notrade = 0
    for r in rows:
        pf = r["pf_fwd"]
        if r["trades_fwd"] in (0, None) or (isinstance(r["trades_fwd"], float) and r["trades_fwd"]==0):
            n_notrade += 1; continue
        if pf is None or not np.isfinite(pf):
            n_inf += 1; continue
        clean.append(r)
    print(f"Higiene: descartados {n_inf} pf_fwd no-finito + {n_notrade} trades_fwd=0 -> N útil = {len(clean)}")
    # winsorize pf_fwd p1/p99 (documentado; Spearman robusto pero cap inf-residual)
    pfv = np.array([r["pf_fwd"] for r in clean]); p1,p99 = np.percentile(pfv,[1,99])
    for r in clean: r["pf_fwd"] = float(min(max(r["pf_fwd"],p1),p99))
    print(f"Winsorize pf_fwd a [p1={p1:.2f}, p99={p99:.2f}]")
    print(f"pf_fwd útil: mean={pfv.mean():.3f} median={np.median(pfv):.3f} | <1: {(pfv<1).mean()*100:.1f}% | >=1.5: {(pfv>=1.5).mean()*100:.1f}%")

    results = {}  # dim -> dict

    # ---- D2: ρ(pf_robustness, pf_fwd) ----
    m,_,sr = within_cell_rho(clean, "pf_robustness", "pf_fwd")
    lo,hi,p = boot_by_symbol(sr)
    results["D2"] = dict(name="Estab. cross-régimen (pf_robustness)", stat="rho", est=m, lo=lo, hi=hi, p=p)

    # ---- D5: ρ(ci_width, pf_fwd) ----
    m,_,sr = within_cell_rho(clean, "ci_width", "pf_fwd")
    lo,hi,p = boot_by_symbol(sr)
    results["D5"] = dict(name="Dispersión (ci_width)", stat="rho", est=m, lo=lo, hi=hi, p=p)

    # ---- D6: ρ(specialist_score, pf_fwd) ----
    m,_,sr = within_cell_rho(clean, "specialist_score", "pf_fwd")
    lo,hi,p = boot_by_symbol(sr)
    results["D6"] = dict(name="Score compuesto (specialist_score)", stat="rho", est=m, lo=lo, hi=hi, p=p)

    # ---- D4: AUC(plateau_ratio -> fracaso pf_fwd<1) ----
    # HALLAZGO: top_configs filtran TODO fracaso forward -> base rate de pf_fwd<1 ~0 en N1.
    fail_rate = float(np.mean([1 if r["pf_fwd"] < 1 else 0 for r in clean]))
    if fail_rate < 0.01:
        results["D4"] = dict(name="Perfil de fracaso — NO EVALUABLE N1 (%.2f%% fracasos: filtrados por selección)" % (fail_rate*100),
                             stat="AUC", est=np.nan, lo=np.nan, hi=np.nan, p=np.nan, null=0.5, inadmissible=True)
        print(f"\n[D4] base rate fracaso(pf_fwd<1) en N1 = {fail_rate*100:.2f}% -> primario INADMISIBLE (sin fracasos). "
              f"Se reporta D4 exploratorio sobre bloque2c (tiene tail/mid con pf_fwd<1).")
    else:
        def auc_fail(group):
            sc = [g["plateau_ratio"] for g in group if np.isfinite(g["plateau_ratio"])]
            lb = [1 if g["pf_fwd"] < 1 else 0 for g in group if np.isfinite(g["plateau_ratio"])]
            return auc_mwu([-s for s in sc], lb)  # alto plateau => menos fracaso
        obs, lo, hi, bd = boot_by_symbol_stat(clean, auc_fail, reps=2000)
        p = 2*min((bd > 0.5).mean(), (bd < 0.5).mean()) if len(bd) else 1.0
        results["D4"] = dict(name="Perfil de fracaso (plateau->fail AUC)", stat="AUC", est=obs, lo=lo, hi=hi, p=float(min(1.0, p)), null=0.5)

    # ---- D3: ε² del clúster sobre pf_fwd (per-símbolo) + permutación ----
    def eps2_sym(group):
        return kruskal_eps2([g["pf_fwd"] for g in group], [g["cluster"] for g in group])
    obs_e,lo_e,hi_e,bd_e = boot_by_symbol_stat(clean, eps2_sym, reps=2000)
    # permutación: barajar cluster within símbolo, recomputar media ε²
    by_sym = {}
    for r in clean: by_sym.setdefault(r["symbol"],[]).append(r)
    def mean_eps2(perm=False):
        vals=[]
        for s,g in by_sym.items():
            pf=[x["pf_fwd"] for x in g]; cl=[x["cluster"] for x in g]
            if perm: cl=list(RNG.permutation(cl))
            e=kruskal_eps2(pf,cl)
            if not np.isnan(e): vals.append(e)
        return np.mean(vals) if vals else np.nan
    obs_eps = mean_eps2(False)
    null = np.array([mean_eps2(True) for _ in range(1000)])
    p_d3 = (null >= obs_eps).mean()
    results["D3"] = dict(name="Contexto/régimen (ε² clúster)", stat="eps2", est=obs_eps, lo=lo_e, hi=hi_e, p=float(p_d3), null="perm")

    # ---- PANEL LIMPIO (auditoría de contaminación, post-verificación primary-source) ----
    # Hechos verificados en regime_walk_forward.py:
    #   pf_combined = blend(pf_tr,pf_fwd)        -> CONTAMINADO (D1)
    #   pf_robustness = min(pf_fwd/pf_tr,1.5)    -> CONTAMINADO (D2)  [L2055]
    #   ci_width = pf_fwd_ci_high - pf_fwd_ci_low-> CONTAMINADO (D5)  [L1239]
    #   specialist_score usa pf_robustness        -> CONTAMINADO (D6) pero ρ≈0
    #   cross_cluster_survival/adjacent_worst_pf = f(pf_fwd adyacente) -> CONTAMINADO
    # Dimensiones LIMPIAS (NO función directa del pf_fwd de este config):
    #   pf_tr, trades_tr, pnl_tr (ventana train), plateau_ratio (densidad param-vecinos), maxdd_worst (drawdown)
    print("\n" + "="*90)
    print("PANEL LIMPIO — dimensiones NO contaminadas por pf_fwd (within-cell N1, bootstrap por-símbolo)")
    print("="*90)
    clean_dims = [("pf_tr","PF train puro (D1 limpio)"),
                  ("plateau_ratio","Robustez param-espacio (D2/D5 limpio)"),
                  ("trades_tr","Nº trades train"),
                  ("pnl_tr","PnL train"),
                  ("maxdd_worst","Drawdown peor (semi-limpio)")]
    clean_panel = {}
    for col, lab in clean_dims:
        # filtra filas con valor finito en col
        sub = [r for r in clean if np.isfinite(r.get(col, np.nan))]
        m,_,sr = within_cell_rho(sub, col, "pf_fwd")
        lo,hi,p = boot_by_symbol(sr)
        clean_panel[col] = dict(label=lab, est=m, lo=lo, hi=hi, p=p, n=len(sub))
        excl0 = (lo>0 and hi>0) or (lo<0 and hi<0)
        verd = "señal" if (excl0 and abs(m)>=0.10) else ("sugestivo" if abs(m)>=0.10 else "MUERTA")
        print(f"  {col:<16}{lab[:40]:<42} ρ={m:+.3f}  CI[{lo:+.3f},{hi:+.3f}]  p={p:.4f}  N={len(sub):<6} -> {verd}")

    # ---- D1: bloque2c N=60 (pooled, instrumento independiente) ----
    b2 = os.path.join(ROOT, "analysis_scripts", "bloque2c_w3_validation_20260423", "bloque2c_smoke_c_results.csv")
    with open(b2) as fh: bl = list(csv.DictReader(fh))
    def fcol(rows_,c): return np.array([float(r[c]) for r in rows_ if r[c] not in ("","inf") and np.isfinite(float(r[c]))])
    # filas con todas las columnas finitas
    good=[r for r in bl if all(r[c] not in ("","inf") and np.isfinite(float(r[c])) for c in ["pf_combined_bin","pf_fwd_bin","pf_fwd_JSON","pf_tr_bin"])]
    pcomb=np.array([float(r["pf_combined_bin"]) for r in good]); pfwd=np.array([float(r["pf_fwd_bin"]) for r in good])
    pjson=np.array([float(r["pf_fwd_JSON"]) for r in good]); ptr=np.array([float(r["pf_tr_bin"]) for r in good])
    rho_d1 = spearman(pcomb, pfwd)
    rho_repro = spearman(pjson, pfwd)  # reproduce ~0.047
    rho_tr = spearman(ptr, pfwd)
    # bootstrap por filas (N pequeño, único instrumento)
    def boot_rows(x,y,reps=N_BOOT):
        n=len(x); arr=np.empty(reps)
        for b in range(reps):
            idx=RNG.choice(n,n,replace=True); arr[b]=spearman(x[idx],y[idx])
        lo,hi=np.nanpercentile(arr,[2.5,97.5]); p=2*min(np.nanmean(arr>0),np.nanmean(arr<0))
        return float(lo),float(hi),float(min(1.0,p))
    lo,hi,p = boot_rows(pcomb,pfwd)
    results["D1"] = dict(name="PF histórico (pf_combined, bloque2c N=%d)"%len(good), stat="rho", est=rho_d1, lo=lo, hi=hi, p=p)
    print(f"\nNivel 2 (bloque2c N={len(good)}): reproducir ρ(pf_fwd_JSON,pf_fwd_bin)={rho_repro:+.4f} (ancla esperada ~+0.047)")
    print(f"  ρ(pf_tr_bin, pf_fwd_bin)={rho_tr:+.4f} | ρ(pf_combined_bin, pf_fwd_bin)={rho_d1:+.4f}")

    # ---- D4 exploratorio sobre bloque2c (tiene fracasos pf_fwd_bin<1) ----
    fail_b2 = (pfwd < 1).astype(int)
    print(f"\n[D4 exploratorio bloque2c] base rate fracaso(pf_fwd_bin<1) = {fail_b2.mean()*100:.1f}% (N={len(good)})")
    if fail_b2.sum() >= 3 and (fail_b2 == 0).sum() >= 3:
        auc_tr = auc_mwu(-ptr, fail_b2)        # bajo pf_tr => fracaso forward?
        auc_trd = auc_mwu([float(r["trades_tr"]) for r in good], fail_b2)  # +trades => fracaso?
        results["D4_explor_bloque2c"] = dict(auc_pf_tr_to_fail=auc_tr, auc_trades_tr_to_fail=auc_trd,
                                             n=len(good), n_fail=int(fail_b2.sum()))
        print(f"  AUC(pf_tr_bin -> fracaso)={auc_tr:.3f} | AUC(trades_tr -> fracaso)={auc_trd:.3f} (0.5=sin info)")

    # ---- multiplicidad sobre tests EVALUABLES (D4 N1 inadmisible por 0 fracasos) ----
    dims = ["D1","D2","D3","D4","D5","D6"]
    eval_dims = [d for d in dims if not results[d].get("inadmissible")]
    pv = [results[d]["p"] for d in eval_dims]
    passed_eval, bonf = fdr_bh(pv, q=0.10)
    passed_map = {d: bool(passed_eval[i]) for i, d in enumerate(eval_dims)}
    print(f"\nMultiplicidad sobre m={len(eval_dims)} EVALUABLES (D4-N1 inadmisible excluido; Bonferroni α={bonf:.4f})")

    # ---- veredicto por dimensión ----
    print("\n"+"="*90)
    print("FASE 2 — TABLA DE CAPACIDAD DE INFORMACIÓN (m=6, FDR-BH q=0.10, Bonferroni α=%.4f)"%bonf)
    print("="*90)
    print(f"{'Dim':<4}{'Dimensión':<46}{'stat':<6}{'est':>9}{'CI95':>20}{'p':>9}{'FDR':>5}{'veredicto':>14}")
    for d in dims:
        r=results[d]; null=r.get("null",0.0)
        if r.get("inadmissible"):
            r["veredicto"]="NO EVALUABLE"
            print(f"{d:<4}{r['name'][:45]:<46}{r['stat']:<6}{'  --':>9}{'  --':>20}{'  --':>9}{'-':>5}{'NO EVALUABLE':>14}")
            continue
        fdr_ok = passed_map.get(d, False)
        excl0 = ((r["lo"]>null and r["hi"]>null) or (r["lo"]<null and r["hi"]<null)) if isinstance(null,(int,float)) else (r["lo"]>0)
        sig = fdr_ok and excl0
        if r["stat"]=="rho": material = abs(r["est"])>=0.10
        elif r["stat"]=="AUC": material = abs(r["est"]-0.5)>=0.05
        else: material = r["est"]>=0.02
        if sig and material: verd="SEÑAL"
        elif sig or (material and r["p"]<0.10): verd="SUGESTIVO"
        elif material: verd="sugestivo-débil"
        else: verd="MUERTA"
        r["veredicto"]=verd; r["fdr"]=fdr_ok; r["material"]=material
        ci=f"[{r['lo']:+.3f},{r['hi']:+.3f}]"
        print(f"{d:<4}{r['name'][:45]:<46}{r['stat']:<6}{r['est']:>9.3f}{ci:>20}{r['p']:>9.4f}{('Y' if fdr_ok else '-'):>5}{verd:>14}")

    n_signal=sum(1 for d in dims if results[d]["veredicto"]=="SEÑAL")
    n_sug=sum(1 for d in dims if "SUGESTIVO" in results[d]["veredicto"] or results[d]["veredicto"]=="sugestivo-débil")
    print("\n"+"-"*90)
    print(f"GLOBAL: {n_signal} SEÑAL, {n_sug} sugestivo, {6-n_signal-n_sug} MUERTA")
    print("Interpretación N1 (congelada): SEÑAL/sugestivo en caso fácil = CANDIDATA (no confirmada, requiere N3-GPU).")
    print("                               MUERTA en caso fácil-sesgado-a-favor = muerta sin ambigüedad.")

    # guardar resultados
    out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "estudio_capacidad_fase1_results.json")
    json.dump({"n1_configs":len(rows),"n_util":len(clean),"bonferroni":bonf,
               "repro_rho_0047":rho_repro,"rho_pf_tr_fwd_b2":rho_tr,"rho_pf_comb_fwd_b2":rho_d1,
               "n1_fail_rate":fail_rate,"clean_panel":clean_panel,
               "d4_explor_bloque2c":results.get("D4_explor_bloque2c"),"results":results}, open(out,"w"), indent=2, default=float)
    print(f"\nGuardado: {out}")

if __name__ == "__main__":
    main()
