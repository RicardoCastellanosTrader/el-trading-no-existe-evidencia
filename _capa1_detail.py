"""CAPA 1 detalle — clasificar divergencias verify_test: drift §12.30 vs bug. READ-ONLY."""
import io, re, json
from contextlib import redirect_stdout
from live.brain_engine import _run_verify_test

SYMS = ["BTC/USDT", "ETH/USDT", "BNB/USDT", "SEI/USDT", "POL/USDT", "ONDO/USDT",
        "TRX/USDT", "XRP/USDT", "RENDER/USDT"]
# MAs iterativas path-dependent (§12.30): drift acumulativo aceptado, ranking-invariante
ITER_MA = {"VIDYA", "KAMA", "ALMA", "T3", "FRAMA", "McGinley", "JMA", "DEMA", "TEMA", "ZLEMA"}

def parse(out):
    preset = None
    m = re.search(r"Fast:\s*([^|]+)\|\s*Slow:\s*([^|]+)\|\s*Trend:\s*([^|]+)\|", out)
    if m:
        preset = {"fast": m.group(1).strip(), "slow": m.group(2).strip(), "trend": m.group(3).strip()}
    metrics = {}
    for name in ["Trades", "Wins", "PnL neto %", "Gross profit %", "Gross loss %"]:
        mm = re.search(re.escape(name) + r"\s+(-?[\d.]+)\s+(-?[\d.]+)\s+(-?[\d.]+)", out)
        if mm:
            metrics[name] = {"brain": float(mm.group(1)), "kernel": float(mm.group(2)), "diff": float(mm.group(3))}
    return preset, metrics

rows = []
for sym in SYMS:
    buf = io.StringIO()
    try:
        with redirect_stdout(buf):
            rc = _run_verify_test(sym, n_bars=1000)
    except Exception as e:
        rows.append({"sym": sym, "rc": None, "err": repr(e)})
        continue
    preset, metrics = parse(buf.getvalue())
    ma_types = []
    if preset:
        for v in preset.values():
            mt = re.match(r"([A-Za-z0-9]+)", v)
            if mt:
                ma_types.append(mt.group(1))
    has_iter = any(t in ITER_MA for t in ma_types)
    trades_match = metrics.get("Trades", {}).get("diff", 0) == 0
    pnl_diff = abs(metrics.get("PnL neto %", {}).get("diff", 0))
    rows.append({"sym": sym, "rc": int(rc), "preset": preset, "ma_types": ma_types,
                 "has_iterative_MA": has_iter, "trades_match": trades_match,
                 "pnl_diff_pp": pnl_diff, "metrics": metrics})

print(f"{'sym':12} {'rc':>3} {'iterMA':>6} {'trdMatch':>8} {'PnLdiff_pp':>10}  preset (fast/slow/trend)")
for r in rows:
    if r.get("err"):
        print(f"{r['sym']:12} ERR {r['err'][:60]}"); continue
    p = r["preset"] or {}
    print(f"{r['sym']:12} {r['rc']:>3} {str(r['has_iterative_MA']):>6} {str(r['trades_match']):>8} "
          f"{r['pnl_diff_pp']:>10.4f}  {p.get('fast','?')}/{p.get('slow','?')}/{p.get('trend','?')}")

print("\n=== Clasificación divergencias (rc=1) ===")
for r in rows:
    if r.get("err") or r["rc"] == 0:
        continue
    iters = [t for t in r["ma_types"] if t in ITER_MA]
    if r["trades_match"] and r["pnl_diff_pp"] < 1.0 and iters:
        verd = f"DRIFT §12.30 ACEPTADO (MAs iterativas {iters}, estructura idéntica, PnL drift {r['pnl_diff_pp']:.4f}pp)"
    elif iters:
        verd = f"DRIFT §12.30 PROBABLE (MAs iterativas {iters}, pero trades_match={r['trades_match']} PnL {r['pnl_diff_pp']:.4f}pp — verificar bar-level <7-9%)"
    else:
        verd = f"REVISAR — sin MA iterativa pero diverge (MAs={r['ma_types']}) — candidato BUG"
    print(f"  {r['sym']}: {verd}")

json.dump(rows, open("audit_capa1_detail_results.json", "w"), indent=2, default=str)
print("\nSaved: audit_capa1_detail_results.json")
