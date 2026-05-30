"""CAPA 1 — Ground truth numérico de fidelidad (READ-ONLY, no modifica nada).

C1.4 — A12 single-source-of-truth: lab_lite.calc_X is lab_historico.calc_X (17 MAs).
C1.1 — §0.8 Nivel A verify_test brain<->kernel parity (N=1000) sobre 9 sym.
       (BTC/ETH/BNB/SEI/POL/ONDO auditoría + TRX/XRP/RENDER desplegados fuera de muestra)
"""
import io, sys, json
from contextlib import redirect_stdout

SYMS = ["BTC/USDT", "ETH/USDT", "BNB/USDT", "SEI/USDT", "POL/USDT", "ONDO/USDT",
        "TRX/USDT", "XRP/USDT", "RENDER/USDT"]

# ---- C1.4 identidad estructural A12 ----
import lab_lite_zonas_v5e as ll
import lab_historico_numba_v8_3 as lh
ma_names = sorted(n for n in dir(ll) if n.startswith("calc_") and callable(getattr(ll, n)) and hasattr(lh, n))
ident = {n: (getattr(ll, n) is getattr(lh, n)) for n in ma_names}
n_ident = sum(ident.values())
print("=" * 80)
print("C1.4 — A12 single-source-of-truth identity (lab_lite.calc_X IS lab_historico.calc_X)")
print("=" * 80)
for n in ma_names:
    print(f"  {n:18} {'IS-IDENTICAL ✓' if ident[n] else 'DISTINCT ✗ (drift surface!)'}")
print(f"  => {n_ident}/{len(ma_names)} MA funcs son single-source-of-truth (cero drift por construcción)")

# ---- C1.1 verify_test Nivel A ----
from live.brain_engine import _run_verify_test
print("\n" + "=" * 80)
print("C1.1 — §0.8 Nivel A verify_test brain<->kernel parity (N=1000)  [rc=0 => diff 0.0000]")
print("=" * 80)
results = {}
for sym in SYMS:
    buf = io.StringIO()
    try:
        with redirect_stdout(buf):
            rc = _run_verify_test(sym, n_bars=1000)
        results[sym] = {"rc": int(rc), "err": None, "out": buf.getvalue()}
    except Exception as e:
        results[sym] = {"rc": None, "err": repr(e), "out": buf.getvalue()}

print(f"\n{'sym':12} {'rc':>4}  verdict")
summary = {}
for sym in SYMS:
    r = results[sym]
    if r["err"]:
        verdict = f"ERROR: {r['err'][:70]}"
    else:
        verdict = "PASS (diff 0.0000)" if r["rc"] == 0 else f"FAIL rc={r['rc']}"
    summary[sym] = verdict
    print(f"{sym:12} {str(r['rc']):>4}  {verdict}")

# Detalle de los que NO pasaron limpio
for sym in SYMS:
    r = results[sym]
    if r["err"] or (r["rc"] not in (0,)):
        print(f"\n--- {sym} (detalle) ---")
        tail = (r["out"] or "")[-1800:]
        print(tail if tail else r["err"])

n_pass = sum(1 for s in SYMS if results[s]["err"] is None and results[s]["rc"] == 0)
print(f"\n=> C1.1 verify_test Nivel A: {n_pass}/{len(SYMS)} sym PASS (diff 0.0000)")
print(f"=> C1.4 identidad A12: {n_ident}/{len(ma_names)} MAs single-source-of-truth")

with open("audit_capa1_fidelity_results.json", "w", encoding="utf-8") as f:
    json.dump({"c1_4_identity": ident, "c1_4_n_identical": n_ident, "c1_4_total": len(ma_names),
               "c1_1_verify": {s: {"rc": results[s]["rc"], "err": results[s]["err"], "verdict": summary[s]} for s in SYMS},
               "c1_1_n_pass": n_pass}, f, indent=2)
print("\nSaved: audit_capa1_fidelity_results.json")
