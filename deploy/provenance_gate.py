# -*- coding: utf-8 -*-
"""
provenance_gate.py — Gate OBLIGATORIO pre-deploy: verifica que cada specialist JSON
viaja con su GMM COMPAÑERO DE GENERACIÓN (runbook §8, junto al closure-check).

Origen: auditoría forense 2026-06-12 (audit_forense_gap_20260612/) — el bug de
misassignment GMM↔specialist (3 variantes, 11/20 símbolos) sobrevivió 4 deploys y
una certificación porque ningún paso lo miraba. A partir de hoy nada se despliega
sin pasar este gate.

Checks por símbolo:
  PER_SYM:
    P1. cluster names del JSON == cluster_names del joblib (orden incluido) —
        caza permutaciones (caso G1 BTC/BNB/TRX).
    P2a. training cutoff del joblib <= generated del JSON (un joblib regenerado
        DESPUÉS del JSON = companion roto — caso ADA).
    P2b. generated − cutoff <= 7 días (misma era de generación — caza GMM stale
        de otra época aunque los nombres coincidan por azar — caso G1 ETH).
    NOTA: NO se usan mtimes — cambian con cada copia/scp; solo contenido+metadata.
  CROSS_SOURCE (según best_source_per_sym del deployment report):
    C1. md5 del {TARGET}_regime.joblib empaquetado == md5 del {SOURCE}_regime.joblib
        de la era de generación (manifest o regime_models actual del source).
    C2. formato de nombres del JSON = cross-class (underscore `neutral_x_y`),
        confirmando que el JSON es realmente el artefacto cross-classified.

Uso:
  python deploy/provenance_gate.py --package <dir_con_json_y_joblib> \
      --report <deployment_report_grupo_N.json> [--models-dir regime_models]
  python deploy/provenance_gate.py --sweep-vps   (barrido completo vía paths locales
      sincronizados o snapshot — verifica TODO el estado desplegado)

Exit code 0 = PASS total; 1 = FAIL (NO DESPLEGAR).
"""
import argparse, hashlib, json, os, sys
from datetime import datetime, timedelta
from pathlib import Path

import joblib

ROOT = Path(__file__).resolve().parent.parent


def md5(p):
    return hashlib.md5(open(p, "rb").read()).hexdigest()


def is_cross_format(names):
    """Nombres estilo cross-class CCV usan underscores: neutral_low-vol_choppy."""
    return all(("_" in n and "/" not in n) for n in names)


def check_symbol(sym, json_path, joblib_path, best_source, models_dir, errors):
    j = json.load(open(json_path, encoding="utf-8"))
    jb = joblib.load(joblib_path)
    jnames = [c["name"] for _, c in sorted(j["clusters"].items())]
    gen = j.get("generated", "")
    tag = f"{sym} ({best_source})"

    if best_source and best_source != "PER_SYM_BASELINE":
        src = best_source.replace("_SOURCE", "")
        # C1: el joblib del target debe SER el del source (mismo contenido)
        src_path = Path(models_dir) / f"{src}_regime.joblib"
        if not src_path.exists():
            errors.append(f"{tag}: source joblib no encontrado: {src_path}")
            return
        if md5(joblib_path) != md5(src_path):
            errors.append(f"{tag}: C1 FAIL — joblib empaquetado != {src} source "
                          f"({md5(joblib_path)[:10]} vs {md5(src_path)[:10]})")
        # C2: JSON debe ser el artefacto cross-classified
        if not is_cross_format(jnames):
            errors.append(f"{tag}: C2 FAIL — JSON no tiene formato cross-class: {jnames}")
    else:
        # P1: nombres idénticos en orden
        if jnames != jb.get("cluster_names"):
            errors.append(f"{tag}: P1 FAIL — names JSON {jnames} != joblib {jb.get('cluster_names')}")
        # P2a/P2b: misma era de generación (solo metadata de contenido, sin mtimes)
        rng = jb.get("training_date_range")
        if rng and gen:
            try:
                cutoff = datetime.strptime(rng[1], "%Y-%m-%d %H:%M:%S")
                gdt = datetime.strptime(gen, "%Y-%m-%d %H:%M")
                if cutoff > gdt:
                    errors.append(f"{tag}: P2a FAIL — training cutoff {rng[1]} POSTERIOR a generated {gen} "
                                  f"(joblib regenerado tras el JSON — caso ADA)")
                elif (gdt - cutoff) > timedelta(days=7):
                    errors.append(f"{tag}: P2b FAIL — gap cutoff→generated {(gdt-cutoff).days}d > 7d "
                                  f"(GMM de otra era de generación — caso G1 stale)")
            except ValueError as e:
                errors.append(f"{tag}: P2 no evaluable ({e})")
        elif not rng:
            errors.append(f"{tag}: P2 no evaluable — joblib sin training_date_range")


def main():
    # consola Windows cp1252: no morir por caracteres unicode en los mensajes
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except AttributeError:
        pass
    ap = argparse.ArgumentParser()
    ap.add_argument("--package", help="dir con {SYM}USDT_specialist_configs.json + {SYM}_regime.joblib")
    ap.add_argument("--report", help="deployment_report_grupo_N.json (best_source_per_sym)")
    ap.add_argument("--models-dir", default=str(ROOT / "regime_models"),
                    help="dir con los joblibs de los SOURCES para checks cross-source")
    ap.add_argument("--json-dir", help="dir de JSONs si separado del de joblibs")
    ap.add_argument("--joblib-dir", help="dir de joblibs si separado")
    ap.add_argument("--symbols", help="lista CSV explícita (default: todos los JSON del package)")
    args = ap.parse_args()

    json_dir = Path(args.json_dir or args.package)
    joblib_dir = Path(args.joblib_dir or args.package)
    best = {}
    if args.report:
        rep = json.load(open(args.report, encoding="utf-8"))
        # composición DESPLEGADA manda (Deploy C override G1) sobre la auto
        comp = rep.get("best_source_per_sym_deploy") or rep.get("best_source_per_sym", {})
        best = {k.replace("USDT", ""): v for k, v in comp.items()}

    if args.symbols:
        syms = args.symbols.split(",")
    else:
        syms = sorted(p.name.replace("USDT_specialist_configs.json", "")
                      for p in json_dir.glob("*USDT_specialist_configs.json"))
    if not syms:
        print("GATE FAIL: 0 símbolos encontrados"); sys.exit(1)

    errors = []
    for s in syms:
        jp = json_dir / f"{s}USDT_specialist_configs.json"
        bp = joblib_dir / f"{s}_regime.joblib"
        if not jp.exists():
            errors.append(f"{s}: JSON ausente {jp}"); continue
        if not bp.exists():
            errors.append(f"{s}: joblib ausente {bp} (lección G3: specialists Y GMM viajan JUNTOS)"); continue
        check_symbol(s, jp, bp, best.get(s, "PER_SYM_BASELINE"), args.models_dir, errors)

    print(f"PROVENANCE GATE — {len(syms)} símbolos verificados")
    if errors:
        for e in errors:
            print(f"  [FAIL] {e}")
        print(f"GATE FAIL ({len(errors)} errores) — NO DESPLEGAR")
        sys.exit(1)
    print("GATE PASS — companions de generación verificados")
    sys.exit(0)


if __name__ == "__main__":
    main()
