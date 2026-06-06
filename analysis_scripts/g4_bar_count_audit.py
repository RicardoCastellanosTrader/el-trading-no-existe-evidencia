# G4 selection audit — bar counts + gaps for the 30 remaining symbols (read-only).
import os
import pandas as pd

REMAINING = ("XLM,SUI,LTC,AVAX,HBAR,SHIB,DOT,UNI,AAVE,NEAR,ICP,ETC,ENA,WLD,APT,"
             "ATOM,ALGO,ARB,FIL,QNT,VET,OP,IMX,INJ,FET,STX,SAND,MANA,GRT,THETA").split(",")

rows = []
for s in REMAINING:
    p = f"data_cache/{s}USDT_1h.parquet"
    if not os.path.exists(p):
        rows.append({"sym": s, "bars": -1})
        continue
    df = pd.read_parquet(p, columns=["timestamp_ms"])
    n = len(df)
    ts = pd.to_datetime(df["timestamp_ms"], unit="ms").sort_values().reset_index(drop=True)
    diffs = ts.diff().dropna()
    gaps = int((diffs > pd.Timedelta(hours=1)).sum())
    rows.append({
        "sym": s,
        "bars": n,
        "first": str(ts.iloc[0]),
        "last": str(ts.iloc[-1]),
        "gaps_gt_1h": gaps,
        "max_gap": str(diffs.max()),
    })

out = pd.DataFrame(rows).sort_values("bars", ascending=False)
print(out.to_string(index=False))
