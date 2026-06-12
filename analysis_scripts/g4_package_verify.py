# B.2 — verificacion univoca origen+contenido del package best-source v2.8.0 (read-only).
import json
import hashlib


def md5(p):
    return hashlib.md5(open(p, "rb").read()).hexdigest()[:12]


rep = json.load(open("deployment_package_grupo_4/deployment_report_grupo_4.json", encoding="utf-8"))
best = rep["best_source_per_sym"]
print("best_source_per_sym (report autoritativo):")
for k, v in best.items():
    print(f"  {k}: {v}")
print()

SRC = {
    "PER_SYM_BASELINE": lambda s: f"regime_wf/{s}_specialist_configs.json",
    "ETH_SOURCE": lambda s: f"ccv_phase4_eth_results/{s}_eth_classified/cell_baseline/{s}/{s}_specialist_configs.json",
    "BTC_SOURCE": lambda s: f"ccv_phase4_btc_results/{s}_btc_classified/cell_baseline/{s}/{s}_specialist_configs.json",
}

print("VERIFICACION origen+contenido (symbol interno coincide + source_path del report coincide):")
ok = True
pkg = {}
for sym in ["LTCUSDT", "XLMUSDT", "ETCUSDT", "VETUSDT", "FETUSDT"]:
    src = best[sym]
    p = SRC[src](sym)
    d = json.load(open(p, encoding="utf-8"))
    internal = d.get("symbol", "?")
    declared = rep["metrics_table"][sym][src]["source_path"].replace("\\", "/")
    nclu = d.get("n_clusters")
    full = sum(1 for v in d.get("clusters", {}).values() if v.get("top_configs"))
    match_decl = (
        (src == "PER_SYM_BASELINE" and "regime_wf" in declared)
        or (src == "ETH_SOURCE" and "eth" in declared)
        or (src == "BTC_SOURCE" and "btc" in declared)
    )
    sym_ok = internal.replace("/USDT", "USDT") == sym
    flag = "OK" if (sym_ok and nclu == 3 and full == 3 and match_decl) else "REVISAR"
    if flag != "OK":
        ok = False
    pkg[sym] = (src, p, md5(p))
    print(f"  {sym:<8} src={src:<16} internal={internal:<10} nclu={nclu} full={full}/3 "
          f"decl_match={match_decl} md5={md5(p)} -> {flag}")
    print(f"           path={p}")

print()
# GMM models presentes
print("GMM models ({SYM}_regime.joblib) presentes:")
import os
for sym in ["LTCUSDT", "XLMUSDT", "ETCUSDT", "VETUSDT", "FETUSDT"]:
    base = sym.replace("USDT", "")
    g = f"regime_models/{base}_regime.joblib"
    ex = os.path.exists(g)
    if not ex:
        ok = False
    print(f"  {g}: {'OK' if ex else 'FALTA'} ({md5(g) if ex else '-'})")

print()
print("VEREDICTO B.2:", "TODOS UNIVOCOS — package armable" if ok
      else "T3.3 — origen NO verificable univocamente")
