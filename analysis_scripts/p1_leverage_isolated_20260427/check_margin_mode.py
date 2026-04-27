"""Read-only verification BingX margin mode operacional bot v2.4.5.
T7 mitigation Fase 2 P1 leverage analysis. NO modifica state.
"""
import asyncio, os
from pathlib import Path

env_path = Path("/home/trader/combolab/.env")
if env_path.exists():
    for line in env_path.read_text().splitlines():
        if "=" in line and not line.startswith("#"):
            k, _, v = line.partition("=")
            os.environ[k.strip()] = v.strip().strip('"').strip("'")

import ccxt.async_support as ccxt_async


async def main():
    api_key = os.environ.get("BINGX_API_KEY", "")
    api_sec = os.environ.get("BINGX_API_SECRET", "")
    if not api_key or not api_sec:
        print("MISSING_CREDENTIALS")
        return

    ex = ccxt_async.bingx({
        "apiKey": api_key,
        "secret": api_sec,
        "options": {"defaultType": "swap"},
        "enableRateLimit": True,
    })

    try:
        print("=== fetch_position_mode ===")
        try:
            mode = await ex.fetch_position_mode()
            print(f"position_mode: {mode}")
        except Exception as e:
            print(f"fetch_position_mode error: {type(e).__name__}: {e}")

        print("\n=== fetch_positions (sample) ===")
        try:
            positions = await ex.fetch_positions()
            open_pos = [p for p in positions if p.get("contracts", 0) and float(p.get("contracts", 0)) != 0]
            print(f"Total positions returned: {len(positions)}, open (contracts!=0): {len(open_pos)}")
            if open_pos:
                p = open_pos[0]
                print(f"Sample symbol: {p.get('symbol')}")
                print(f"  marginMode: {p.get('marginMode')!r}")
                print(f"  marginType: {p.get('marginType')!r}")
                print(f"  leverage: {p.get('leverage')!r}")
                print(f"  initialMargin: {p.get('initialMargin')!r}")
                print(f"  notional: {p.get('notional')!r}")
                print(f"  contracts: {p.get('contracts')!r}")
                info = p.get("info", {}) or {}
                print(f"  info.marginMode: {info.get('marginMode')!r}")
                print(f"  info.marginType: {info.get('marginType')!r}")
                print(f"  info.leverage: {info.get('leverage')!r}")
                print(f"  info.positionSide: {info.get('positionSide')!r}")
                print(f"  info keys (first 20): {list(info.keys())[:20]}")
        except Exception as e:
            print(f"fetch_positions error: {type(e).__name__}: {e}")

        print("\n=== fetch_balance info ===")
        try:
            bal = await ex.fetch_balance()
            info_keys = list((bal.get("info", {}) or {}).keys())[:20]
            print(f"info keys (first 20): {info_keys}")
        except Exception as e:
            print(f"fetch_balance error: {type(e).__name__}: {e}")

    finally:
        await ex.close()


if __name__ == "__main__":
    asyncio.run(main())
