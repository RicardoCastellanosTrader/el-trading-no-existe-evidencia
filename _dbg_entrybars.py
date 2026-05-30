"""DIAGNÓSTICO frame de índices brain vs kernel entry_bar (ETH W=500, N pequeño). READ-ONLY."""
import re, os, numpy as np, pandas as pd
from live.brain_engine import (_evaluate_bar, load_models, decode_config_bits,
                               SL_PERCENT, SL_EMERGENCY_PERCENT, TS_PERCENT,
                               COOLDOWN_BARS, COMMISSION_ROUND_TRIP, _project_root,
                               _normalize_ohlcv, _load_preset_tuple)
from lab_historico_numba_v8_3 import precalculate_all_data, run_on_slice

sym = "ETH/USDT"; W = 500; N = 2000
brain = load_models(regime_models_dir=os.path.join(_project_root, "regime_models"),
                    specialist_configs_dir=os.path.join(_project_root, "regime_wf"), symbols=[sym])
cfg_data = brain.specialist_configs[sym]
tc = next(int(k) for k, c in cfg_data["clusters"].items() if c.get("top_configs"))
top = cfg_data["clusters"][str(tc)]["top_configs"][0]
cid, plabel = top["config_id"], top["preset"]
ptuple = brain.preset_tuples.get(plabel) or _load_preset_tuple(sym, plabel)[0]
hm = re.search(r"_H(\d+)$", plabel); hyst = int(hm.group(1))/10.0 if hm else 0.0

sc = sym.replace("/", "").replace("USDT", "")
df = _normalize_ohlcv(pd.read_parquet(os.path.join(_project_root, "data_cache", f"{sc}USDT_1h.parquet")))
df_test = df.tail(N).reset_index(drop=True)

# Brain entries
bits = decode_config_bits(cid)
st = brain.get_state(sym); st.current_cluster = tc
st.cluster_probs = np.ones(cfg_data["n_clusters"])/cfg_data["n_clusters"]; st.cluster_probs[tc] = 0.9
be = []
for i in range(W, N):
    window = df_test.iloc[max(0, i-W+1):i+1].reset_index(drop=True)
    cfg = {"config_id": cid, "preset": plabel, "preset_tuple": ptuple, "config_bits": bits,
           "cluster": tc, "operable": True, "regime_changed": False}
    try:
        sig = _evaluate_bar(brain, sym, window, cfg)
        if sig["action"] in ("LONG", "SHORT"):
            be.append(i)
    except Exception:
        pass

# Kernel entries
data = precalculate_all_data(df_test, preset=ptuple, hyst_mult=hyst, symbol=sym)
print("len(df_test)=", len(df_test), " len(data['close'])=", len(data["close"]))
configs = np.array([cid], dtype=np.uint32)
agg, pt = run_on_slice(configs, data, start_bar=W, end_bar=N, sl_pct=SL_PERCENT,
                       sl_emergency_pct=SL_EMERGENCY_PERCENT, ts_pct=TS_PERCENT,
                       cooldown_bars=COOLDOWN_BARS, commission_pct=COMMISSION_ROUND_TRIP,
                       warmup=100, return_per_trade=True)
print("per_trade keys:", list(pt.keys()))
cnt = int(pt["count"][0]); ke = pt["entry_bar"][0, :cnt].astype(int)
xb = pt["exit_bar"][0, :cnt].astype(int) if "exit_bar" in pt else None
print(f"\nBRAIN: n={len(be)}  range[{min(be) if be else '-'}..{max(be) if be else '-'}]  first15={be[:15]}")
print(f"KERNEL: n={cnt}  range[{ke.min() if cnt else '-'}..{ke.max() if cnt else '-'}]  first15={ke[:15].tolist()}")
if xb is not None and cnt:
    print(f"KERNEL exit_bar first15={xb[:15].tolist()}")
# overlap exacto
inter = len(set(be) & set(ke.tolist()))
print(f"\nIntersección EXACTA brain∩kernel = {inter}")
# probar offsets
for off in range(-3, 4):
    m = len(set(b+off for b in be) & set(ke.tolist()))
    print(f"  offset brain{off:+d}: exact matches = {m}")
