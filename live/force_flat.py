"""
Admin script — force-flat all positions and cancel all open orders.

Usage:
    python -m live.force_flat              # Dry-run: list state, NO execution.
    python -m live.force_flat --confirm    # Execute: close all positions + cancel all orders.

Reuses live.data_feed (_create_kraken_exchange, get_open_positions, get_open_orders)
and live.execution_manager (close_position, cancel_order, DRY_RUN module flag).

Designed para correr antes de deployment batch nuevos JSONs especialistas
(M.β cluster mapping mismatch mitigation cumulative). Idempotente: re-ejecutar
tras éxito produce 0 acciones (positions ya flat).

Recomendación operacional: stop bot via systemctl pre-ejecución para evitar
race con polling cycle bot.
"""
from __future__ import annotations

import argparse
import asyncio
import logging
import sys
from pathlib import Path

_project_root = str(Path(__file__).parent.parent)
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

from live import execution_manager
from live.data_feed import (
    _create_kraken_exchange,
    get_open_orders,
    get_open_positions,
)
from live.execution_manager import cancel_order, close_position

logger = logging.getLogger(__name__)


async def fetch_state(exchange):
    """Snapshot current state — no execution."""
    positions = await get_open_positions(exchange=exchange)
    orders = await get_open_orders(exchange=exchange)
    return positions, orders


def print_state(positions, orders, header):
    print(f"\n=== {header} ===")
    print(f"Open positions: {len(positions)}")
    for sym, pos in sorted(positions.items()):
        print(
            f"  {sym}: side={pos.get('side')} size={pos.get('size')} "
            f"entry={pos.get('entry_price')} pnl={pos.get('unrealized_pnl', 0.0):.2f} "
            f"stop={pos.get('stop_order_id') or '-'}"
        )
    print(f"Open orders: {len(orders)}")
    for o in sorted(orders, key=lambda x: (x.get("symbol", ""), x.get("id", ""))):
        print(
            f"  {o.get('symbol')}: id={o.get('id')} type={o.get('type')} "
            f"side={o.get('side')} amount={o.get('amount')} price={o.get('price')}"
        )


async def force_flat(exchange) -> int:
    """Close all positions, then sweep any remaining orders. Return exit code."""
    positions, orders = await fetch_state(exchange)
    print_state(positions, orders, "PRE force-flat")

    if not positions and not orders:
        print("\n[OK] Already flat — 0 actions needed")
        return 0

    closed = 0
    close_failures = []
    for sym, pos in sorted(positions.items()):
        try:
            result = await close_position(sym, pos, exchange)
            action = result.get("action", "unknown")
            if action in ("closed", "already_closed_by_sl", "closed_dry"):
                closed += 1
                logger.info(f"[FORCE_FLAT] {sym}: {action}")
            else:
                err = result.get("error", "")
                logger.error(f"[FORCE_FLAT] {sym}: action={action} error={err}")
                close_failures.append((sym, action, err))
        except Exception as e:
            logger.error(f"[FORCE_FLAT] close_position({sym}) raised: {e}")
            close_failures.append((sym, "exception", str(e)))

    _, orders_remaining = await fetch_state(exchange)
    canceled = 0
    cancel_failures = []
    for o in orders_remaining:
        sym = o.get("symbol", "")
        order_id = o.get("id", "")
        try:
            ok = await cancel_order(order_id, sym, exchange)
            if ok:
                canceled += 1
            else:
                cancel_failures.append((sym, order_id, "returned False"))
        except Exception as e:
            logger.error(f"[FORCE_FLAT] cancel_order({order_id}, {sym}) raised: {e}")
            cancel_failures.append((sym, order_id, str(e)))

    positions_final, orders_final = await fetch_state(exchange)
    print_state(positions_final, orders_final, "POST force-flat")

    print(f"\n=== Force-flat summary ===")
    print(f"Closed: {closed}/{len(positions)}")
    print(f"Canceled (sweep): {canceled}")
    if close_failures:
        print(f"Close failures: {len(close_failures)}")
        for sym, action, err in close_failures:
            print(f"  {sym}: action={action} err={err}")
    if cancel_failures:
        print(f"Cancel failures: {len(cancel_failures)}")
        for sym, oid, err in cancel_failures:
            print(f"  {sym} {oid}: {err}")

    if positions_final or orders_final:
        print(f"\n[WARN] Residual: {len(positions_final)} positions, {len(orders_final)} orders")
        return 1

    print("\n[OK] All flat — 0 positions, 0 orders")
    return 0


async def main_async(confirm: bool) -> int:
    exchange = _create_kraken_exchange()
    try:
        if confirm:
            execution_manager.DRY_RUN = False
            return await force_flat(exchange)
        positions, orders = await fetch_state(exchange)
        print_state(positions, orders, "Current state (dry-run, no execution)")
        print("\nDry-run only. Pass --confirm to execute force-flat.")
        return 0
    finally:
        await exchange.close()


def main():
    parser = argparse.ArgumentParser(
        description="Force-flat admin script: close all positions + cancel all orders.",
    )
    parser.add_argument(
        "--confirm",
        action="store_true",
        help="Execute force-flat (otherwise dry-run only).",
    )
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
        datefmt="%H:%M:%S",
    )

    exit_code = asyncio.run(main_async(args.confirm))
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
