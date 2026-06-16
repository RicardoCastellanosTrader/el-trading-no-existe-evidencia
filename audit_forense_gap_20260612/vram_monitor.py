#!/usr/bin/env python
"""Monitor VRAM de alta frecuencia (1s, line-buffered + fsync por muestra).

Diseñado para sobrevivir a un TDR/reinicio duro: cada muestra se vacía a disco
físico (flush + os.fsync) para que la ÚLTIMA lectura antes del crash quede
persistida. El monitor del run anterior muestreaba cada 5 min y bufferizaba ->
perdió el instante del lanzamiento del kernel GPU (causa del 0x116).

Uso (atado al ciclo de vida del run vía driver: arranca como hijo, muere con trap EXIT):
    python vram_monitor.py --log <path> --interval 1
"""
import argparse
import os
import subprocess
import sys
import time

QUERY = "memory.used,memory.total,utilization.gpu,temperature.gpu"


def sample():
    try:
        out = subprocess.run(
            ["nvidia-smi", f"--query-gpu={QUERY}", "--format=csv,noheader,nounits"],
            capture_output=True, text=True, timeout=10,
        )
        return out.stdout.strip().replace("\n", " | ")
    except Exception as e:  # nvidia-smi colgado/ausente: registrar, no morir
        return f"QUERY_ERR {e!r}"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--log", required=True)
    ap.add_argument("--interval", type=float, default=1.0)
    args = ap.parse_args()

    f = open(args.log, "a", buffering=1)  # line-buffered
    f.write(f"# vram_monitor START pid={os.getpid()} interval={args.interval}s\n")
    f.flush(); os.fsync(f.fileno())
    while True:
        ts = time.strftime("%Y-%m-%dT%H:%M:%S")
        line = f"{ts} {sample()}\n"
        f.write(line)
        f.flush()
        os.fsync(f.fileno())  # forzar a disco físico: sobrevive a reboot duro
        time.sleep(args.interval)


if __name__ == "__main__":
    main()
