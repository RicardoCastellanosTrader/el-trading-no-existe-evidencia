"""
live_engine.py — Orquestador del ciclo horario 24/7.

Coordina data_feed -> brain_engine -> portfolio_manager -> execution_manager
con timing preciso al cierre de cada vela 1h.
"""

import asyncio
import json
import logging
import os
import signal
import sys
import time
import traceback
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from pathlib import Path

import ccxt.async_support as ccxt_async

from live.data_feed import (
    _create_bingx_exchange,
    download_all_ohlcv,
    get_open_positions,
    get_open_orders,
    get_balance,
    MASTER_SYMBOLS,
)
from live.brain_engine import (
    BrainState,
    load_models,
    classify_regimes,
    apply_btc_override,
    select_active_configs,
    generate_signals,
)
from live.portfolio_manager import (
    PortfolioConfig,
    load_portfolio_config,
    allocate_positions,
)
from live import execution_manager
from live.execution_manager import (
    ExecutionReport,
    execute_cycle as exec_cycle,
    get_dry_run_positions,
    save_dry_run_positions,
    load_dry_run_positions,
    log_trade,
)
from live.health_monitor import (
    HealthConfig,
    evaluate_health,
    generate_daily_health_summary,
)

logger = logging.getLogger("live.live_engine")

_project_root = Path(__file__).parent.parent


# ---------------------------------------------------------------------------
# EngineConfig
# ---------------------------------------------------------------------------

@dataclass
class EngineConfig:
    # Timing
    cycle_offset_seconds: float = 10.0      # segundos antes del cierre para despertar
    execution_offset_ms: float = 500.0       # ms antes del cierre para disparar órdenes
    max_cycle_duration_seconds: float = 30.0

    # Modos
    dry_run: bool = True
    symbols: list = None                     # None = MASTER_SYMBOLS

    # Resiliencia
    max_consecutive_errors: int = 3
    error_pause_minutes: int = 60

    # Alertas
    telegram_bot_token: str = None
    telegram_chat_id: str = None
    alert_on_trade: bool = True
    alert_on_error: bool = True
    alert_daily_summary: bool = True
    alert_dd_threshold_pct: float = 5.0

    # Paths
    regime_models_dir: str = "regime_models"
    specialist_configs_dir: str = "regime_wf"
    trade_log_path: str = "trade_history.csv"
    engine_log_path: str = "engine.log"
    state_file_path: str = "engine_state.json"


def load_engine_config(config_path: str | None = None) -> EngineConfig:
    """Carga config desde JSON o retorna defaults."""
    if config_path and os.path.exists(config_path):
        with open(config_path) as f:
            data = json.load(f)
        cfg = EngineConfig()
        for k, v in data.items():
            if hasattr(cfg, k):
                setattr(cfg, k, v)
    else:
        cfg = EngineConfig()

    # Telegram: env vars tienen prioridad si el config no las trajo
    if not cfg.telegram_bot_token:
        cfg.telegram_bot_token = os.environ.get("TELEGRAM_BOT_TOKEN")
    if not cfg.telegram_chat_id:
        cfg.telegram_chat_id = os.environ.get("TELEGRAM_CHAT_ID")

    return cfg


# ---------------------------------------------------------------------------
# CycleReport
# ---------------------------------------------------------------------------

@dataclass
class CycleReport:
    timestamp: str = ""
    cycle_number: int = 0
    duration_ms: float = 0.0
    symbols_processed: int = 0
    signals_summary: dict = field(default_factory=dict)
    allocations_summary: dict = field(default_factory=dict)
    execution_report: ExecutionReport = field(default_factory=ExecutionReport)
    errors: list = field(default_factory=list)
    balance_after: dict = field(default_factory=dict)


# ---------------------------------------------------------------------------
# LiveEngine
# ---------------------------------------------------------------------------

class LiveEngine:
    """Motor de ejecución 24/7."""

    def __init__(self, config: EngineConfig | None = None):
        self.config = config or EngineConfig()
        self.brain: BrainState | None = None
        self.portfolio_config: PortfolioConfig | None = None
        self.exchange: ccxt_async.bingx | None = None

        self.running: bool = False
        self.cycle_count: int = 0
        self.start_time: datetime | None = None
        self.last_cycle_time: datetime | None = None
        self.consecutive_errors: int = 0
        self._balance_24h_ago: float | None = None
        self._last_daily_summary: int = -1  # hora UTC del último resumen

        # Drawdown circuit breaker
        self._peak_balance: float = 0.0
        self._current_balance: float = 0.0  # v2.3.6: persistido para health_monitor H1
        self._dd_multiplier: float = 1.0
        self._prev_dd_multiplier: float = 1.0  # para detectar cambios
        self._circuit_breaker_active: bool = False  # histeresis
        self._dd_alert_pending: str | None = None   # alerta pendiente

    # ------------------------------------------------------------------
    # 1. start
    # ------------------------------------------------------------------
    async def start(self):
        """Secuencia de arranque."""
        t0 = time.perf_counter()
        symbols = self.config.symbols or MASTER_SYMBOLS
        mode = "DRY_RUN" if self.config.dry_run else "LIVE"

        logger.info(f"[ENGINE] Arrancando en modo {mode} con {len(symbols)} simbolos")

        # Propagar dry_run al execution_manager
        execution_manager.DRY_RUN = self.config.dry_run

        # 1. Conexión al exchange
        try:
            self.exchange = _create_bingx_exchange()
            bal = await get_balance(exchange=self.exchange)
            logger.info(f"[ENGINE] Conexion BingX OK. Balance: {bal['total']:.2f} USDT")
            self._balance_24h_ago = bal["total"]
        except Exception as e:
            logger.critical(f"[ENGINE] Fallo de conexion a BingX: {e}")
            raise

        # 2. Cargar modelos GMM + specialist configs
        models_dir = str(_project_root / self.config.regime_models_dir)
        configs_dir = str(_project_root / self.config.specialist_configs_dir)

        self.brain = load_models(models_dir, configs_dir, symbols)
        n_gmm = len(self.brain.gmm_models)
        n_specs = len(self.brain.specialist_configs)
        logger.info(f"[ENGINE] Modelos cargados: {n_gmm} GMM, {n_specs} specialist configs")

        if n_specs == 0:
            logger.warning(
                "[ENGINE] Sin specialist_configs.json. "
                "Solo se usaran modelos GMM con fallback."
            )

        # 3. Portfolio config
        self.portfolio_config = load_portfolio_config(configs_dir)
        logger.info(
            f"[ENGINE] Portfolio config: {len(self.portfolio_config.leverage_map or {})} "
            f"leverage entries, {len(self.portfolio_config.sector_map or {})} sectores"
        )

        # 4. Restaurar estado si existe
        self._load_state()

        # 5. Sincronizar posiciones del exchange con brain state
        try:
            positions = await get_open_positions(exchange=self.exchange)
            self._sync_brain_positions(positions)
            n_pos = len(positions)
            logger.info(f"[ENGINE] {n_pos} posiciones sincronizadas desde exchange")
        except Exception as e:
            logger.warning(f"[ENGINE] No se pudieron sincronizar posiciones: {e}")
            positions = {}

        # 6. Purgar posiciones fantasma del brain state que no existen en
        # la fuente de verdad (exchange en LIVE, _dry_run_positions en DRY_RUN).
        # v2.3.7 (fix L3): extendido a DRY_RUN. Sin esto, state stale post-restart
        # en DRY_RUN deja fantasmas hasta el primer reconcile post-ciclo.
        if self.brain:
            if self.config.dry_run:
                truth_positions = get_dry_run_positions()
            else:
                truth_positions = positions
            purged = 0
            for sym, ss in self.brain.symbol_state.items():
                if ss.position != 0 and sym not in truth_positions:
                    logger.warning(
                        f"[ENGINE] Purgando posicion fantasma {sym} "
                        f"(pos={ss.position}, entry={ss.entry_price}) — "
                        f"no existe en fuente de verdad "
                        f"({'dry_run' if self.config.dry_run else 'exchange'})"
                    )
                    ss.position = 0
                    ss.entry_price = 0.0
                    ss.sl_level = 0.0
                    ss.stop_order_id = ""
                    ss.entry_filters_forming = 0
                    purged += 1
            if purged:
                logger.info(f"[ENGINE] {purged} posiciones fantasma purgadas")

        self.start_time = datetime.now(timezone.utc)
        self.running = True
        elapsed = time.perf_counter() - t0

        msg = (
            f"Bot arrancado. {len(symbols)} simbolos, "
            f"{n_specs} con specialists, {mode}, "
            f"balance={bal['total']:.0f} USDT ({elapsed:.1f}s)"
        )
        logger.info(f"[ENGINE] {msg}")
        await self._send_alert(f"[START] {msg}")

    # ------------------------------------------------------------------
    # Drawdown circuit breaker
    # ------------------------------------------------------------------
    def _calc_dd_multiplier(self, balance: float) -> float:
        """
        Reduce exposicion segun drawdown desde el pico de equity.

        DD 0-5%:   multiplier = 1.0 (operacion normal)
        DD 5-10%:  multiplier = 0.75 (reduce 25%)
        DD 10-15%: multiplier = 0.50 (reduce 50%)
        DD >15%:   multiplier = 0.0 (pausa operaciones, solo cierra)

        Histeresis: cuando DD baja de 12% tras circuit breaker, reanuda con 0.50.
        """
        if balance <= 0:
            return 0.0

        # v2.3.6: capturar balance actual para persistencia (health_monitor H1)
        self._current_balance = balance

        # Actualizar pico
        self._peak_balance = max(self._peak_balance, balance)

        if self._peak_balance <= 0:
            return 1.0

        dd_pct = (self._peak_balance - balance) / self._peak_balance * 100.0

        # Histeresis: si el circuit breaker estaba activo (DD >15%)
        # no reanudar hasta que DD < 12%
        if self._circuit_breaker_active:
            if dd_pct < 12.0:
                self._circuit_breaker_active = False
                multiplier = 0.50
            else:
                multiplier = 0.0
        elif dd_pct > 15.0:
            multiplier = 0.0
            self._circuit_breaker_active = True
        elif dd_pct > 10.0:
            multiplier = 0.50
        elif dd_pct > 5.0:
            multiplier = 0.75
        else:
            multiplier = 1.0

        # Logging: solo cuando cambia o DD > 5%
        if multiplier != self._prev_dd_multiplier or dd_pct > 5.0:
            logger.info(
                f"[ENGINE] DD circuit breaker: balance={balance:.0f} USDT, "
                f"peak={self._peak_balance:.0f}, DD={dd_pct:.1f}%, "
                f"multiplier={multiplier}"
            )

        # Alertas Telegram por cruce de umbrales (pendiente, se envia en run_cycle)
        prev = self._prev_dd_multiplier
        if multiplier != prev:
            if multiplier == 0.0 and prev != 0.0:
                self._dd_alert_pending = (
                    "CIRCUIT BREAKER ACTIVO: DD >15%, operaciones pausadas. "
                    f"peak={self._peak_balance:.0f} -> balance={balance:.0f} USDT"
                )
            elif multiplier == 0.50 and prev == 0.0:
                self._dd_alert_pending = (
                    "Circuit breaker desactivado, sizing al 50%. "
                    f"DD={dd_pct:.1f}%, balance={balance:.0f} USDT"
                )
            elif multiplier == 0.50 and prev > 0.50:
                self._dd_alert_pending = (
                    f"DD severo: -{dd_pct:.1f}%, sizing reducido al 50%. "
                    f"peak={self._peak_balance:.0f} -> {balance:.0f} USDT"
                )
            elif multiplier == 0.75 and prev == 1.0:
                self._dd_alert_pending = (
                    f"DD alert: -{dd_pct:.1f}% desde pico "
                    f"({self._peak_balance:.0f} -> {balance:.0f} USDT)"
                )

        self._prev_dd_multiplier = multiplier
        self._dd_multiplier = multiplier
        return multiplier

    # ------------------------------------------------------------------
    # 2. stop
    # ------------------------------------------------------------------
    async def stop(self):
        """Parada limpia."""
        self.running = False
        logger.info("[ENGINE] Deteniendo...")

        # Guardar estado
        self._save_state()

        # Contar posiciones abiertas (reales + dry_run)
        n_pos = 0
        try:
            positions = await get_open_positions(exchange=self.exchange)
            n_pos = len(positions)
        except Exception:
            pass
        if self.config.dry_run:
            n_pos += len(get_dry_run_positions())

        # Cerrar exchange
        if self.exchange:
            try:
                await self.exchange.close()
            except Exception:
                pass
            self.exchange = None

        msg = (
            f"Bot detenido. {n_pos} posiciones abiertas con stops. "
            f"{self.cycle_count} ciclos ejecutados."
        )
        logger.info(f"[ENGINE] {msg}")
        await self._send_alert(f"[STOP] {msg}")

    # ------------------------------------------------------------------
    # 3. run_cycle
    # ------------------------------------------------------------------
    async def run_cycle(self) -> CycleReport:
        """
        v2.3.7 (fix L5): wrapper con enforcement de timeout.
        Si la logica interna cuelga (ej. BingX outage con retry largo),
        cancela el ciclo para no perder ventana del siguiente cierre.
        """
        timeout_s = self.config.max_cycle_duration_seconds
        try:
            return await asyncio.wait_for(self._run_cycle_inner(), timeout=timeout_s)
        except asyncio.TimeoutError:
            logger.error(
                f"[ENGINE] Ciclo {self.cycle_count} TIMEOUT tras {timeout_s}s "
                f"— abortado para preservar proximo cierre"
            )
            self.consecutive_errors += 1
            report = CycleReport(
                timestamp=datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S"),
                cycle_number=self.cycle_count,
            )
            report.errors.append(f"timeout after {timeout_s}s")
            self.cycle_count += 1
            self.last_cycle_time = datetime.now(timezone.utc)
            return report

    async def _run_cycle_inner(self) -> CycleReport:
        """Ejecuta un ciclo completo (logica interna, sin timeout)."""
        t0 = time.perf_counter()
        now_utc = datetime.now(timezone.utc)
        report = CycleReport(
            timestamp=now_utc.strftime("%Y-%m-%d %H:%M:%S"),
            cycle_number=self.cycle_count,
        )

        try:
            symbols = self.config.symbols or MASTER_SYMBOLS

            # ---- DATOS ----
            logger.info(f"[ENGINE] Ciclo {self.cycle_count} — descargando datos")
            market_data = await download_all_ohlcv(symbols, exchange=self.exchange)
            positions = await get_open_positions(exchange=self.exchange)
            orders = await get_open_orders(exchange=self.exchange)
            balance = await get_balance(exchange=self.exchange)

            # En DRY_RUN, el exchange no tiene posiciones simuladas;
            # inyectar las posiciones dry_run para que brain/portfolio las vean
            if self.config.dry_run:
                dry_pos = get_dry_run_positions()
                for sym, dp in dry_pos.items():
                    if sym not in positions:
                        positions[sym] = dp

            ok_data = sum(1 for v in market_data.values() if v is not None)
            if ok_data == 0:
                raise RuntimeError("No market data received")

            report.symbols_processed = ok_data

            # ---- CLASIFICACION + SENALES ----
            regimes = classify_regimes(self.brain, market_data)
            regimes = apply_btc_override(self.brain, regimes)
            active_configs = select_active_configs(self.brain, regimes)

            # ---- SNAPSHOT PRE-SIGNAL STATE (v2.3.2 phantom fix) ----
            pre_signal_state = {}
            if self.brain:
                for sym, ss in self.brain.symbol_state.items():
                    if ss.position != 0:
                        pre_signal_state[sym] = {
                            "position": ss.position,
                            "side": "long" if ss.position == 1 else "short",
                            "entry_price": ss.entry_price,
                            "sl_level": ss.sl_level,
                            "entry_bar_timestamp": getattr(
                                ss, "entry_bar_timestamp", 0
                            ),
                            "entry_timestamp_ms": getattr(
                                ss, "entry_timestamp_ms", 0
                            ),
                        }

            signals = generate_signals(self.brain, market_data, active_configs)

            active_signals = {
                s: sig["action"]
                for s, sig in signals.items()
                if sig["action"] not in ("FLAT", "HOLD")
            }
            report.signals_summary = active_signals
            logger.info(f"[ENGINE] {len(active_signals)} senales activas")

            # ---- ENGINE_STATE (estado global del ciclo, v2.3.1) ----
            total_balance = balance.get("total", 0.0)
            n_open = sum(
                1 for p in positions.values()
                if p.get("side", "") in ("long", "short")
            )
            _es = {
                "t": int(now_utc.timestamp()),
                "bal": round(total_balance, 2),
                "peak": round(self._peak_balance, 2),
                "dd_pct": round(total_balance / self._peak_balance - 1, 4) if self._peak_balance > 0 else 0.0,
                "dd_mult": self._dd_multiplier,
                "cb_active": self._circuit_breaker_active,
                "n_open": n_open,
            }
            logger.info(f"[ENGINE_STATE] {json.dumps(_es, separators=(',', ':'))}")

            # ---- LOG SENALES RAW (pre-portfolio, para auditoria v2.3.1) ----
            raw_for_log = {}
            for sym, sig in signals.items():
                if sig["action"] in ("FLAT", "HOLD"):
                    continue
                entry = {"a": sig["action"], "r": sig.get("reason", "")}
                ep = sig.get("entry_price", 0.0)
                if ep:
                    entry["p"] = ep
                sl = sig.get("sl_price", 0.0)
                if sl:
                    entry["sl"] = sl
                c = sig.get("confidence", 0.0)
                if c:
                    entry["c"] = round(c, 3)
                cfg = active_configs.get(sym, {})
                st = cfg.get("strategy_type", "")
                entry["s"] = "MR" if st == "mean_reversion" else "TF"
                k = cfg.get("cluster")
                if k is not None:
                    entry["k"] = k
                df_sym = market_data.get(sym)
                if df_sym is not None and len(df_sym) > 0:
                    ts_val = df_sym["timestamp"].iloc[-1]
                    if hasattr(ts_val, "timestamp"):
                        entry["t"] = int(ts_val.timestamp())
                raw_for_log[sym] = entry
            if raw_for_log:
                logger.info(f"[SIGNALS_RAW] {json.dumps(raw_for_log, separators=(',', ':'))}")

            # ---- DD CIRCUIT BREAKER ----
            dd_mult = self._calc_dd_multiplier(total_balance)
            if self._dd_alert_pending:
                await self._send_alert(f"[DD] {self._dd_alert_pending}")
                self._dd_alert_pending = None

            # ---- PORTFOLIO ----
            allocations = allocate_positions(
                signals, balance, positions, regimes,
                market_data, self.portfolio_config,
                dd_multiplier=dd_mult,
            )
            entry_allocs = {
                s: a["action"]
                for s, a in allocations.items()
                if a.get("action") in ("LONG", "SHORT", "CLOSE_LONG", "CLOSE_SHORT")
            }
            report.allocations_summary = entry_allocs

            # ---- LOG SENALES DESCARTADAS POR PORTFOLIO (v2.3.1) ----
            discarded = {}
            for sym in raw_for_log:
                if sym not in entry_allocs:
                    reason = allocations.get(sym, {}).get("reason", "unknown")
                    discarded[sym] = {"a": raw_for_log[sym]["a"], "d": reason}
                    if reason == "unknown":
                        logger.warning(
                            f"[SIGNALS_DISCARDED] {sym} descartado sin reason "
                            f"en allocations"
                        )
            if discarded:
                logger.info(f"[SIGNALS_DISCARDED] {json.dumps(discarded, separators=(',', ':'))}")

            # ---- LOG SENALES EJECUTADAS CON FACTORES (v2.3.1) ----
            executed_log = {}
            for sym, alloc in allocations.items():
                if (alloc.get("action") in ("LONG", "SHORT")
                        and alloc.get("size_usdt", 0) > 0):
                    executed_log[sym] = {
                        "a": alloc["action"],
                        "sz": alloc["size_usdt"],
                        "lv": alloc["leverage"],
                        "vw": round(alloc.get("vol_weight", 1.0), 4),
                        "bf": round(alloc.get("blending_factor", 1.0), 4),
                        "br": round(alloc.get("block_reduction", 1.0), 4),
                        "dd": dd_mult,
                    }
            if executed_log:
                logger.info(f"[SIGNALS_EXECUTED] {json.dumps(executed_log, separators=(',', ':'))}")

            # ---- ENRIQUECER ORDENES CON STOPS CONOCIDOS DEL BRAIN ----
            # Fix: BingX puede no devolver trigger orders en fetch_open_orders.
            # Inyectar stops conocidos del brain state para que reconcile_state
            # y update_trailing_stop los encuentren y no dupliquen.
            if self.brain and not self.config.dry_run:
                order_syms = {o["symbol"] for o in orders}
                for sym, ss in self.brain.symbol_state.items():
                    if (ss.position != 0
                            and ss.stop_order_id
                            and sym not in order_syms):
                        orders.append({
                            "id": ss.stop_order_id,
                            "symbol": sym,
                            "type": "stop_market",
                            "side": "sell" if ss.position == 1 else "buy",
                            "price": ss.sl_level,
                            "amount": 0,
                            "_from_brain_state": True,
                        })

            # ---- ESPERA HASTA VENTANA DE EJECUCION ----
            await self._wait_for_execution_window()

            # ---- v2.3.3: enriquecer positions con entry_timestamp_ms del brain ----
            # Para que close_position / log_trade tengan la ms fill-time al cerrar.
            if self.brain:
                for sym, pos in positions.items():
                    ss = self.brain.symbol_state.get(sym)
                    if ss and getattr(ss, "entry_timestamp_ms", 0) > 0:
                        pos["entry_timestamp_ms"] = ss.entry_timestamp_ms

            # ---- EJECUCION ----
            exec_report = await exec_cycle(
                allocations, positions, orders, self.exchange,
            )
            report.execution_report = exec_report

            # ---- v2.3.3: persistir entry_timestamp_ms de aperturas exitosas ----
            if self.brain:
                for opened in exec_report.orders_sent:
                    sym = opened.get("symbol")
                    ts_ms = opened.get("entry_timestamp_ms", 0)
                    if sym and ts_ms:
                        ss = self.brain.symbol_state.get(sym)
                        if ss:
                            ss.entry_timestamp_ms = int(ts_ms)

            # ---- RECONCILIACION POST-EJECUCION (v2.3.2) ----
            await self._reconcile_brain_after_execution(
                exec_report, pre_signal_state, allocations,
            )

            # ---- POST-CICLO ----
            await self._post_cycle(exec_report, balance)

            self.consecutive_errors = 0

        except Exception as e:
            self.consecutive_errors += 1
            err_msg = f"Ciclo {self.cycle_count} fallido: {e}"
            logger.critical(f"[ENGINE] {err_msg}", exc_info=True)
            report.errors.append(err_msg)
            await self._handle_cycle_error(e)

        elapsed_ms = (time.perf_counter() - t0) * 1000
        report.duration_ms = elapsed_ms
        self.cycle_count += 1
        self.last_cycle_time = datetime.now(timezone.utc)

        logger.info(
            f"[ENGINE] Ciclo {report.cycle_number} completado en {elapsed_ms:.0f}ms"
        )

        return report

    # ------------------------------------------------------------------
    # 4. run_forever
    # ------------------------------------------------------------------
    async def run_forever(self):
        """Bucle principal — programa ciclos cada hora al xx:59:50."""
        await self.start()

        try:
            while self.running:
                next_act = self._next_activation_time()
                now_utc = datetime.now(timezone.utc)
                sleep_s = (next_act - now_utc).total_seconds()

                if sleep_s > 0:
                    logger.debug(
                        f"[ENGINE] Durmiendo {sleep_s:.1f}s hasta {next_act.strftime('%H:%M:%S')}"
                    )
                    # Dormir en tramos de 1s para poder responder a shutdown
                    while sleep_s > 0 and self.running:
                        chunk = min(sleep_s, 1.0)
                        await asyncio.sleep(chunk)
                        sleep_s -= chunk

                if not self.running:
                    break

                report = await self.run_cycle()

                # Pausa por errores consecutivos
                if self.consecutive_errors >= self.config.max_consecutive_errors:
                    pause_min = self.config.error_pause_minutes
                    msg = (
                        f"Bot en pausa {pause_min}m: "
                        f"{self.consecutive_errors} errores consecutivos"
                    )
                    logger.critical(f"[ENGINE] {msg}")
                    await self._send_alert(f"[WARN] {msg}")

                    # Dormir en tramos para poder responder a shutdown
                    remaining = pause_min * 60
                    while remaining > 0 and self.running:
                        chunk = min(remaining, 1.0)
                        await asyncio.sleep(chunk)
                        remaining -= chunk

                    self.consecutive_errors = 0
        except (asyncio.CancelledError, KeyboardInterrupt):
            logger.info("[ENGINE] Interrupcion recibida, cerrando...")
        finally:
            await self.stop()

    # ------------------------------------------------------------------
    # 5. _wait_for_execution_window
    # ------------------------------------------------------------------
    async def _wait_for_execution_window(self):
        """Duerme hasta xx:59:59.500 (500ms antes del cierre)."""
        now = datetime.now(timezone.utc)
        offset_ms = self.config.execution_offset_ms

        # Target: minuto 59, segundo 59, microsecond basado en offset
        target_us = int((1000 - offset_ms) * 1000)
        target = now.replace(minute=59, second=59, microsecond=target_us)

        # Si ya pasamos el minuto 59 (estamos en minuto 0+)
        if now.minute < 59:
            # Estamos demasiado temprano o ya pasó — ajustar
            if now.minute == 0 and now.second < 5:
                # Acabamos de pasar el cierre
                logger.warning("[ENGINE] Ventana de ejecucion pasada, ejecutando inmediatamente")
                return
            # Para --once mode u otros casos, no esperar
            logger.debug("[ENGINE] No en ventana horaria, ejecutando sin espera")
            return

        delta = (target - now).total_seconds()
        if delta > 0:
            logger.debug(f"[ENGINE] Esperando {delta:.2f}s hasta ventana de ejecucion")
            await asyncio.sleep(delta)
        elif delta < -5:
            logger.warning(
                f"[ENGINE] Ventana pasada por {-delta:.1f}s, ejecutando inmediatamente"
            )

    # ------------------------------------------------------------------
    # 6. _post_cycle
    # ------------------------------------------------------------------
    async def _post_cycle(self, exec_report: ExecutionReport, balance: dict):
        """Post-procesamiento del ciclo."""
        # Actualizar stop_order_id en brain state desde ejecucion
        if self.brain:
            # Nuevas posiciones abiertas -> guardar stop_order_id
            for order in exec_report.orders_sent:
                sym = order.get("symbol", "")
                stop_id = order.get("stop_order_id", "")
                if sym and stop_id:
                    state = self.brain.get_state(sym)
                    state.stop_order_id = stop_id
            # Stops actualizados -> actualizar stop_order_id
            for stop in exec_report.stops_updated:
                sym = stop.get("symbol", "")
                new_id = stop.get("new_order_id", "")
                if sym and new_id:
                    state = self.brain.get_state(sym)
                    state.stop_order_id = new_id
            # Stops de emergencia -> actualizar stop_order_id
            for stop in exec_report.stops_placed:
                sym = stop.get("symbol", "")
                stop_id = stop.get("stop_order_id") or stop.get("new_order_id", "")
                if sym and stop_id:
                    state = self.brain.get_state(sym)
                    state.stop_order_id = stop_id
            # Posiciones cerradas -> limpiar stop_order_id
            for close in exec_report.positions_closed:
                sym = close.get("symbol", "")
                if sym:
                    state = self.brain.get_state(sym)
                    state.stop_order_id = ""

        # Guardar estado
        self._save_state()

        # Alertas por trades
        # v2.3.10 (fix D4): fire-and-forget via asyncio.create_task para
        # reducir latencia del cycle. Con N trades en un ciclo y timeout
        # Telegram 10s, los awaits secuenciales sumaban 1-3s al cycle.
        # Alertas son observabilidad, no bloqueantes — _send_alert tiene
        # try/except interno que captura y loguea errores. El event loop
        # retiene las tasks hasta completion, no hace falta guardar
        # referencias para evitar GC.
        if self.config.alert_on_trade:
            for order in exec_report.orders_sent:
                sym = order.get("symbol", "")
                side = order.get("side", "")
                sl = order.get("sl_price", 0)
                msg = (
                    f"[OPEN] {side.upper()} {sym} "
                    f"size={order.get('size', 0)} "
                    f"@ {order.get('entry_price', 0):.2f} "
                    f"[SL={sl:.2f}]"
                )
                asyncio.create_task(self._send_alert(msg))

            for close in exec_report.positions_closed:
                sym = close.get("symbol", "")
                side = close.get("side", "")
                pnl = close.get("pnl", 0)
                funding = close.get("funding_paid", 0)
                msg = (
                    f"[CLOSE] {side.upper()} {sym} "
                    f"@ {close.get('close_price', 0):.2f} "
                    f"PnL={pnl:+.2f} USDT"
                )
                if funding != 0:
                    msg += f" (funding: {funding:+.2f} USDT)"
                asyncio.create_task(self._send_alert(msg))

        # Alertas por errores
        if self.config.alert_on_error and exec_report.errors:
            await self._send_alert(
                f"[ERROR] {len(exec_report.errors)} errores en ciclo "
                f"{self.cycle_count}: {exec_report.errors[0]}"
            )

        # Check drawdown 24h
        total_balance = balance.get("total", 0)
        if self._balance_24h_ago and self._balance_24h_ago > 0:
            dd_pct = (1 - total_balance / self._balance_24h_ago) * 100
            if dd_pct > self.config.alert_dd_threshold_pct:
                await self._send_alert(
                    f"[DD] Drawdown {dd_pct:.1f}% en 24h: "
                    f"{self._balance_24h_ago:.0f} -> {total_balance:.0f} USDT"
                )

        # Resumen diario a las 00:00 UTC
        now_utc = datetime.now(timezone.utc)
        if (self.config.alert_daily_summary
                and now_utc.hour == 0
                and self._last_daily_summary != now_utc.day):
            self._last_daily_summary = now_utc.day
            await self._send_daily_summary(balance)
            self._balance_24h_ago = total_balance

            # Health monitor — evalúa rendimiento real vs esperado
            try:
                health_cfg = HealthConfig(
                    trade_log_path=self.config.trade_log_path,
                    specialist_configs_dir=self.config.specialist_configs_dir,
                )
                health_summary = generate_daily_health_summary(health_cfg)
                await self._send_alert(health_summary)
            except Exception as e:
                logger.warning(f"[ENGINE] Health monitor error: {e}")

    async def _send_daily_summary(self, balance: dict):
        """Envía resumen diario."""
        total = balance.get("total", 0)
        free = balance.get("free", 0)
        used = balance.get("used", 0)

        if self._balance_24h_ago and self._balance_24h_ago > 0:
            change = total - self._balance_24h_ago
            change_pct = change / self._balance_24h_ago * 100
            pnl_str = f"{change:+.2f} USDT ({change_pct:+.1f}%)"
        else:
            pnl_str = "N/A"

        msg = (
            f"[DAILY] Resumen diario\n"
            f"  Balance: {total:.2f} USDT (libre: {free:.0f}, usado: {used:.0f})\n"
            f"  PnL 24h: {pnl_str}\n"
            f"  Ciclos: {self.cycle_count} ejecutados"
        )
        await self._send_alert(msg)

    # ------------------------------------------------------------------
    # 6b. _reconcile_brain_after_execution (v2.3.2)
    # ------------------------------------------------------------------
    async def _reconcile_brain_after_execution(
        self, exec_report, pre_signal_state, allocations,
    ):
        """
        v2.3.2: Reconcilia brain state con BingX real despues de ejecucion.

        Bug #1: Limpia fantasmas (brain position!=0, BingX vacio).
        Bug #2: Registra trades cerrados por SL trigger entre ciclos
                (orphan closes no capturados por reconcile_state).
        """
        if not self.brain:
            return

        # Fetch posiciones reales frescas post-ejecucion
        try:
            real_positions = await get_open_positions(exchange=self.exchange)
        except Exception as e:
            logger.warning(f"[BRAIN_RECONCILE] fetch_positions failed: {e}")
            return

        if self.config.dry_run:
            dry_pos = get_dry_run_positions()
            for sym, dp in dry_pos.items():
                if sym not in real_positions:
                    real_positions[sym] = dp

        # --- Bug #2: Detectar orphan closes ---
        closed_syms = {c.get("symbol") for c in exec_report.positions_closed}

        for sym, pre in pre_signal_state.items():
            if sym in real_positions:
                continue
            if sym in closed_syms:
                continue

            alloc = allocations.get(sym, {})
            action = alloc.get("action", "")
            if action not in ("CLOSE_LONG", "CLOSE_SHORT"):
                continue

            side = pre["side"]
            entry_price = pre["entry_price"]
            sl_level = pre["sl_level"]

            if not entry_price or not sl_level:
                logger.warning(
                    f"[ORPHAN_CLOSE] {sym}: datos insuficientes "
                    f"(entry={entry_price}, sl={sl_level})"
                )
                continue

            estimated_exit = sl_level
            if side == "long":
                pnl_pct = (estimated_exit - entry_price) / entry_price
            else:
                pnl_pct = (entry_price - estimated_exit) / entry_price

            logger.info(
                f"[ORPHAN_CLOSE] {sym} reconstructed: {side} "
                f"entry={entry_price} exit~={estimated_exit} "
                f"pnl~={pnl_pct * 100:.2f}%"
            )

            log_trade({
                "symbol": sym,
                "side": side,
                "entry_price": entry_price,
                "exit_price": estimated_exit,
                "size_usdt": 0.0,
                "pnl_usdt": 0.0,
                "reason_exit": "sl_trigger_reconstructed",
                "funding_paid": 0.0,
                "flag": "reconstructed",
                "entry_timestamp_ms": pre.get("entry_timestamp_ms", 0),
            })

        # --- Bug #1: Limpiar fantasmas ---
        for sym, ss in self.brain.symbol_state.items():
            if ss.position == 0:
                continue

            real = real_positions.get(sym)
            if real is not None:
                real_side = real.get("side", "")
                if ((ss.position == 1 and real_side == "long")
                        or (ss.position == -1 and real_side == "short")):
                    continue

            prev_pos = ss.position
            prev_entry = ss.entry_price
            ss.position = 0
            ss.entry_price = 0.0
            ss.sl_level = 0.0
            ss.stop_order_id = ""
            ss.entry_filters_forming = 0
            ss.entry_timestamp_ms = 0

            logger.info(
                f"[BRAIN_RECONCILE] {sym} reset: "
                f"{'LONG' if prev_pos == 1 else 'SHORT'} "
                f"entry={prev_entry} -> position=0 "
                f"(no real BingX position)"
            )

    # ------------------------------------------------------------------
    # 7. _send_alert
    # ------------------------------------------------------------------
    async def _send_alert(self, message: str):
        """Envía alerta por Telegram. Si no configurado, solo logea."""
        logger.info(f"[ALERT] {message}")

        token = self.config.telegram_bot_token
        chat_id = self.config.telegram_chat_id
        if not token or not chat_id:
            return

        url = f"https://api.telegram.org/bot{token}/sendMessage"
        try:
            import httpx
            async with httpx.AsyncClient(timeout=10) as client:
                # v2.3.7 (fix L7): parse_mode omitido (texto plano). Mensajes
                # generados no usan tags HTML; con parse_mode=HTML caracteres
                # especiales (<,>,&) en exception msg o PnL formateado rompian
                # alerta (HTTP 400) silenciosamente.
                await client.post(url, json={
                    "chat_id": chat_id,
                    "text": message,
                })
        except ImportError:
            # Fallback a urllib si httpx no está instalado
            try:
                import urllib.request
                import urllib.parse
                data = urllib.parse.urlencode({
                    "chat_id": chat_id, "text": message,
                }).encode()
                req = urllib.request.Request(url, data=data)
                urllib.request.urlopen(req, timeout=10)
            except Exception as e:
                logger.warning(f"[ENGINE] Alerta Telegram fallida: {e}")
        except Exception as e:
            logger.warning(f"[ENGINE] Alerta Telegram fallida: {e}")

    # ------------------------------------------------------------------
    # _handle_cycle_error
    # ------------------------------------------------------------------
    async def _handle_cycle_error(self, error: Exception):
        """Manejo de errores de ciclo."""
        if self.config.alert_on_error:
            await self._send_alert(
                f"[ERROR] Ciclo {self.cycle_count} fallido "
                f"({self.consecutive_errors} consecutivos): "
                f"{type(error).__name__}: {error}"
            )

    # ------------------------------------------------------------------
    # _next_activation_time
    # ------------------------------------------------------------------
    def _next_activation_time(self) -> datetime:
        """Calcula próximo xx:59:50 UTC.

        v2.3.4 (fix L1): usa timedelta para evitar ValueError en cambio
        de mes/año. El .replace(day=now.day + 1, hour=0) original
        crasheaba en ultimo dia del mes (ej. day=31 en abril inválido).
        timedelta(hours=1) maneja rollover automaticamente.
        Tests mentales verificados:
          - 2026-04-30 23:59:51 -> target = 2026-05-01 00:59:50
          - 2026-12-31 23:59:51 -> target = 2027-01-01 00:59:50
          - 2028-02-29 23:59:51 -> target = 2028-03-01 00:59:50 (bisiesto)
        """
        now = datetime.now(timezone.utc)
        offset = self.config.cycle_offset_seconds

        # Target: minuto 59, segundo (60 - offset)
        target_second = int(60 - offset)
        target = now.replace(minute=59, second=target_second, microsecond=0)

        if now >= target:
            target = target + timedelta(hours=1)

        return target

    # ------------------------------------------------------------------
    # _sync_brain_positions
    # ------------------------------------------------------------------
    def _sync_brain_positions(self, positions: dict):
        """Sincroniza posiciones del exchange (+ dry_run simuladas) con el brain state."""
        if not self.brain:
            return

        # Merge dry_run positions
        if self.config.dry_run:
            dry_pos = get_dry_run_positions()
            for sym, dp in dry_pos.items():
                if sym not in positions:
                    positions[sym] = dp

        for sym, pos in positions.items():
            state = self.brain.get_state(sym)
            side = pos.get("side", "")
            if side == "long":
                state.position = 1
                state.entry_price = pos.get("entry_price", 0.0)
            elif side == "short":
                state.position = -1
                state.entry_price = pos.get("entry_price", 0.0)
            else:
                state.position = 0

    # ------------------------------------------------------------------
    # 8. _save_state / _load_state
    # ------------------------------------------------------------------
    def _save_state(self):
        """Guarda estado a JSON para recovery."""
        if not self.brain:
            return

        state_path = _project_root / self.config.state_file_path

        data = {
            "saved_at": datetime.now(timezone.utc).isoformat(),
            "cycle_count": self.cycle_count,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "peak_balance": self._peak_balance,
            "current_balance": self._current_balance,
            "dd_multiplier": self._dd_multiplier,
            "circuit_breaker_active": self._circuit_breaker_active,
            "symbols": {},
            "dry_run_positions": save_dry_run_positions() if self.config.dry_run else {},
        }

        for sym, ss in self.brain.symbol_state.items():
            data["symbols"][sym] = {
                "current_cluster": ss.current_cluster,
                "cluster_probs": ss.cluster_probs.tolist() if ss.cluster_probs is not None else None,
                "active_config_id": ss.active_config_id,
                "active_preset": ss.active_preset,
                "position": ss.position,
                "entry_price": ss.entry_price,
                "entry_bar_timestamp": ss.entry_bar_timestamp,
                "sl_level": ss.sl_level,
                "entry_filters_forming": ss.entry_filters_forming,
                "div_ctx_bull": ss.div_ctx_bull,
                "div_ctx_bear": ss.div_ctx_bear,
                "prev_div_bull_now": ss.prev_div_bull_now,
                "prev_div_bear_now": ss.prev_div_bear_now,
                "prev_zone_bull": ss.prev_zone_bull,
                "prev_zone_bear": ss.prev_zone_bear,
                "cooldown_until": ss.cooldown_until,
                "bars_since_entry": ss.bars_since_entry,
                "stop_order_id": ss.stop_order_id,
                "entry_timestamp_ms": ss.entry_timestamp_ms,
            }

        try:
            # v2.3.4 (fix L2): write atómico via tmp + os.replace.
            # Previene JSON parcial si crash durante write (OOM, SIGKILL).
            # os.replace es atómico en POSIX; en Windows sobrescribe OK.
            tmp_path = f"{state_path}.tmp"
            with open(tmp_path, "w") as f:
                json.dump(data, f, indent=2)
            os.replace(tmp_path, state_path)
            logger.debug(f"[ENGINE] Estado guardado: {len(data['symbols'])} simbolos")
        except Exception as e:
            logger.error(f"[ENGINE] Error guardando estado: {e}")

    def _load_state(self):
        """Restaura estado desde JSON. Ignora si >2h antiguo."""
        if not self.brain:
            return

        state_path = _project_root / self.config.state_file_path
        if not state_path.exists():
            logger.info("[ENGINE] Sin state file previo")
            return

        try:
            with open(state_path) as f:
                data = json.load(f)
        except Exception as e:
            logger.warning(f"[ENGINE] Error leyendo state file: {e}")
            return

        # Verificar antigüedad
        saved_at = data.get("saved_at", "")
        if saved_at:
            try:
                saved_time = datetime.fromisoformat(saved_at)
                age_hours = (datetime.now(timezone.utc) - saved_time).total_seconds() / 3600
                if age_hours > 2.0:
                    logger.warning(
                        f"[ENGINE] State file tiene {age_hours:.1f}h, ignorando "
                        f"(max 2h para recovery)"
                    )
                    return
            except ValueError:
                pass

        # Restaurar
        self.cycle_count = data.get("cycle_count", 0)
        self._peak_balance = data.get("peak_balance", 0.0)
        self._current_balance = data.get("current_balance", 0.0)
        self._dd_multiplier = data.get("dd_multiplier", 1.0)
        self._prev_dd_multiplier = self._dd_multiplier
        self._circuit_breaker_active = data.get("circuit_breaker_active", False)
        restored = 0

        for sym, ss_data in data.get("symbols", {}).items():
            state = self.brain.get_state(sym)
            state.current_cluster = ss_data.get("current_cluster", -1)
            probs = ss_data.get("cluster_probs")
            if probs is not None:
                import numpy as np
                state.cluster_probs = np.array(probs)
            state.active_config_id = ss_data.get("active_config_id", -1)
            state.active_preset = ss_data.get("active_preset", "")
            state.position = ss_data.get("position", 0)
            state.entry_price = ss_data.get("entry_price", 0.0)
            state.entry_bar_timestamp = ss_data.get("entry_bar_timestamp", 0)
            state.entry_timestamp_ms = ss_data.get("entry_timestamp_ms", 0)
            state.sl_level = ss_data.get("sl_level", 0.0)
            state.entry_filters_forming = ss_data.get("entry_filters_forming", 0)
            state.div_ctx_bull = ss_data.get("div_ctx_bull", False)
            state.div_ctx_bear = ss_data.get("div_ctx_bear", False)
            state.prev_div_bull_now = ss_data.get("prev_div_bull_now", False)
            state.prev_div_bear_now = ss_data.get("prev_div_bear_now", False)
            state.prev_zone_bull = ss_data.get("prev_zone_bull", False)
            state.prev_zone_bear = ss_data.get("prev_zone_bear", False)
            state.cooldown_until = ss_data.get("cooldown_until", 0)
            state.bars_since_entry = ss_data.get("bars_since_entry", 0)
            state.stop_order_id = ss_data.get("stop_order_id", "")
            restored += 1

        # Restaurar posiciones DRY_RUN simuladas
        if self.config.dry_run:
            dry_pos_data = data.get("dry_run_positions", {})
            if dry_pos_data:
                load_dry_run_positions(dry_pos_data)
                logger.info(
                    f"[ENGINE] {len(dry_pos_data)} posiciones DRY_RUN restauradas"
                )

        logger.info(f"[ENGINE] Estado restaurado: {restored} simbolos, ciclo #{self.cycle_count}")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _show_status():
    """Muestra estado actual sin ejecutar."""
    print("=" * 60)
    print("LIVE ENGINE -- Status")
    print("=" * 60)

    state_path = _project_root / "engine_state.json"
    if state_path.exists():
        with open(state_path) as f:
            data = json.load(f)
        print(f"\nState file: {state_path}")
        print(f"Guardado: {data.get('saved_at', 'N/A')}")
        print(f"Ciclos: {data.get('cycle_count', 0)}")
        syms = data.get("symbols", {})
        n_pos = sum(1 for s in syms.values() if s.get("position", 0) != 0)
        print(f"Simbolos con estado: {len(syms)}")
        print(f"Posiciones en brain state: {n_pos}")

        if n_pos > 0:
            print("\nPosiciones:")
            for sym, ss in syms.items():
                pos = ss.get("position", 0)
                if pos != 0:
                    side = "LONG" if pos == 1 else "SHORT"
                    print(f"  {sym}: {side} @ {ss.get('entry_price', 0):.2f} "
                          f"SL={ss.get('sl_level', 0):.2f}")
    else:
        print("\nSin state file previo")

    # Modelos disponibles
    models_dir = _project_root / "regime_models"
    configs_dir = _project_root / "regime_wf"
    n_gmm = len(list(models_dir.glob("*_regime.joblib"))) if models_dir.exists() else 0
    n_specs = len(list(configs_dir.glob("*_specialist_configs.json"))) if configs_dir.exists() else 0
    print(f"\nModelos GMM: {n_gmm}")
    print(f"Specialist configs: {n_specs}")
    print(f"Simbolos totales: {len(MASTER_SYMBOLS)}")


async def _run_once(config: EngineConfig):
    """Ejecuta un solo ciclo."""
    engine = LiveEngine(config)
    try:
        await engine.start()
        report = await engine.run_cycle()
        print(f"\n--- CycleReport ---")
        print(f"Ciclo: {report.cycle_number}")
        print(f"Duracion: {report.duration_ms:.0f}ms")
        print(f"Simbolos procesados: {report.symbols_processed}")
        print(f"Senales activas: {report.signals_summary}")
        print(f"Allocaciones: {report.allocations_summary}")
        er = report.execution_report
        print(f"Ordenes enviadas: {len(er.orders_sent)}")
        print(f"Posiciones cerradas: {len(er.positions_closed)}")
        print(f"Stops actualizados: {len(er.stops_updated)}")
        print(f"Errores: {len(er.errors)}")
        if report.errors:
            print(f"Errores de ciclo: {report.errors}")
    finally:
        await engine.stop()


async def _run_forever(config: EngineConfig):
    """Ejecuta el bucle principal."""
    engine = LiveEngine(config)

    # Manejo de señales de parada
    loop = asyncio.get_running_loop()

    def _shutdown():
        logger.info("[ENGINE] Shutdown signal recibida")
        engine.running = False

    try:
        loop.add_signal_handler(signal.SIGINT, _shutdown)
        loop.add_signal_handler(signal.SIGTERM, _shutdown)
    except NotImplementedError:
        # Windows no soporta add_signal_handler en asyncio
        pass

    await engine.run_forever()


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Live Trading Engine")
    parser.add_argument("--live", action="store_true",
                        help="Modo REAL con dinero (requiere confirmacion)")
    parser.add_argument("--once", action="store_true",
                        help="Ejecuta 1 solo ciclo y sale")
    parser.add_argument("--status", action="store_true",
                        help="Muestra estado actual sin ejecutar")
    parser.add_argument("--symbols", nargs="+", default=None,
                        help="Solo estos simbolos (ej: BTC/USDT ETH/USDT)")
    parser.add_argument("--config", default=None,
                        help="Path a engine_config.json")
    parser.add_argument("--confirm-live", action="store_true",
                        help="Skip interactive confirmation for systemd")
    args = parser.parse_args()

    # Logging
    log_handlers = [
        logging.StreamHandler(sys.stdout),
    ]
    # Rotar log a archivo
    try:
        from logging.handlers import RotatingFileHandler
        fh = RotatingFileHandler(
            _project_root / "engine.log",
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=5,
        )
        fh.setFormatter(logging.Formatter(
            "%(asctime)s %(name)s %(levelname)s %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        ))
        log_handlers.append(fh)
    except Exception:
        pass

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(name)s %(message)s",
        datefmt="%H:%M:%S",
        handlers=log_handlers,
    )

    # Status
    if args.status:
        _show_status()
        return

    # Config
    config = load_engine_config(args.config)
    config.dry_run = not args.live
    if args.symbols:
        config.symbols = args.symbols

    # Confirmacion para modo live
    if args.live and not args.confirm_live:
        print("=" * 60)
        print("  MODO REAL CON DINERO")
        print("  Las ordenes se ejecutaran en BingX con fondos reales.")
        print("=" * 60)
        confirm = input("Escriba 'CONFIRMO' para continuar: ")
        if confirm.strip() != "CONFIRMO":
            print("Cancelado.")
            return
        print()

    mode = "DRY_RUN" if config.dry_run else "LIVE"
    syms = config.symbols or MASTER_SYMBOLS
    print(f"Arrancando en modo {mode} con {len(syms)} simbolos")
    print(f"{'1 ciclo' if args.once else 'Bucle continuo'}")
    print()

    if args.once:
        asyncio.run(_run_once(config))
    else:
        # En Windows, capturar Ctrl+C manualmente
        try:
            asyncio.run(_run_forever(config))
        except KeyboardInterrupt:
            print("\nInterrumpido por usuario.")


if __name__ == "__main__":
    main()
