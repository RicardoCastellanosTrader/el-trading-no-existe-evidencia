"""
clock_sync.py — Gate de sincronización horaria (arranque del bot).

Kraken Futures usa nonce = system-time-ms y tolera nonces fuera de orden solo
"brevemente" → un reloj con deriva da rechazos de timestamp. Este módulo verifica
que el reloj del sistema está sincronizado por NTP con offset bajo umbral ANTES
de la primera orden autenticada. Es un GATE DE ARRANQUE PERMANENTE: instalado-
pero-no-sincronizado da el mismo rechazo, así que se chequea en cada arranque,
no solo al provisionar.

Soporta chrony (preferido, deriva sub-segundo vía `chronyc tracking`) y
systemd-timesyncd (`timedatectl`). En entornos sin NTP tool (p.ej. Windows local
en DRY_RUN), retorna ok=False con motivo — el caller solo ENFORZA cuando hay
órdenes reales (no DRY_RUN).
"""
from __future__ import annotations

import logging
import subprocess

logger = logging.getLogger("live.clock_sync")

DEFAULT_MAX_OFFSET_MS = 250.0


def _run(cmd: list[str], timeout: float = 5.0) -> str | None:
    """Ejecuta un comando read-only y devuelve stdout, o None si falla/no existe."""
    try:
        out = subprocess.run(
            cmd, capture_output=True, text=True, timeout=timeout, check=False,
        )
    except (FileNotFoundError, OSError, subprocess.SubprocessError):
        return None
    if out.returncode != 0:
        return None
    return out.stdout or ""


def _parse_chrony_seconds(stdout: str, label: str) -> float | None:
    """Extrae la magnitud en segundos de una línea de `chronyc tracking`,
    p.ej. 'Last offset     : -0.000001234 seconds' o
    'System time     : 0.000012 seconds slow of NTP time'."""
    for line in stdout.splitlines():
        if line.strip().startswith(label):
            parts = line.split(":", 1)
            if len(parts) != 2:
                continue
            for tok in parts[1].split():
                try:
                    return abs(float(tok))
                except ValueError:
                    continue
    return None


def _check_chrony(max_offset_ms: float) -> tuple[bool, dict] | None:
    """chrony vía `chronyc -n tracking`. None si chrony no está disponible."""
    stdout = _run(["chronyc", "-n", "tracking"])
    if stdout is None:
        return None
    leap = ""
    for line in stdout.splitlines():
        if line.strip().startswith("Leap status"):
            leap = line.split(":", 1)[1].strip()
            break
    synced = leap.lower() == "normal"
    sys_off = _parse_chrony_seconds(stdout, "System time")
    last_off = _parse_chrony_seconds(stdout, "Last offset")
    offsets = [o for o in (sys_off, last_off) if o is not None]
    offset_ms = max(offsets) * 1000.0 if offsets else None
    detail = {
        "tool": "chrony", "leap_status": leap,
        "offset_ms": round(offset_ms, 3) if offset_ms is not None else None,
        "max_offset_ms": max_offset_ms,
    }
    if not synced:
        detail["reason"] = f"leap status no es Normal ({leap!r})"
        return False, detail
    if offset_ms is None:
        detail["reason"] = "no se pudo leer offset de chronyc"
        return False, detail
    if offset_ms > max_offset_ms:
        detail["reason"] = f"offset {offset_ms:.1f}ms > umbral {max_offset_ms}ms"
        return False, detail
    return True, detail


def _check_timesyncd(max_offset_ms: float) -> tuple[bool, dict] | None:
    """systemd-timesyncd vía `timedatectl`. None si no está disponible."""
    synced_out = _run(["timedatectl", "show", "-p", "NTPSynchronized", "--value"])
    if synced_out is None:
        return None
    synced = synced_out.strip().lower() in ("yes", "true", "1")
    detail = {"tool": "timesyncd", "ntp_synchronized": synced_out.strip(),
              "max_offset_ms": max_offset_ms}
    # offset (best-effort) desde timesync-status
    status = _run(["timedatectl", "timesync-status"]) or ""
    offset_ms = None
    for line in status.splitlines():
        if "Offset" in line:
            val = line.split(":", 1)[-1].strip()
            num = val.replace("ms", "").replace("us", "").replace("s", "").strip()
            try:
                raw = float(num)
                offset_ms = raw if "ms" in val else (raw / 1000.0 if "us" in val else raw * 1000.0)
                offset_ms = abs(offset_ms)
            except ValueError:
                offset_ms = None
            break
    detail["offset_ms"] = round(offset_ms, 3) if offset_ms is not None else None
    if not synced:
        detail["reason"] = "NTPSynchronized != yes"
        return False, detail
    if offset_ms is not None and offset_ms > max_offset_ms:
        detail["reason"] = f"offset {offset_ms:.1f}ms > umbral {max_offset_ms}ms"
        return False, detail
    return True, detail


def check_clock_sync(max_offset_ms: float = DEFAULT_MAX_OFFSET_MS) -> tuple[bool, dict]:
    """Verifica sincronización NTP del reloj del sistema.

    Returns:
        (ok, detail). ok=True solo si un NTP tool reporta sincronizado y el
        offset (cuando es legible) está bajo `max_offset_ms`. ok=False si no
        sincronizado, offset alto, o ningún NTP tool disponible.
    """
    for checker in (_check_chrony, _check_timesyncd):
        res = checker(max_offset_ms)
        if res is not None:
            return res
    return False, {"tool": None, "reason": "ningún NTP tool (chrony/timesyncd) disponible",
                   "max_offset_ms": max_offset_ms}


def assert_clock_synced_for_trading(
    dry_run: bool, max_offset_ms: float = DEFAULT_MAX_OFFSET_MS
) -> bool:
    """Gate de arranque: verifica sync ANTES de la primera orden. Si NO está
    sincronizado: en DRY_RUN/sim avisa y continúa (no hay órdenes reales); con
    órdenes reales (dry_run=False) loguea CRÍTICO y retorna False para que el
    caller ABORTE el arranque (no operar con reloj desincronizado → rechazos
    Kraken por nonce/timestamp). Retorna True si OK.
    """
    ok, detail = check_clock_sync(max_offset_ms)
    if ok:
        logger.info(f"[CLOCK_SYNC] OK — {detail}")
        return True
    if dry_run:
        logger.warning(
            f"[CLOCK_SYNC] NO sincronizado pero DRY_RUN — continúo (sin órdenes "
            f"reales): {detail}"
        )
        return True
    logger.critical(
        f"[CLOCK_SYNC] RELOJ NO SINCRONIZADO — abortando arranque antes de la "
        f"primera orden (Kraken rechaza por nonce/timestamp): {detail}"
    )
    return False
