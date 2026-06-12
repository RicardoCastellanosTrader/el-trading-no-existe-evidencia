# -*- coding: utf-8 -*-
"""Fetch BingX 1h OHLCV (closed bars) para la replicación FASE 1.
Nota metodológica: el bot no persiste caché de velas → re-fetch con posibilidad
de revisiones de velas por el exchange (documentado en el reporte)."""
import ccxt, time, sys
import pandas as pd
from pathlib import Path

OUT = Path(r"c:\Users\rixip\combolab\audit_forense_gap_20260612\bingx_data")
OUT.mkdir(exist_ok=True)
SYMS = ["BTC", "ETH", "BNB", "XRP", "TRX", "ONDO", "RENDER", "POL", "SEI", "TAO",
        "SOL", "DOGE", "ADA", "BCH", "LINK", "LTC", "XLM", "ETC", "VET", "FET"]
SINCE = int(pd.Timestamp("2026-03-10 00:00:00", tz="UTC").timestamp() * 1000)

ex = ccxt.bingx({"options": {"defaultType": "swap"}})
ex.load_markets()

for s in SYMS:
    sym = f"{s}/USDT:USDT"
    rows = []
    since = SINCE
    while True:
        batch = ex.fetch_ohlcv(sym, "1h", since=since, limit=1000)
        if not batch:
            break
        rows.extend(batch)
        if len(batch) < 2:
            break
        nxt = batch[-1][0] + 3_600_000
        if nxt <= since:
            break
        since = nxt
        if batch[-1][0] >= int(time.time() * 1000) - 3_600_000:
            break
        time.sleep(0.25)
    df = pd.DataFrame(rows, columns=["timestamp", "open", "high", "low", "close", "volume"])
    df = df.drop_duplicates("timestamp").sort_values("timestamp").reset_index(drop=True)
    # descartar la última fila si es la barra en curso (forming)
    now_h = int(time.time() * 1000) // 3_600_000 * 3_600_000
    df = df[df["timestamp"] < now_h].reset_index(drop=True)
    df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms", utc=True)
    df.to_parquet(OUT / f"{s}USDT_1h_bingx.parquet")
    print(f"{s}: {len(df)} bars  {df['timestamp'].iloc[0]} -> {df['timestamp'].iloc[-1]}", flush=True)
print("DONE")
