# -*- coding: utf-8 -*-
"""
E2-full as-of runner (test-only). Corre el pipeline de PRODUCCIÓN strict point-in-time
as-of una fecha, en un SANDBOX aislado (no toca producción), sobre datos truncados ≤ ancla.
La LÓGICA del pipeline (master/lab_lite/walk-forward/kernel) corre INTACTA; el harness
solo (a) trunca la entrada a ≤ ancla, (b) aísla I/O en sandbox, (c) sirve a lab_lite la
ventana truncada. Tras producir artefactos, el leakage gate (ajuste #6) los verifica.

Uso (2-phase H_B, procesos separados):
  python asof_run.py --symbol BTC --anchor 2026-02-01 --phase 1   # train+lite CPU
  python asof_run.py --symbol BTC --anchor 2026-02-01 --phase 2   # regime-wf GPU
"""
import sys, argparse, os
from pathlib import Path
import pandas as pd

ROOT = Path(r"c:\Users\rixip\combolab")
AUDIT = ROOT / "audit_forense_gap_20260612"
sys.path.insert(0, str(ROOT))


def sandbox_dir(symbol, anchor):
    return AUDIT / "asof_sandbox" / f"{symbol}_{anchor}"


def prep_truncated(symbol, anchor, source="binance_deep"):
    """Trunca ≤ ancla → sandbox/data_cache; registra nº barras pre-ancla (ajuste #1).
    source='binance_deep' (E2-full, 5 sym) o 'data_cache' (canónico 45 sym, validado byte-idéntico
    en ventana de selección vs binance_deep — mini-gate de fuente 2026-06-16 PASS)."""
    A = pd.Timestamp(anchor, tz="UTC")
    if source == "data_cache":
        src = ROOT / "data_cache" / f"{symbol}USDT_1h.parquet"
        df = pd.read_parquet(src)
        df["ts"] = pd.to_datetime(df["timestamp_ms"], unit="ms", utc=True)
    else:
        src = AUDIT / "binance_deep" / f"{symbol}USDT_1h_binance.parquet"
        df = pd.read_parquet(src)
        df["ts"] = pd.to_datetime(df["timestamp"], utc=True)
    df = df[df["ts"] < A].copy()
    n = len(df)
    out = df[["ts", "open", "high", "low", "close", "volume"]].copy()
    out["timestamp_ms"] = (out["ts"].astype("int64") // 1_000_000)
    out = out[["timestamp_ms", "open", "high", "low", "close", "volume"]]
    sb = sandbox_dir(symbol, anchor)
    (sb / "data_cache").mkdir(parents=True, exist_ok=True)
    (sb / "regime_models").mkdir(parents=True, exist_ok=True)
    (sb / "output" / "production").mkdir(parents=True, exist_ok=True)
    (sb / "regime_wf").mkdir(parents=True, exist_ok=True)
    out.to_parquet(sb / "data_cache" / f"{symbol}USDT_1h.parquet")
    import json
    meta = {"symbol": symbol, "anchor": anchor, "pre_anchor_bars": n,
            "first": str(out["timestamp_ms"].iloc[0]), "last_ts": str(out["timestamp_ms"].iloc[-1])}
    json.dump(meta, open(sb / "asof_meta.json", "w"), indent=1)
    return n, sb


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--symbol", required=True)
    ap.add_argument("--anchor", required=True)  # YYYY-MM-DD
    ap.add_argument("--phase", type=int, choices=[1, 2], required=True)
    ap.add_argument("--chunk-size", type=int, default=1_000_000)
    ap.add_argument("--source", default="binance_deep", choices=["binance_deep", "data_cache"])
    args = ap.parse_args()
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except AttributeError:
        pass

    n, sb = prep_truncated(args.symbol, args.anchor, source=args.source)
    print(f"[asof {args.symbol}@{args.anchor}] prehistoria={n} barras -> sandbox {sb}", flush=True)

    import master
    import lab_lite_zonas_v5e as _lab
    # aislar I/O en sandbox (no toca producción)
    master.CONFIG["data_cache_dir"] = str(sb / "data_cache")
    master.CONFIG["regime_models_dir"] = str(sb / "regime_models")
    master.CONFIG["output_dir"] = str(sb / "output" / "production")
    master.CONFIG["regime_wf_dir"] = str(sb / "regime_wf")
    sym_fmt = f"{args.symbol}/USDT"
    if sym_fmt not in master.CONFIG["symbols"]:
        master.CONFIG["symbols"] = list(master.CONFIG["symbols"]) + [sym_fmt]

    # lab_lite re-descarga su ventana; servimos la truncada (≤ ancla)
    A = pd.Timestamp(args.anchor, tz="UTC")
    _orig = _lab.fetch_all_candles
    def _patched(symbol, timeframe, total_candles, max_retries=3):
        key = symbol.replace("/", "")
        if key == f"{args.symbol}USDT":
            df = pd.read_parquet(sb / "data_cache" / f"{args.symbol}USDT_1h.parquet")
            rows = df[["timestamp_ms", "open", "high", "low", "close", "volume"]].values.tolist()
            served = rows[-(total_candles):]
            mx = pd.to_datetime(served[-1][0], unit="ms", utc=True)
            assert mx < A, f"LEAK lab_lite: ventana servida {mx} >= ancla {A}"
            return served
        return _orig(symbol, timeframe, total_candles, max_retries)
    _lab.fetch_all_candles = _patched

    if args.phase == 1:
        sys.argv = ["master.py", "--from-step", "train", "--to-step", "lite", "--recycle",
                    "--symbols", sym_fmt, "--chunk-size", str(args.chunk_size)]
    else:
        sys.argv = ["master.py", "--from-step", "regime-wf", "--recycle",
                    "--symbols", sym_fmt, "--chunk-size", str(args.chunk_size)]
    master.main()

    # leakage gate post-fase (ajuste #6)
    if args.phase == 2:
        from leakage_gate import assert_asof
        gmm = sb / "regime_models" / f"{args.symbol}_regime.joblib"
        ok, errs = assert_asof(A, sb / "data_cache" / f"{args.symbol}USDT_1h.parquet",
                               str(gmm) if gmm.exists() else None, label=f"{args.symbol}@{args.anchor}")
        print(f"[LEAKAGE GATE {args.symbol}@{args.anchor}] {'PASS' if ok else 'FAIL'}", flush=True)
        for e in errs:
            print("   →", e, flush=True)
        if not ok:
            sys.exit(3)


if __name__ == "__main__":
    sys.path.insert(0, str(AUDIT))
    main()
