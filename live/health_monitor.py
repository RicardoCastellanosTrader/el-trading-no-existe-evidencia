"""
health_monitor.py — Monitoriza salud del sistema comparando rendimiento real vs esperado.

Solo lectura + alertas. No modifica señales, sizing ni ejecución.
Lee trade_history.csv, calcula métricas reales por símbolo/cluster,
compara con pf_combined de specialist_configs.json y genera alertas
cuando hay degradación significativa.
"""

import argparse
import json
import logging
import os
import sys
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from pathlib import Path

import pandas as pd

logger = logging.getLogger(__name__)


# ──────────────────────────────────────────────────────────────────────
# Dataclasses
# ──────────────────────────────────────────────────────────────────────

@dataclass
class HealthConfig:
    # Umbrales de degradación
    pf_degradation_threshold: float = 0.70   # PF real < 70% del esperado -> WARNING
    pf_critical_threshold: float = 0.50      # PF real < 50% del esperado -> CRITICAL
    min_trades_to_evaluate: int = 15         # mínimo de trades antes de evaluar
    evaluation_window_days: int = 30         # ventana rolling para métricas reales

    # Triggers de reciclaje
    max_days_since_recycle: int = 90         # 3 meses máximo sin reciclar
    consecutive_loss_alert: int = 5          # N trades perdedores seguidos -> WARNING
    portfolio_dd_alert_pct: float = 10.0     # DD portfolio > 10% desde máximo -> CRITICAL

    # Paths
    trade_log_path: str = "trade_history.csv"
    specialist_configs_dir: str = "regime_wf"
    last_recycle_file: str = "last_recycle.txt"
    engine_state_path: str = "engine_state.json"


@dataclass
class SymbolHealth:
    symbol: str
    cluster: int
    trades_real: int
    pf_real: float
    pf_expected: float              # del JSON (pf_combined del top config)
    pf_ratio: float                 # real / expected
    win_rate_real: float
    avg_pnl_real: float
    consecutive_losses: int
    status: str                     # HEALTHY, WARNING, CRITICAL, INSUFFICIENT_DATA


@dataclass
class HealthReport:
    timestamp: str
    days_since_recycle: int
    portfolio_pnl_total: float
    portfolio_dd_from_peak: float
    symbols: list = field(default_factory=list)   # lista de SymbolHealth
    recycle_recommended: bool = False
    recycle_reasons: list = field(default_factory=list)
    alerts: list = field(default_factory=list)


# ──────────────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────────────

def _days_since_recycle(config: HealthConfig) -> int:
    """Lee last_recycle.txt y devuelve días transcurridos.

    v2.3.6 (fix H4): si no existe el archivo (o hay error de parsing),
    retorna 0 para NO disparar trigger calendario espurio. 9999 > 90
    hacia que recycle_recommended fuera siempre True sin archivo.
    Ausencia de archivo no es razon suficiente de reciclaje — los otros
    3 triggers (PF degradado, DD alto, flag manual) siguen activos.
    """
    path = Path(config.last_recycle_file)
    if not path.exists():
        return 0
    try:
        text = path.read_text().strip()
        last_date = datetime.fromisoformat(text).replace(tzinfo=timezone.utc)
        delta = datetime.now(timezone.utc) - last_date
        return delta.days
    except Exception as e:
        logger.warning(f"[HEALTH] No se pudo leer last_recycle.txt: {e}")
        return 0


def _load_expected_pf(config: HealthConfig) -> dict:
    """
    Carga pf_combined esperado por símbolo y cluster desde specialist_configs.json.
    Retorna dict: { ('BTC/USDT', 0): 3.845, ('BTC/USDT', 1): 2.1, ... }
    usando el top_config[0] de cada cluster.
    """
    expected = {}
    configs_dir = Path(config.specialist_configs_dir)
    if not configs_dir.exists():
        logger.warning(f"[HEALTH] Directorio {configs_dir} no encontrado")
        return expected

    for json_path in configs_dir.glob("*_specialist_configs.json"):
        try:
            with open(json_path, "r") as f:
                data = json.load(f)
            symbol = data.get("symbol", "")
            clusters = data.get("clusters", {})
            for cluster_id, cluster_data in clusters.items():
                top_configs = cluster_data.get("top_configs", [])
                if top_configs:
                    pf = top_configs[0].get("pf_combined", 0)
                    expected[(symbol, int(cluster_id))] = pf
        except Exception as e:
            logger.warning(f"[HEALTH] Error leyendo {json_path.name}: {e}")
    return expected


def _load_trades(config: HealthConfig) -> pd.DataFrame:
    """Carga trade_history.csv filtrado por ventana de evaluación.

    v2.3.5 (fix H3): parseo posicional con pad/trunc a 12 cols para
    tolerar CSVs con schema evolucionado (header pre-v2.3.2 con 10 cols,
    rows de v2.3.2+ con 11-12 cols). Mismo patrón que analyzer v2.4.1
    y audit v5.1.
    v2.3.5 (fix H2): excluye trades con flag='reconstructed_post_hoc'
    o 'reconstructed' por consistencia con analyzer v2.4.1 y audit v5.1
    (ambos excluyen reconstructed trades de sus agregados).
    """
    path = Path(config.trade_log_path)
    if not path.exists() or path.stat().st_size == 0:
        return pd.DataFrame()

    CSV_COLUMNS = ['timestamp', 'symbol', 'side', 'entry_price', 'exit_price',
                   'size_usdt', 'pnl_pct', 'pnl_usdt', 'funding_paid',
                   'reason_exit', 'flag', 'entry_timestamp_ms']
    N_COLS = len(CSV_COLUMNS)
    rows = []
    with open(path, 'r', encoding='utf-8', errors='replace') as f:
        _ = f.readline()  # header (variable: 10/11/12 cols según edad)
        for line in f:
            parts = line.rstrip('\n').split(',')
            while len(parts) < N_COLS:
                parts.append('')
            rows.append(parts[:N_COLS])
    if not rows:
        return pd.DataFrame()

    df = pd.DataFrame(rows, columns=CSV_COLUMNS)
    for col in ('entry_price', 'exit_price', 'size_usdt', 'pnl_pct',
                'pnl_usdt', 'funding_paid', 'entry_timestamp_ms'):
        df[col] = pd.to_numeric(df[col], errors='coerce')
    df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce')
    df = df.dropna(subset=['timestamp']).reset_index(drop=True)

    # H2: excluir reconstructed (consistente con analyzer/audit)
    EXCLUDE_FLAGS = {'reconstructed_post_hoc', 'reconstructed'}
    df['flag'] = df['flag'].fillna('').astype(str).str.strip().str.lower()
    df = df[~df['flag'].isin(EXCLUDE_FLAGS)].reset_index(drop=True)

    cutoff = datetime.now(timezone.utc) - timedelta(days=config.evaluation_window_days)
    # Path C anchor (2026-05-19): si last_recycle.txt es más reciente que la
    # ventana rolling 30d, usar esa fecha como corte. Bajo deployment
    # incremental rolling Path C (Grupo 1 deploy 2026-05-17), trades
    # pre-deploy usan specialists distintos a los actuales — compararlos
    # contra el pf_combined post-reciclaje produce falsos CRITICAL.
    # Anchor a last_recycle.txt elimina contaminación pre-deploy hasta
    # que la ventana rolling natural (30d) supere al deploy.
    recycle_path = Path(config.last_recycle_file)
    if recycle_path.exists():
        try:
            last_recycle_dt = datetime.fromisoformat(
                recycle_path.read_text().strip()
            )
            if last_recycle_dt.tzinfo is None:
                last_recycle_dt = last_recycle_dt.replace(tzinfo=timezone.utc)
            if last_recycle_dt > cutoff:
                cutoff = last_recycle_dt
        except Exception as e:
            logger.debug(f"[HEALTH] last_recycle anchor parse fail: {e}")
    if df['timestamp'].dt.tz is None:
        cutoff = cutoff.replace(tzinfo=None) if cutoff.tzinfo is not None else cutoff
    df = df[df['timestamp'] >= cutoff].copy()
    return df


def _compute_pf(pnl_series: pd.Series) -> float:
    """Profit Factor = sum(ganancias) / abs(sum(pérdidas)). Si no hay pérdidas, retorna 99."""
    gains = pnl_series[pnl_series > 0].sum()
    losses = abs(pnl_series[pnl_series < 0].sum())
    if losses == 0:
        return 99.0 if gains > 0 else 0.0
    return gains / losses


def _consecutive_losses(pnl_series: pd.Series) -> int:
    """Cuenta trades perdedores consecutivos desde el más reciente."""
    count = 0
    for val in reversed(pnl_series.values):
        if val < 0:
            count += 1
        else:
            break
    return count


def _compute_portfolio_dd(config: HealthConfig) -> float:
    """
    v2.3.6 (fix H1): DD del portfolio sobre capital total real.
    Lee peak_balance y current_balance de engine_state.json (mismas
    referencias que usa el DD breaker de live_engine). Retorna % >= 0.
    Fallback 0.0 en cualquier caso ambiguo: archivo no existe,
    peak<=0 (arranque fresco), current<=0 (bot recien restart antes
    de primer ciclo — current_balance aun no capturado), current>peak
    (nuevo maximo), o error de parsing. "Unknown" es mas seguro que
    reportar DD espuriamente alto.
    """
    try:
        state_path = Path(config.engine_state_path)
        if not state_path.exists():
            return 0.0
        with open(state_path, "r") as f:
            state = json.load(f)
        peak_balance = float(state.get("peak_balance", 0.0))
        current_balance = float(state.get("current_balance", 0.0))
        # Solo computar si ambos son positivos y current <= peak.
        # current_balance=0 significa "aun no capturado" (primer arranque),
        # tratarlo como DD=0 evita reportar 100% espurio.
        if peak_balance > 0 and current_balance > 0 and current_balance <= peak_balance:
            return (peak_balance - current_balance) / peak_balance * 100.0
        return 0.0
    except Exception as e:
        logger.warning(f"[HEALTH] Error leyendo engine_state para DD: {e}")
        return 0.0


def _get_active_cluster(symbol: str, config: HealthConfig) -> int:
    """
    Intenta obtener el cluster activo actual desde engine_state.json.
    Fallback: -1 (desconocido).
    """
    state_path = Path("engine_state.json")
    if not state_path.exists():
        return -1
    try:
        with open(state_path, "r") as f:
            state = json.load(f)
        sym_key = symbol.replace("/", "")  # BTC/USDT -> BTCUSDT
        # Probar ambos formatos de key
        for key in [symbol, sym_key]:
            if key in state.get("symbols", {}):
                return state["symbols"][key].get("current_cluster", -1)
    except Exception:
        pass
    return -1


# ──────────────────────────────────────────────────────────────────────
# 1. evaluate_health
# ──────────────────────────────────────────────────────────────────────

def evaluate_health(config: HealthConfig) -> HealthReport:
    """Evalúa la salud del sistema comparando rendimiento real vs esperado."""
    now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    days_recycle = _days_since_recycle(config)
    expected_pf = _load_expected_pf(config)
    df = _load_trades(config)

    report = HealthReport(
        timestamp=now_str,
        days_since_recycle=days_recycle,
        portfolio_pnl_total=0.0,
        portfolio_dd_from_peak=0.0,
    )

    # v2.3.6 (fix H1): DD sobre capital total real (peak_balance vs
    # current_balance), no sobre cumsum de PnL de trades cerrados.
    # Alinea con DD breaker del live_engine que usa la misma referencia
    # (peak_balance del engine_state.json). El cumsum previo daba valores
    # espurios (-121.7% observado en summary Telegram). Se computa antes
    # del check df.empty porque DD depende del balance persistente, no de
    # los trades en la ventana rolling.
    report.portfolio_dd_from_peak = _compute_portfolio_dd(config)

    # Scope filter (2026-05-19): bajo Path C incremental rolling sólo
    # evaluamos símbolos con specialist_configs cargados (Grupo N actual).
    # Trades históricos de símbolos archivados (pre-scope-reduction) no
    # tienen pf_expected comparable y generan ruido (false HEALTHY con
    # pf_exp=0 + ratio 0%). Filtrar aquí mantiene el reporte limpio.
    if not df.empty and expected_pf:
        loaded_symbols = {sym for (sym, _) in expected_pf.keys()}
        df = df[df['symbol'].isin(loaded_symbols)].copy()

    if df.empty:
        report.alerts.append("No hay trades en la ventana de evaluación")
        return report

    # --- Métricas de portfolio ---
    report.portfolio_pnl_total = df["pnl_usdt"].sum()

    # --- Métricas por símbolo ---
    for symbol, sym_df in df.groupby("symbol"):
        cluster = _get_active_cluster(symbol, config)
        n_trades = len(sym_df)
        pnl_series = sym_df["pnl_usdt"].reset_index(drop=True)

        if n_trades < config.min_trades_to_evaluate:
            report.symbols.append(SymbolHealth(
                symbol=symbol,
                cluster=cluster,
                trades_real=n_trades,
                pf_real=0.0,
                pf_expected=0.0,
                pf_ratio=0.0,
                win_rate_real=0.0,
                avg_pnl_real=0.0,
                consecutive_losses=0,
                status="INSUFFICIENT_DATA",
            ))
            continue

        pf_real = _compute_pf(pnl_series)
        win_rate = (pnl_series > 0).sum() / n_trades * 100
        avg_pnl = pnl_series.mean()
        consec_losses = _consecutive_losses(pnl_series)

        # Buscar PF esperado: primero por (symbol, cluster), si no cualquier cluster
        pf_exp = expected_pf.get((symbol, cluster), 0.0)
        if pf_exp == 0.0:
            # Fallback: promedio de todos los clusters del símbolo
            sym_pfs = [v for (s, c), v in expected_pf.items() if s == symbol]
            pf_exp = sum(sym_pfs) / len(sym_pfs) if sym_pfs else 0.0

        pf_ratio = pf_real / pf_exp if pf_exp > 0 else 0.0

        # Determinar status
        if pf_ratio < config.pf_critical_threshold and pf_exp > 0:
            status = "CRITICAL"
        elif pf_ratio < config.pf_degradation_threshold and pf_exp > 0:
            status = "WARNING"
        else:
            status = "HEALTHY"

        # Alertas por trades consecutivos perdedores
        if consec_losses >= config.consecutive_loss_alert:
            status = "WARNING" if status == "HEALTHY" else status
            report.alerts.append(
                f"{symbol}: {consec_losses} trades perdedores consecutivos"
            )

        sh = SymbolHealth(
            symbol=symbol,
            cluster=cluster,
            trades_real=n_trades,
            pf_real=round(pf_real, 2),
            pf_expected=round(pf_exp, 2),
            pf_ratio=round(pf_ratio, 2),
            win_rate_real=round(win_rate, 1),
            avg_pnl_real=round(avg_pnl, 2),
            consecutive_losses=consec_losses,
            status=status,
        )
        report.symbols.append(sh)

        if status == "CRITICAL":
            report.alerts.append(
                f"{symbol} C{cluster}: PF {pf_real:.1f} vs esperado {pf_exp:.1f} "
                f"(ratio {pf_ratio:.0%}) — CRITICAL"
            )
        elif status == "WARNING":
            report.alerts.append(
                f"{symbol} C{cluster}: PF {pf_real:.1f} vs esperado {pf_exp:.1f} "
                f"(ratio {pf_ratio:.0%}) — WARNING"
            )

    # --- Evaluar triggers de reciclaje ---
    report.recycle_recommended, report.recycle_reasons = check_recycle_triggers(
        report, config
    )

    return report


# ──────────────────────────────────────────────────────────────────────
# 2. check_recycle_triggers
# ──────────────────────────────────────────────────────────────────────

def check_recycle_triggers(report: HealthReport, config: HealthConfig) -> tuple:
    """
    Evalúa 4 triggers de reciclaje. Retorna (bool, list[str]).

    1. Calendario: días desde último reciclaje > 90
    2. Degradación PF: >=3 símbolos con pf_ratio < 0.70
    3. DD del portfolio: > 10% desde pico
    4. Evento manual: force_recycle.flag existe
    """
    reasons = []

    # 1. Calendario
    if report.days_since_recycle > config.max_days_since_recycle:
        reasons.append(
            f"Calendario: {report.days_since_recycle} días sin reciclar "
            f"(máx {config.max_days_since_recycle})"
        )

    # 2. Degradación PF (>=3 símbolos degradados)
    degraded = [
        s for s in report.symbols
        if s.status in ("WARNING", "CRITICAL")
        and s.pf_ratio < config.pf_degradation_threshold
        and s.trades_real >= config.min_trades_to_evaluate
    ]
    if len(degraded) >= 3:
        syms = ", ".join(s.symbol for s in degraded[:5])
        reasons.append(
            f"Degradación PF: {len(degraded)} símbolos degradados ({syms})"
        )

    # 3. DD del portfolio
    if report.portfolio_dd_from_peak > config.portfolio_dd_alert_pct:
        reasons.append(
            f"Drawdown portfolio: {report.portfolio_dd_from_peak:.1f}% "
            f"desde pico (umbral {config.portfolio_dd_alert_pct}%)"
        )

    # 4. Evento manual
    if Path("force_recycle.flag").exists():
        reasons.append("Reciclaje manual solicitado (force_recycle.flag)")

    return (len(reasons) > 0, reasons)


# ──────────────────────────────────────────────────────────────────────
# 3. generate_daily_health_summary
# ──────────────────────────────────────────────────────────────────────

def generate_daily_health_summary(config: HealthConfig) -> str:
    """Genera resumen de texto para la alerta diaria de Telegram."""
    report = evaluate_health(config)
    lines = []

    pnl_sign = "+" if report.portfolio_pnl_total >= 0 else ""
    lines.append(
        f"\U0001f4ca Health Report ({config.evaluation_window_days}d rolling):"
    )
    lines.append(
        f"  Portfolio: {pnl_sign}{report.portfolio_pnl_total:.1f} USDT "
        f"(DD: -{report.portfolio_dd_from_peak:.1f}% from peak)"
    )

    # v2.3.6 (fix H4): placeholder via existencia de archivo en vez de
    # sentinel 9999 (que disparaba trigger calendario espuriamente).
    if not Path(config.last_recycle_file).exists():
        days_str = f"??/{config.max_days_since_recycle} (no last_recycle.txt)"
    else:
        days_str = f"{report.days_since_recycle}/{config.max_days_since_recycle}"
    lines.append(f"  Days since recycle: {days_str}")

    # Contar por status
    evaluated = [s for s in report.symbols if s.status != "INSUFFICIENT_DATA"]
    pending = [s for s in report.symbols if s.status == "INSUFFICIENT_DATA"]
    total_active = len(evaluated) + len(pending)
    lines.append(f"\n  Symbols ({total_active} active):")

    # Ordenar: CRITICAL primero, luego WARNING, luego HEALTHY
    status_order = {"CRITICAL": 0, "WARNING": 1, "HEALTHY": 2, "INSUFFICIENT_DATA": 3}
    sorted_symbols = sorted(report.symbols, key=lambda s: status_order.get(s.status, 9))

    for sh in sorted_symbols:
        if sh.status == "INSUFFICIENT_DATA":
            lines.append(
                f"    \u23f3 {sh.symbol}: {sh.trades_real} trades "
                f"(need {config.min_trades_to_evaluate} to evaluate)"
            )
        elif sh.status == "HEALTHY":
            lines.append(
                f"    \u2705 {sh.symbol} C{sh.cluster}: PF {sh.pf_real} "
                f"(expected {sh.pf_expected}, ratio {sh.pf_ratio:.0%})"
            )
        elif sh.status == "WARNING":
            lines.append(
                f"    \u26a0\ufe0f {sh.symbol} C{sh.cluster}: PF {sh.pf_real} "
                f"(expected {sh.pf_expected}, ratio {sh.pf_ratio:.0%}) "
                f"\u2190 DEGRADED"
            )
        elif sh.status == "CRITICAL":
            lines.append(
                f"    \U0001f534 {sh.symbol} C{sh.cluster}: PF {sh.pf_real} "
                f"(expected {sh.pf_expected}, ratio {sh.pf_ratio:.0%}) "
                f"\u2190 CRITICAL"
            )

    # Recomendación de reciclaje
    if report.recycle_recommended:
        lines.append(f"\n  \U0001f504 RECYCLE RECOMENDADO:")
        for reason in report.recycle_reasons:
            lines.append(f"    - {reason}")
    else:
        lines.append(f"\n  No recycle needed.")

    return "\n".join(lines)


# ──────────────────────────────────────────────────────────────────────
# 4. log_recycle_event
# ──────────────────────────────────────────────────────────────────────

def log_recycle_event(config: HealthConfig | None = None):
    """Registra la fecha del reciclaje en last_recycle.txt."""
    if config is None:
        config = HealthConfig()
    now_str = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S+00:00")
    Path(config.last_recycle_file).write_text(now_str)
    logger.info(f"[HEALTH] Reciclaje registrado: {now_str}")


# ──────────────────────────────────────────────────────────────────────
# CLI
# ──────────────────────────────────────────────────────────────────────

def main():
    # Forzar UTF-8 en stdout para emojis en Windows
    if sys.stdout.encoding != "utf-8":
        sys.stdout.reconfigure(encoding="utf-8")

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
    )

    parser = argparse.ArgumentParser(
        description="Health Monitor — rendimiento real vs esperado"
    )
    parser.add_argument(
        "--summary", action="store_true",
        help="Resumen formato Telegram",
    )
    parser.add_argument(
        "--log-recycle", action="store_true",
        help="Registra que se hizo un reciclaje",
    )
    parser.add_argument(
        "--trade-log", type=str, default="trade_history.csv",
        help="Path al trade_history.csv",
    )
    parser.add_argument(
        "--configs-dir", type=str, default="regime_wf",
        help="Directorio de specialist_configs.json",
    )
    args = parser.parse_args()

    config = HealthConfig(
        trade_log_path=args.trade_log,
        specialist_configs_dir=args.configs_dir,
    )

    if args.log_recycle:
        log_recycle_event(config)
        print("Reciclaje registrado.")
        return

    if args.summary:
        print(generate_daily_health_summary(config))
        return

    # Default: evaluación completa
    report = evaluate_health(config)
    print(f"=== Health Report ({report.timestamp}) ===")
    print(f"Days since recycle: {report.days_since_recycle}")
    print(f"Portfolio PnL: {report.portfolio_pnl_total:+.2f} USDT")
    print(f"Portfolio DD from peak: {report.portfolio_dd_from_peak:.1f}%")
    print(f"\nSymbols ({len(report.symbols)}):")
    for sh in report.symbols:
        print(
            f"  [{sh.status:>17s}] {sh.symbol:<12s} C{sh.cluster} | "
            f"trades={sh.trades_real:>3d} PF={sh.pf_real:>5.2f} "
            f"(exp {sh.pf_expected:.2f}, ratio {sh.pf_ratio:.0%}) "
            f"WR={sh.win_rate_real:.0f}% consec_loss={sh.consecutive_losses}"
        )
    if report.alerts:
        print(f"\nAlerts ({len(report.alerts)}):")
        for alert in report.alerts:
            print(f"  - {alert}")
    if report.recycle_recommended:
        print(f"\nRECYCLE RECOMENDADO:")
        for r in report.recycle_reasons:
            print(f"  - {r}")
    else:
        print(f"\nNo recycle needed.")


if __name__ == "__main__":
    main()
