#!/usr/bin/env python3
"""C2 — Nivel 3 patas pre-registradas OMITIDAS, desde sealed JSONs (sin GPU).
(a) Placebo wrong-match: especificidad del emparejamiento régimen-specialist (permutación de 'home').
(b) Cartera régimen-condicional (solo MATCH) vs agnóstica (todos los trades).
Métrica NETA (fee 0.10pp RT), como el pre-registro congelado."""
import json, glob
from pathlib import Path
import numpy as np, pandas as pd

HERE = Path(__file__).resolve().parent
SRC = HERE.parent / "audit_forense_gap_20260612"
FEE = 0.10   # pct points RT
SEED = 20260702

def pf(trades):
    if not trades: return None, 0
    net = np.array([t["pnl_pct"] - FEE for t in trades])
    pos = net[net > 0].sum(); neg = -net[net < 0].sum()
    return (float(pos/neg) if neg > 0 else np.inf), len(net)

files = sorted(glob.glob(str(SRC / "nivel3_resmoke_trades_*_2025-05-01_data_cache.json")))
cells = {}
all_match, all_mismatch, all_agn = [], [], []
for f in files:
    sym = Path(f).stem.split("_")[3]
    d = json.load(open(f))
    agn = d.get("agn", {})
    match, mism = [], []
    for c, trades in agn.items():
        for t in trades:
            all_agn.append(t)
            if t.get("entry_regime") == t.get("home"): match.append(t); all_match.append(t)
            else: mism.append(t); all_mismatch.append(t)
    if match or mism:
        pm, nm = pf(match); pmm, nmm = pf(mism)
        cells[sym] = {"pf_match": pm, "n_match": nm, "pf_mismatch": pmm, "n_mismatch": nmm,
                      "delta": (pm - pmm) if (pm is not None and pmm is not None and np.isfinite(pm) and np.isfinite(pmm)) else None}

# ---- (b) cartera condicional (MATCH) vs agnostica (todos) ----
pf_cond, n_cond = pf(all_match)
pf_agn, n_agn = pf(all_agn)

# ---- (a) placebo wrong-match: permutar 'home' por specialist y recomputar delta pooled ----
# construir por (sym, home-original) los trades con su entry_regime; permutar la etiqueta home entre los 3 clusters
def pooled_delta(match_list, mismatch_list):
    pm, _ = pf(match_list); pmm, _ = pf(mismatch_list)
    if pm is None or pmm is None or not np.isfinite(pm) or not np.isfinite(pmm): return None
    return pm - pmm
obs_delta = pooled_delta(all_match, all_mismatch)

# permutacion: para cada sym, reasignar aleatoriamente que cluster es 'home' (0/1/2) y re-clasificar
rng = np.random.default_rng(SEED)
raw = {}  # sym -> list of trades con entry_regime y home_original
for f in files:
    sym = Path(f).stem.split("_")[3]
    d = json.load(open(f)); agn = d.get("agn", {})
    tr = []
    for c, trades in agn.items():
        for t in trades:
            tr.append((int(t["home"]), int(t["entry_regime"]), t["pnl_pct"]))
    if tr: raw[sym] = tr
null = []
for _ in range(2000):
    m, mm = [], []
    for sym, tr in raw.items():
        homes = list({h for h, _, _ in tr})
        perm = {h: rng.choice(homes) for h in homes} if len(homes) > 1 else {homes[0]: homes[0]}
        for h, er, pnl in tr:
            fake_home = perm[h]
            (m if er == fake_home else mm).append({"pnl_pct": pnl})
    dnull = pooled_delta(m, mm)
    if dnull is not None: null.append(dnull)
null = np.array(null)
p_perm = float(np.mean(np.abs(null) >= abs(obs_delta))) if len(null) and obs_delta is not None else None

res = {
    "metrica": "PF neto (fee 0.10pp RT)",
    "leg_a_placebo_wrong_match": {
        "delta_pooled_obs": round(obs_delta, 4) if obs_delta is not None else None,
        "null_perm_media": round(float(null.mean()), 4) if len(null) else None,
        "null_perm_p95_abs": round(float(np.percentile(np.abs(null), 95)), 4) if len(null) else None,
        "p_permutacion": p_perm,
        "interpretacion": "si p_perm alto -> el emparejamiento real NO es mas especifico que el aleatorio (sin especificidad = confirma NO CONFIRMADO)"},
    "leg_b_condicional_vs_agnostica": {
        "pf_condicional_MATCH": round(pf_cond, 4) if pf_cond and np.isfinite(pf_cond) else pf_cond, "n_cond": n_cond,
        "pf_agnostica_TODOS": round(pf_agn, 4) if pf_agn and np.isfinite(pf_agn) else pf_agn, "n_agn": n_agn,
        "gate_regimen_ayuda": bool(pf_cond and pf_agn and pf_cond > pf_agn and pf_cond > 1.0),
        "interpretacion": "condicional>agnostica Y >1.0 -> el gate de regimen anade valor; si no -> no ayuda"},
    "por_celda": cells,
}
(HERE / "results_C2.json").write_text(json.dumps(res, indent=2, default=str))
print(json.dumps(res, indent=2, default=str))
