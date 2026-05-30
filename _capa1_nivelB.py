"""CAPA 1 PARTE A — Nivel B CONCLUSIVO (§12.30 gate) sobre 9 sym. READ-ONLY.
N=8000. Criterio Nivel B (implementado en _run_verify_test): PnL 15% rel (floor 0.1pp)
+ trades ±max(1,5%N), match>=95%. PASS => drift dentro de baseline §12.30 (benigno).
FAIL => bug candidato. 4 divergentes (ETH/ONDO/TRX/RENDER) + 5 control (BTC/BNB/SEI/POL/XRP).
"""
import io, re, json
from contextlib import redirect_stdout
from live.brain_engine import _run_verify_test

DIVERGENT = ["ETH/USDT", "ONDO/USDT", "TRX/USDT", "RENDER/USDT"]
CONTROL = ["BTC/USDT", "BNB/USDT", "SEI/USDT", "POL/USDT", "XRP/USDT"]
SYMS = DIVERGENT + CONTROL
N = 8000

def parse(out):
    d = {}
    for key, pat in [
        ("brain_trades", r"Trades\s+(\d+)\s+\d+"),
        ("kernel_trades", r"Trades\s+\d+\s+(\d+)"),
        ("pnl_rel_pct", r"PnL diff relativo\s+([\d.]+)pct"),
        ("match_pct", r"Match count trades\s+([\d.]+)pct"),
    ]:
        m = re.search(pat, out)
        d[key] = float(m.group(1)) if m else None
    return d

rows = []
for sym in SYMS:
    buf = io.StringIO()
    try:
        with redirect_stdout(buf):
            rc = _run_verify_test(sym, n_bars=N)
        out = buf.getvalue()
        p = parse(out)
        rows.append({"sym": sym, "group": "DIVERGENT" if sym in DIVERGENT else "CONTROL",
                     "rc": int(rc), "nivelB_pass": rc == 0, **p})
        print(f"{sym:12} [{('DIV' if sym in DIVERGENT else 'CTL')}] rc={rc} "
              f"{'PASS' if rc==0 else 'FAIL'} | trades B/K={p['brain_trades']}/{p['kernel_trades']} "
              f"PnL_rel={p['pnl_rel_pct']}% match={p['match_pct']}%", flush=True)
    except Exception as e:
        rows.append({"sym": sym, "rc": None, "err": repr(e)})
        print(f"{sym:12} ERROR {e!r}", flush=True)

json.dump(rows, open("audit_capa1_nivelB_results.json", "w"), indent=2)
n_div_pass = sum(1 for r in rows if r.get("group") == "DIVERGENT" and r.get("nivelB_pass"))
n_ctl_pass = sum(1 for r in rows if r.get("group") == "CONTROL" and r.get("nivelB_pass"))
print(f"\n=> NIVEL B: divergentes {n_div_pass}/4 PASS (drift benigno §12.30), control {n_ctl_pass}/5 PASS")
print("Saved: audit_capa1_nivelB_results.json")
