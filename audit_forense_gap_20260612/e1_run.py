# -*- coding: utf-8 -*-
"""
E1 harness test-only: extiende el whitelist de símbolos EN MEMORIA con los placebo
y delega a master.main() — la LÓGICA del pipeline (master/lab_lite/walk-forward/kernel)
corre INTACTA; solo se controla la entrada (símbolos placebo ya en data_cache).
Cada invocación es un proceso fresco (patrón H_B 2-phase). Args = los de master.py.
"""
import sys
sys.path.insert(0, r"c:\Users\rixip\combolab")
import pandas as pd
import master
import lab_lite_zonas_v5e as _lab

PLB = [f"PLBGB{i}/USDT" for i in (1, 2, 3)] + [f"PLBSH{i}/USDT" for i in (1, 2, 3)]
master.CONFIG['symbols'] = list(master.CONFIG['symbols']) + PLB

# --- harness input-control: lab_lite re-descarga su ventana de Binance; para
# símbolos placebo la servimos desde data_cache (NO toca lógica del pipeline) ---
_orig_fetch = _lab.fetch_all_candles
def _patched_fetch(symbol, timeframe, total_candles, max_retries=3):
    key = symbol.replace("/", "")
    if key.startswith("PLB"):
        df = pd.read_parquet(fr"c:\Users\rixip\combolab\data_cache\{key}_1h.parquet")
        rows = df[["timestamp_ms", "open", "high", "low", "close", "volume"]].values.tolist()
        return rows[-(total_candles):]
    return _orig_fetch(symbol, timeframe, total_candles, max_retries)
_lab.fetch_all_candles = _patched_fetch

master.main()
