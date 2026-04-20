"""
stress_test.py — Test de estres con datos de crashes historicos (LUNA, FTT).

Descarga datos de Binance Vision, entrena GMM temporal, simula ciclo horario
barra a barra durante el crash, y reporta:
  - Cuando detecta el cambio de regimen
  - Si el SL protege la posicion
  - Drawdown maximo sin proteccion

CLI:
    python -m live.stress_test                # Ambos tests
    python -m live.stress_test --symbol LUNA   # Solo LUNA
    python -m live.stress_test --symbol FTT    # Solo FTT
"""

import argparse
import io
import os
import sys
import time
import zipfile
from pathlib import Path

import joblib
import numpy as np
import pandas as pd

_project_root = str(Path(__file__).parent.parent)
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

from regime_features import compute_regime_features, LOOKBACK_LONG, N_FEATURES
from train_regime_model import train_symbol_model

CACHE_DIR = os.path.join(_project_root, "data_cache", "stress_test")

# ---------------------------------------------------------------------------
# Crash definitions
# ---------------------------------------------------------------------------
CRASHES = {
    "LUNA": {
        "pair": "LUNAUSDT",
        "months": ["2022-01", "2022-02", "2022-03", "2022-04", "2022-05"],
        "crash_start": "2022-05-07",
        "crash_end": "2022-05-13",
        "description": "Terra/LUNA collapse — de $80 a $0.00 en 6 dias",
    },
    "FTT": {
        "pair": "FTTUSDT",
        "months": ["2022-08", "2022-09", "2022-10", "2022-11"],
        "crash_start": "2022-11-07",
        "crash_end": "2022-11-11",
        "description": "FTX collapse — de $25 a $1 en 5 dias",
    },
}

# Trading constants (identical to brain_engine / lab_historico)
SL_PERCENT = 3.0
SL_EMERGENCY_PERCENT = 5.0


# ---------------------------------------------------------------------------
# 1. Download from Binance Vision
# ---------------------------------------------------------------------------
def _download_binance_klines(pair: str, months: list[str]) -> pd.DataFrame:
    """Download monthly kline ZIPs from data.binance.vision and concatenate."""
    import urllib.request

    all_dfs = []
    for month in months:
        csv_path = os.path.join(CACHE_DIR, f"{pair}-1h-{month}.csv")

        if os.path.exists(csv_path):
            print(f"    Cache hit: {pair}-1h-{month}")
            df_month = pd.read_csv(csv_path)
            # Ensure open_time is numeric (cached CSVs may have mixed types)
            df_month["open_time"] = pd.to_numeric(df_month["open_time"], errors="coerce")
            df_month = df_month.dropna(subset=["open_time"])
            all_dfs.append(df_month)
            continue

        url = (
            f"https://data.binance.vision/data/futures/um/monthly/klines/"
            f"{pair}/1h/{pair}-1h-{month}.zip"
        )
        print(f"    Descargando {url} ...")
        try:
            resp = urllib.request.urlopen(url, timeout=30)
            zip_bytes = resp.read()
        except Exception as e:
            print(f"    ERROR descargando {month}: {e}")
            continue

        with zipfile.ZipFile(io.BytesIO(zip_bytes)) as zf:
            csv_name = zf.namelist()[0]
            with zf.open(csv_name) as f:
                df_month = pd.read_csv(
                    f, header=None,
                    names=[
                        "open_time", "open", "high", "low", "close", "volume",
                        "close_time", "quote_volume", "trades",
                        "taker_buy_volume", "taker_buy_quote_volume", "ignore",
                    ],
                )

        # Save to cache
        df_month.to_csv(csv_path, index=False)
        all_dfs.append(df_month)
        print(f"    OK: {len(df_month)} barras")

    if not all_dfs:
        return pd.DataFrame()

    df = pd.concat(all_dfs, ignore_index=True)
    df["open_time"] = pd.to_numeric(df["open_time"], errors="coerce")
    df = df.dropna(subset=["open_time"])
    df = df.sort_values("open_time").drop_duplicates("open_time").reset_index(drop=True)

    # Convert to standard OHLCV format
    result = pd.DataFrame({
        "timestamp": pd.to_datetime(df["open_time"].astype(np.int64), unit="ms", utc=True),
        "open": df["open"].astype(float),
        "high": df["high"].astype(float),
        "low": df["low"].astype(float),
        "close": df["close"].astype(float),
        "volume": df["volume"].astype(float),
    })

    return result


# ---------------------------------------------------------------------------
# 2. Train temporary GMM
# ---------------------------------------------------------------------------
def _train_temp_gmm(symbol_label: str, df: pd.DataFrame) -> dict | None:
    """Train a temporary GMM on the crash data. Returns model_data or None."""
    print(f"\n  [2] Entrenando GMM temporal para {symbol_label}...")
    print(f"      {len(df)} barras: {df['timestamp'].iloc[0]} -> {df['timestamp'].iloc[-1]}")

    model_data = train_symbol_model(f"{symbol_label}/USDT", df)
    if model_data is None:
        print(f"      FALLO: insuficientes barras validas para GMM")
        return None

    print(f"      Clusters: {model_data['n_clusters']}")
    for i, name in enumerate(model_data['cluster_names']):
        c = model_data['centroids'][i]
        print(f"        C{i} ({name}): Hurst={c[0]:.3f} Z_ATR={c[1]:.3f} ER={c[2]:.3f}")

    return model_data


# ---------------------------------------------------------------------------
# 3. Simulate bar-by-bar through crash
# ---------------------------------------------------------------------------
def _simulate_crash(
    symbol_label: str,
    df: pd.DataFrame,
    model_data: dict,
    crash_start: str,
    crash_end: str,
) -> dict:
    """
    Simulate hourly cycle bar-by-bar through the crash period.

    Returns dict with detailed results.
    """
    from sklearn.preprocessing import StandardScaler

    gmm = model_data['gmm']
    scaler = model_data['scaler']
    n_clusters = model_data['n_clusters']
    cluster_names = model_data['cluster_names']
    lookback = model_data['lookback']

    crash_start_ts = pd.Timestamp(crash_start, tz="UTC")
    crash_end_ts = pd.Timestamp(crash_end + " 23:59:59", tz="UTC")

    # Find crash bar indices
    crash_mask = (df['timestamp'] >= crash_start_ts) & (df['timestamp'] <= crash_end_ts)
    crash_indices = df.index[crash_mask].tolist()

    if not crash_indices:
        print(f"      No se encontraron barras en el rango {crash_start} - {crash_end}")
        return {}

    # We need enough history before crash for features (LOOKBACK_LONG)
    first_crash_bar = crash_indices[0]
    history_start = max(0, first_crash_bar - LOOKBACK_LONG - 50)

    print(f"\n  [3] Simulando crash barra a barra...")
    print(f"      Periodo crash: {crash_start} a {crash_end}")
    print(f"      Barras de crash: {len(crash_indices)}")
    print(f"      Historia pre-crash desde bar {history_start}")

    # Pre-crash classification (last bar before crash)
    pre_crash_bar = first_crash_bar - 1
    if pre_crash_bar < LOOKBACK_LONG:
        print(f"      WARN: insuficiente historia pre-crash")
        pre_crash_cluster = -1
        pre_crash_conf = 0.0
    else:
        window = df.iloc[:pre_crash_bar + 1]
        features, valid = compute_regime_features(window, lookback=lookback)
        valid_idx = np.where(valid)[0]
        if len(valid_idx) > 0:
            feat = features[valid_idx[-1]:valid_idx[-1] + 1]
            X = scaler.transform(feat)
            probs = gmm.predict_proba(X)[0]
            pre_crash_cluster = int(np.argmax(probs))
            pre_crash_conf = float(probs[pre_crash_cluster])
        else:
            pre_crash_cluster = -1
            pre_crash_conf = 0.0

    pre_crash_price = float(df['close'].iloc[pre_crash_bar])
    print(f"      Pre-crash: C{pre_crash_cluster} ({cluster_names[pre_crash_cluster] if pre_crash_cluster >= 0 else '?'}) "
          f"conf={pre_crash_conf:.1%}, price=${pre_crash_price:.2f}")

    # Bar-by-bar simulation
    bar_results = []
    prev_cluster = pre_crash_cluster

    # Simulated position state
    position = 0  # 0=flat, 1=long
    entry_price = 0.0
    sl_level = 0.0
    sl_emergency = 0.0
    trade_result = None  # filled when SL hits

    # Simulate being LONG at crash start (worst case)
    position = 1
    entry_price = pre_crash_price
    sl_level = entry_price * (1 - SL_PERCENT / 100)
    sl_emergency = entry_price * (1 - SL_EMERGENCY_PERCENT / 100)

    first_transition_bar = None
    confirmed_bar = None
    confirm_threshold = 0.75

    for bar_idx in crash_indices:
        window = df.iloc[max(0, bar_idx - LOOKBACK_LONG - 50):bar_idx + 1]
        ts = df['timestamp'].iloc[bar_idx]
        close_p = float(df['close'].iloc[bar_idx])
        low_p = float(df['low'].iloc[bar_idx])
        high_p = float(df['high'].iloc[bar_idx])

        # Classify regime
        features, valid = compute_regime_features(window, lookback=lookback)
        valid_idx = np.where(valid)[0]
        if len(valid_idx) > 0:
            feat = features[valid_idx[-1]:valid_idx[-1] + 1]
            X = scaler.transform(feat)
            probs = gmm.predict_proba(X)[0]
            cluster = int(np.argmax(probs))
            confidence = float(probs[cluster])
        else:
            cluster = prev_cluster
            confidence = 0.0

        # Detect transition
        transitioned = cluster != pre_crash_cluster
        if transitioned and first_transition_bar is None:
            first_transition_bar = {
                "bar_idx": bar_idx, "timestamp": ts,
                "cluster": cluster, "confidence": confidence,
            }
        if transitioned and confidence >= confirm_threshold and confirmed_bar is None:
            confirmed_bar = {
                "bar_idx": bar_idx, "timestamp": ts,
                "cluster": cluster, "confidence": confidence,
            }

        # SL check (for simulated long position)
        if position == 1 and trade_result is None:
            if low_p <= sl_emergency:
                trade_result = {
                    "exit_type": "sl_emergency",
                    "exit_bar": bar_idx, "exit_time": ts,
                    "exit_price": sl_emergency,
                    "pnl_pct": (sl_emergency / entry_price - 1) * 100,
                }
            elif close_p < sl_level:
                trade_result = {
                    "exit_type": "sl_fixed",
                    "exit_bar": bar_idx, "exit_time": ts,
                    "exit_price": close_p,
                    "pnl_pct": (close_p / entry_price - 1) * 100,
                }

        bar_results.append({
            "bar_idx": bar_idx,
            "timestamp": ts,
            "close": close_p,
            "low": low_p,
            "cluster": cluster,
            "confidence": confidence,
            "drawdown_pct": (close_p / pre_crash_price - 1) * 100,
        })

        prev_cluster = cluster

    # Max drawdown without SL
    min_close = min(r["close"] for r in bar_results)
    max_dd_no_sl = (min_close / pre_crash_price - 1) * 100

    return {
        "symbol": symbol_label,
        "pre_crash_cluster": pre_crash_cluster,
        "pre_crash_cluster_name": cluster_names[pre_crash_cluster] if pre_crash_cluster >= 0 else "?",
        "pre_crash_confidence": pre_crash_conf,
        "pre_crash_price": pre_crash_price,
        "n_crash_bars": len(crash_indices),
        "first_transition": first_transition_bar,
        "confirmed_transition": confirmed_bar,
        "cluster_names": cluster_names,
        "simulated_long": {
            "entry_price": entry_price,
            "sl_level": sl_level,
            "sl_emergency": sl_emergency,
            "trade_result": trade_result,
        },
        "max_dd_no_sl_pct": max_dd_no_sl,
        "final_price": bar_results[-1]["close"] if bar_results else 0,
        "bar_results": bar_results,
    }


# ---------------------------------------------------------------------------
# 4. Report
# ---------------------------------------------------------------------------
def _print_report(result: dict, crash_info: dict):
    """Print formatted stress test report."""
    sym = result["symbol"]
    print(f"\n  {'=' * 60}")
    print(f"  STRESS TEST: {sym} — {crash_info['description']}")
    print(f"  {'=' * 60}")

    # Pre-crash state
    print(f"\n  Pre-crash:")
    print(f"    Cluster: C{result['pre_crash_cluster']} ({result['pre_crash_cluster_name']}) "
          f"conf={result['pre_crash_confidence']:.0%}")
    print(f"    Price: ${result['pre_crash_price']:.2f}")

    # Regime transition
    ft = result["first_transition"]
    ct = result["confirmed_transition"]
    if ft:
        cname = result["cluster_names"][ft["cluster"]]
        print(f"\n  Deteccion de regimen:")
        print(f"    Primera transicion: {ft['timestamp']} -> C{ft['cluster']} ({cname}) "
              f"conf={ft['confidence']:.0%}")
        if ct:
            cname2 = result["cluster_names"][ct["cluster"]]
            bars_delay = ct["bar_idx"] - ft["bar_idx"]
            print(f"    Confirmado (>=75%):  {ct['timestamp']} -> C{ct['cluster']} ({cname2}) "
                  f"conf={ct['confidence']:.0%} ({bars_delay} barras delay)")
        else:
            print(f"    Confirmacion >=75%: NO alcanzada durante el crash")
    else:
        print(f"\n  Deteccion de regimen: SIN transicion detectada")

    # Simulated position
    sim = result["simulated_long"]
    tr = sim["trade_result"]
    print(f"\n  Posicion LONG simulada:")
    print(f"    Entry: ${sim['entry_price']:.2f}")
    print(f"    SL fijo ({SL_PERCENT}%): ${sim['sl_level']:.2f}")
    print(f"    SL emergencia ({SL_EMERGENCY_PERCENT}%): ${sim['sl_emergency']:.2f}")
    if tr:
        print(f"    EXIT: {tr['exit_type']} @ ${tr['exit_price']:.2f} "
              f"({tr['pnl_pct']:+.2f}%) en {tr['exit_time']}")
    else:
        print(f"    EXIT: SL nunca ejecutado (posicion habria sobrevivido?)")

    # Max drawdown
    print(f"\n  Drawdown maximo sin SL: {result['max_dd_no_sl_pct']:.1f}%")
    print(f"  Precio final: ${result['final_price']:.4f}")

    # Timeline (key bars)
    print(f"\n  Timeline (barras clave):")
    bars = result["bar_results"]
    prev_cl = result["pre_crash_cluster"]
    shown = 0
    for r in bars:
        is_transition = r["cluster"] != prev_cl
        is_big_move = abs(r["drawdown_pct"]) > 5 and shown < 20
        is_first = r == bars[0]
        is_last = r == bars[-1]
        is_sl = tr and r["bar_idx"] == tr["exit_bar"]

        if is_first or is_last or is_transition or is_big_move or is_sl:
            marker = ""
            if is_sl:
                marker = " <<< SL HIT"
            elif is_transition:
                marker = f" <<< C{prev_cl}->C{r['cluster']}"
            print(f"    {r['timestamp']}  ${r['close']:>10.4f}  "
                  f"C{r['cluster']} conf={r['confidence']:.0%}  "
                  f"DD={r['drawdown_pct']:+.1f}%{marker}")
            shown += 1
            prev_cl = r["cluster"]


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def run_stress_test(symbol: str):
    """Run stress test for one symbol."""
    if symbol not in CRASHES:
        print(f"  Simbolo desconocido: {symbol}. Disponibles: {list(CRASHES.keys())}")
        return

    crash = CRASHES[symbol]
    print(f"\n{'=' * 60}")
    print(f"STRESS TEST: {symbol} ({crash['description']})")
    print(f"{'=' * 60}")

    # Ensure cache dir exists
    os.makedirs(CACHE_DIR, exist_ok=True)

    # Step 1: Download data
    print(f"\n  [1] Descargando datos {crash['pair']} de Binance Vision...")
    df = _download_binance_klines(crash["pair"], crash["months"])
    if df.empty:
        print(f"  ERROR: No se pudieron descargar datos para {symbol}")
        return
    print(f"      Total: {len(df)} barras ({df['timestamp'].iloc[0]} -> {df['timestamp'].iloc[-1]})")

    # Step 2: Train temporary GMM
    model_data = _train_temp_gmm(symbol, df)
    if model_data is None:
        return

    # Step 3: Simulate crash
    result = _simulate_crash(
        symbol, df, model_data,
        crash["crash_start"], crash["crash_end"],
    )
    if not result:
        return

    # Step 4: Report
    _print_report(result, crash)


def main():
    parser = argparse.ArgumentParser(description="Stress test con crashes historicos")
    parser.add_argument("--symbol", type=str, default=None,
                        help="LUNA o FTT (default: ambos)")
    args = parser.parse_args()

    t0 = time.time()

    if args.symbol:
        run_stress_test(args.symbol.upper())
    else:
        for sym in CRASHES:
            run_stress_test(sym)

    elapsed = time.time() - t0
    print(f"\nStress test completado en {elapsed:.1f}s")


if __name__ == "__main__":
    main()
