#!/usr/bin/env python3
"""
analyze_train_test.py — Investiga si las metricas de train/test del lab
predicen rendimiento forward.

Lee wf_full/dataset_labeled.parquet y genera analisis completo.

Uso:
    python analyze_train_test.py --input wf_full/dataset_labeled.parquet --output wf_full/train_test_analysis.txt
"""

import argparse
import gc
import os
import sys

import numpy as np
import pandas as pd
import pyarrow.parquet as pq


# ============================================
# COLUMNAS REQUERIDAS (solo las que usan las secciones)
# ============================================

REQUIRED_COLUMNS = [
    'symbol', 'anchor_idx', 'config_id',
    # train/test/full
    'pnl_tr', 'pnl_ann_tr', 'pf_tr', 'score_tr', 'wr_tr', 'maxdd_tr', 'trades_tr',
    'pnl_te', 'pnl_ann_te', 'pf_te', 'score_te', 'wr_te', 'maxdd_te', 'trades_te',
    'pnl_fu', 'pnl_ann_fu', 'pf_fu', 'score_fu', 'wr_fu', 'maxdd_fu', 'trades_fu',
    'cancels_tr', 'cancels_te', 'cancels_fu',
    # derived
    'robustness', 'combined_score', 'ratio_pnl_te_tr',
    # forward
    'fwd_pnl', 'fwd_pf', 'fwd_trades', 'fwd_maxdd', 'fwd_wr', 'fwd_alpha', 'fwd_label',
    'fwd_h1_pnl', 'fwd_h2_pnl', 'fwd_q1_pnl', 'fwd_q2_pnl', 'fwd_q3_pnl', 'fwd_q4_pnl',
    'fwd_h2_ratio',
    # slices
    'opt_pnl', 'opt_pf', 'opt_trades', 'opt_maxdd', 'opt_wr',
    'ext_pnl', 'ext_pf', 'ext_trades', 'ext_maxdd', 'ext_wr',
    'combined_7k_pf', 'combined_7k_dd', 'combined_7k_pnl', 'combined_7k_trades',
    'delta_pf_opt_7k', 'delta_dd_opt_7k',
    'pasa_7k', 'n_criterios', 'is_gem',
    # asset context
    'asset_return_ext', 'asset_volatility_ext', 'asset_maxdd_ext',
    'asset_return_fwd', 'asset_volatility_fwd', 'asset_maxdd_fwd',
    'asset_return_opt', 'asset_volatility_opt', 'asset_maxdd_opt',
    # regime
    'regime_opt', 'regime_fwd', 'regime_match', 'regime_pair', 'chaos_opt',
]


def _select_columns(path):
    """Intersect REQUIRED_COLUMNS with columns actually present in a parquet file."""
    schema_cols = pq.read_schema(path).names
    return [c for c in REQUIRED_COLUMNS if c in schema_cols]


def _optimize_dtypes(df):
    """Downcast float64→float32 and string→category to reduce RAM."""
    float_cols = df.select_dtypes(include=['float64']).columns
    if len(float_cols):
        df[float_cols] = df[float_cols].astype(np.float32)
    for col in ['symbol', 'regime_opt', 'regime_fwd', 'regime_pair', 'fwd_label']:
        if col in df.columns and df[col].dtype == 'object':
            df[col] = df[col].astype('category')
    return df


# ============================================
# HELPERS
# ============================================

def safe_corr(s1, s2, min_n=30):
    valid = pd.concat([s1, s2], axis=1).dropna()
    if len(valid) < min_n:
        return np.nan
    return valid.iloc[:, 0].corr(valid.iloc[:, 1])


def fmt(v, width=9):
    if np.isnan(v):
        return f"{'--':>{width}}"
    return f"{v:>+{width}.4f}"


def pct(v):
    if np.isnan(v):
        return "--"
    return f"{v:.1f}%"


# ============================================
# 1. CORRELACIONES TRAIN/TEST VS FORWARD
# ============================================

def section_correlations(df, L):
    L.append("=" * 90)
    L.append("1. CORRELACIONES TRAIN/TEST VS FORWARD")
    L.append("=" * 90)

    lab_features = [
        'pnl_tr', 'pnl_ann_tr', 'pf_tr', 'score_tr', 'wr_tr', 'maxdd_tr', 'trades_tr',
        'pnl_te', 'pnl_ann_te', 'pf_te', 'score_te', 'wr_te', 'maxdd_te', 'trades_te',
        'pnl_fu', 'pnl_ann_fu', 'pf_fu', 'score_fu', 'wr_fu', 'maxdd_fu', 'trades_fu',
        'robustness', 'combined_score',
        'opt_pnl', 'opt_pf', 'opt_maxdd', 'opt_wr', 'opt_trades',
        'ext_pnl', 'ext_pf', 'ext_maxdd', 'ext_wr',
        'combined_7k_pf', 'combined_7k_dd', 'combined_7k_pnl',
        'delta_pf_opt_7k', 'delta_dd_opt_7k',
        'n_criterios',
        'asset_return_ext', 'asset_volatility_ext',
    ]
    targets = ['fwd_pnl', 'fwd_alpha', 'fwd_q1_pnl']

    available_feats = [f for f in lab_features if f in df.columns]
    available_tgts = [t for t in targets if t in df.columns]

    if not available_feats or not available_tgts:
        L.append("  [SKIP] Faltan columnas de features o targets")
        return

    rows = []
    for feat in available_feats:
        r = {'feature': feat}
        for tgt in available_tgts:
            r[tgt] = safe_corr(df[feat], df[tgt])
        r['max_abs_r'] = max(abs(r.get(t, 0) or 0) for t in available_tgts)
        rows.append(r)

    rows.sort(key=lambda x: x['max_abs_r'], reverse=True)

    header = f"  {'Feature':<25s}"
    for t in available_tgts:
        header += f" | {t:>12s}"
    header += " | max|r|"
    L.append(header)
    L.append(f"  {'-'*25}" + "".join(f"-+-{'-'*12}" for _ in available_tgts) + "-+-------")

    for r in rows:
        line = f"  {r['feature']:<25s}"
        for t in available_tgts:
            v = r.get(t, np.nan)
            if v is None or np.isnan(v):
                line += f" | {'--':>12s}"
            else:
                star = " **" if abs(v) > 0.3 else " * " if abs(v) > 0.15 else "   "
                line += f" | {v:>+9.4f}{star}"
        line += f" | {r['max_abs_r']:.4f}"
        L.append(line)

    L.append("")
    L.append("  (* |r|>0.15, ** |r|>0.30)")


# ============================================
# 2. DISTRIBUCION BUENA VS MALA
# ============================================

def section_distribution(df, L):
    L.append("")
    L.append("=" * 90)
    L.append("2. DISTRIBUCION POR LABEL (BUENA / NEUTRA / MALA)")
    L.append("=" * 90)

    lab_metrics = [
        'pnl_tr', 'pnl_te', 'pf_tr', 'pf_te', 'score_tr', 'score_te',
        'wr_tr', 'wr_te', 'maxdd_tr', 'maxdd_te',
        'robustness', 'combined_score',
        'pnl_fu', 'pf_fu', 'score_fu',
        'opt_pnl', 'opt_pf', 'ext_pnl', 'ext_pf',
    ]
    available = [m for m in lab_metrics if m in df.columns]

    if not available:
        L.append("  [SKIP] Sin metricas train/test disponibles")
        return

    label_col = 'fwd_label' if 'fwd_label' in df.columns else None
    if not label_col:
        L.append("  [SKIP] Sin columna fwd_label")
        return

    labels = ['BUENA', 'NEUTRA', 'MALA']

    header = f"  {'Metrica':<22s}"
    for lab in labels:
        header += f" | {'mean':>8s} {'med':>8s}"
    header += " | diff B-M"
    L.append(header)
    L.append(f"  {'-'*22}" + "".join(f"-+-{'-'*17}" for _ in labels) + "-+---------")

    for metric in available:
        line = f"  {metric:<22s}"
        means = {}
        for lab in labels:
            subset = df[df[label_col] == lab][metric].dropna()
            m = subset.mean() if len(subset) > 0 else np.nan
            med = subset.median() if len(subset) > 0 else np.nan
            means[lab] = m
            line += f" | {fmt(m, 8)} {fmt(med, 8)}"

        diff = (means.get('BUENA', np.nan) or 0) - (means.get('MALA', np.nan) or 0)
        line += f" | {diff:>+8.3f}"
        L.append(line)


# ============================================
# 3. DEGRADACION TRAIN -> TEST -> FORWARD
# ============================================

def section_degradation(df, L):
    L.append("")
    L.append("=" * 90)
    L.append("3. DEGRADACION: CURVA DE VIDA DE UNA GEMA")
    L.append("=" * 90)

    # Phases: use pnl_ann for train/test (they're on different bar counts),
    # or pnl for comparable slices
    # Best approach: use raw PnL for comparable phases
    phases_lab = ['pnl_tr', 'pnl_te']
    phases_fwd = ['fwd_q1_pnl', 'fwd_q2_pnl', 'fwd_q3_pnl', 'fwd_q4_pnl']

    # Check which are available
    all_phases = phases_lab + phases_fwd
    available = [p for p in all_phases if p in df.columns]

    if len(available) < 3:
        # Fallback: use opt/ext/fwd
        all_phases = ['opt_pnl', 'ext_pnl', 'fwd_q1_pnl', 'fwd_q2_pnl', 'fwd_q3_pnl', 'fwd_q4_pnl']
        available = [p for p in all_phases if p in df.columns]
        if len(available) < 3:
            L.append("  [SKIP] Insuficientes columnas para degradacion")
            return
        L.append("  (Usando opt/ext como proxy de train/test)")
        L.append("")

    label_col = 'fwd_label'
    labels = ['BUENA', 'NEUTRA', 'MALA', 'ALL']

    # Header
    header = f"  {'Label':<10s}"
    for p in available:
        short = p.replace('fwd_', '').replace('_pnl', '').replace('pnl_', '')
        header += f" | {short:>8s}"
    header += " | trend"
    L.append(header)
    L.append(f"  {'-'*10}" + "".join(f"-+-{'-'*8}" for _ in available) + "-+--------")

    for label in labels:
        if label == 'ALL':
            subset = df
        else:
            subset = df[df[label_col] == label]

        if len(subset) == 0:
            continue

        line = f"  {label:<10s}"
        means = []
        for p in available:
            m = subset[p].dropna().mean()
            means.append(m)
            line += f" | {m:>+8.3f}"

        # Trend: compare first vs last available
        if len(means) >= 2 and not np.isnan(means[0]) and not np.isnan(means[-1]):
            delta = means[-1] - means[0]
            line += f" | {delta:>+7.2f}"
        else:
            line += f" | {'--':>7s}"
        L.append(line)

    # Annualized version if available
    phases_ann = ['pnl_ann_tr', 'pnl_ann_te']
    phases_ann_fwd = ['fwd_q1_pnl_ann', 'fwd_q2_pnl_ann', 'fwd_q3_pnl_ann', 'fwd_q4_pnl_ann']
    avail_ann = [p for p in phases_ann + phases_ann_fwd if p in df.columns]

    if len(avail_ann) >= 3:
        L.append("")
        L.append("  PnL anualizado:")
        header = f"  {'Label':<10s}"
        for p in avail_ann:
            short = p.replace('fwd_', '').replace('_pnl_ann', '').replace('pnl_ann_', '')
            header += f" | {short:>8s}"
        L.append(header)
        L.append(f"  {'-'*10}" + "".join(f"-+-{'-'*8}" for _ in avail_ann) + "")

        for label in labels:
            subset = df if label == 'ALL' else df[df[label_col] == label]
            if len(subset) == 0:
                continue
            line = f"  {label:<10s}"
            for p in avail_ann:
                m = subset[p].dropna().mean()
                line += f" | {m:>+8.2f}"
            L.append(line)


# ============================================
# 4. RATIO TEST/TRAIN COMO PREDICTOR
# ============================================

def section_ratios(df, L):
    L.append("")
    L.append("=" * 90)
    L.append("4. RATIO TEST/TRAIN COMO PREDICTOR")
    L.append("=" * 90)

    ratios = {}

    # PnL ratio
    if 'pnl_te' in df.columns and 'pnl_tr' in df.columns:
        mask = df['pnl_tr'].abs() > 0.1  # avoid division by near-zero
        ratios['ratio_pnl_te_tr'] = pd.Series(np.nan, index=df.index)
        ratios['ratio_pnl_te_tr'][mask] = df.loc[mask, 'pnl_te'] / df.loc[mask, 'pnl_tr']
    elif 'ext_pnl' in df.columns and 'opt_pnl' in df.columns:
        mask = df['opt_pnl'].abs() > 0.1
        ratios['ratio_ext_opt_pnl'] = pd.Series(np.nan, index=df.index)
        ratios['ratio_ext_opt_pnl'][mask] = df.loc[mask, 'ext_pnl'] / df.loc[mask, 'opt_pnl']

    # PF ratio
    if 'pf_te' in df.columns and 'pf_tr' in df.columns:
        mask = df['pf_tr'] > 0.1
        ratios['ratio_pf_te_tr'] = pd.Series(np.nan, index=df.index)
        ratios['ratio_pf_te_tr'][mask] = df.loc[mask, 'pf_te'] / df.loc[mask, 'pf_tr']
    elif 'ext_pf' in df.columns and 'opt_pf' in df.columns:
        mask = df['opt_pf'] > 0.1
        ratios['ratio_ext_opt_pf'] = pd.Series(np.nan, index=df.index)
        ratios['ratio_ext_opt_pf'][mask] = df.loc[mask, 'ext_pf'] / df.loc[mask, 'opt_pf']

    # Score ratio
    if 'score_te' in df.columns and 'score_tr' in df.columns:
        mask = df['score_tr'].abs() > 0.01
        ratios['ratio_score_te_tr'] = pd.Series(np.nan, index=df.index)
        ratios['ratio_score_te_tr'][mask] = df.loc[mask, 'score_te'] / df.loc[mask, 'score_tr']

    if not ratios:
        L.append("  [SKIP] Sin columnas train/test para calcular ratios")
        return

    targets = ['fwd_pnl', 'fwd_alpha', 'fwd_q1_pnl']
    avail_tgts = [t for t in targets if t in df.columns]

    L.append(f"\n  Correlaciones ratio vs forward:")
    for rname, rseries in ratios.items():
        # Clip extremes
        clipped = rseries.clip(-5, 5)
        for tgt in avail_tgts:
            r = safe_corr(clipped, df[tgt])
            star = "**" if abs(r or 0) > 0.15 else ""
            L.append(f"    {rname:<25s} vs {tgt:<15s}: r={fmt(r or 0)} {star}")

    # Bucket analysis: ratio near 1.0 vs far from 1.0
    L.append("")
    L.append("  Analisis por buckets de ratio (configs donde test ~ train vs test << train):")

    for rname, rseries in ratios.items():
        clipped = rseries.clip(-5, 5).dropna()
        if len(clipped) < 100:
            continue

        L.append(f"\n    {rname}:")
        buckets = [
            ("ratio < 0.3", clipped < 0.3),
            ("0.3 <= ratio < 0.7", (clipped >= 0.3) & (clipped < 0.7)),
            ("0.7 <= ratio < 1.3", (clipped >= 0.7) & (clipped < 1.3)),
            ("1.3 <= ratio < 2.0", (clipped >= 1.3) & (clipped < 2.0)),
            ("ratio >= 2.0", clipped >= 2.0),
        ]

        header = f"      {'Bucket':<25s} | {'N':>6s} | {'fwd_pnl':>9s} | {'%BUENA':>7s} | {'%MALA':>7s}"
        L.append(header)
        L.append(f"      {'-'*25}-+-{'-'*6}-+-{'-'*9}-+-{'-'*7}-+-{'-'*7}")

        for bname, bmask in buckets:
            idx = clipped[bmask].index
            sub = df.loc[idx]
            n = len(sub)
            if n < 5:
                continue
            avg_fwd = sub['fwd_pnl'].mean() if 'fwd_pnl' in sub else np.nan
            pct_b = (sub['fwd_label'] == 'BUENA').mean() * 100 if 'fwd_label' in sub else np.nan
            pct_m = (sub['fwd_label'] == 'MALA').mean() * 100 if 'fwd_label' in sub else np.nan
            L.append(f"      {bname:<25s} | {n:>6d} | {avg_fwd:>+9.3f} | {pct_b:>6.1f}% | {pct_m:>6.1f}%")


# ============================================
# 5. ROBUSTNESS SCORE VS FORWARD
# ============================================

def section_robustness(df, L):
    L.append("")
    L.append("=" * 90)
    L.append("5. ROBUSTNESS SCORE VS FORWARD")
    L.append("=" * 90)

    rob_col = 'robustness' if 'robustness' in df.columns else None
    if not rob_col:
        # Try to compute from available columns
        if 'pnl_ann_te' in df.columns and 'pnl_ann_tr' in df.columns:
            mask = df['pnl_ann_tr'].abs() > 0.01
            df['_robustness_calc'] = np.nan
            df.loc[mask, '_robustness_calc'] = (df.loc[mask, 'pnl_ann_te'] / df.loc[mask, 'pnl_ann_tr']).clip(upper=1.5)
            rob_col = '_robustness_calc'
            L.append("  (robustness calculado como min(pnl_ann_te/pnl_ann_tr, 1.5))")
        elif 'ext_pnl_ann' in df.columns and 'opt_pnl_ann' in df.columns:
            mask = df['opt_pnl_ann'].abs() > 0.01
            df['_robustness_calc'] = np.nan
            df.loc[mask, '_robustness_calc'] = (df.loc[mask, 'ext_pnl_ann'] / df.loc[mask, 'opt_pnl_ann']).clip(upper=1.5)
            rob_col = '_robustness_calc'
            L.append("  (robustness aproximado como min(ext_pnl_ann/opt_pnl_ann, 1.5))")
        else:
            L.append("  [SKIP] Sin columna robustness ni datos para calcularla")
            return

    targets = ['fwd_pnl', 'fwd_alpha', 'fwd_q1_pnl']
    avail_tgts = [t for t in targets if t in df.columns]

    L.append(f"\n  Correlacion robustness vs forward:")
    for tgt in avail_tgts:
        r = safe_corr(df[rob_col], df[tgt])
        L.append(f"    robustness vs {tgt:<15s}: r={fmt(r or 0)}")

    # Bucket analysis
    rob = df[rob_col].dropna()
    if len(rob) < 100:
        return

    L.append(f"\n  Analisis por buckets de robustness:")
    buckets = [
        ("rob < 0.3", rob < 0.3),
        ("0.3 <= rob < 0.6", (rob >= 0.3) & (rob < 0.6)),
        ("0.6 <= rob < 0.9", (rob >= 0.6) & (rob < 0.9)),
        ("0.9 <= rob < 1.2", (rob >= 0.9) & (rob < 1.2)),
        ("rob >= 1.2", rob >= 1.2),
    ]

    header = f"    {'Bucket':<20s} | {'N':>6s} | {'fwd_pnl':>9s} | {'fwd_alpha':>10s} | {'%BUENA':>7s} | {'%MALA':>7s}"
    L.append(header)
    L.append(f"    {'-'*20}-+-{'-'*6}-+-{'-'*9}-+-{'-'*10}-+-{'-'*7}-+-{'-'*7}")

    for bname, bmask in buckets:
        idx = rob[bmask].index
        sub = df.loc[idx]
        n = len(sub)
        if n < 5:
            continue
        avg_fwd = sub['fwd_pnl'].mean() if 'fwd_pnl' in sub.columns else np.nan
        avg_alpha = sub['fwd_alpha'].mean() if 'fwd_alpha' in sub.columns else np.nan
        pct_b = (sub['fwd_label'] == 'BUENA').mean() * 100 if 'fwd_label' in sub.columns else np.nan
        pct_m = (sub['fwd_label'] == 'MALA').mean() * 100 if 'fwd_label' in sub.columns else np.nan
        L.append(f"    {bname:<20s} | {n:>6d} | {avg_fwd:>+9.3f} | {avg_alpha:>+10.3f} | {pct_b:>6.1f}% | {pct_m:>6.1f}%")

    # Alternative metrics that might correlate better
    L.append(f"\n  Metricas alternativas vs fwd_pnl (buscando mejor predictor que robustness):")
    alt_metrics = [
        ('pf_te', 'pf_te'),
        ('score_te', 'score_te'),
        ('maxdd_te', 'maxdd_te'),
        ('delta_pf_opt_7k', 'delta_pf_opt_7k'),
        ('combined_7k_pf', 'combined_7k_pf'),
        ('ext_pf', 'ext_pf'),
        ('opt_pf', 'opt_pf'),
        ('ext_pnl', 'ext_pnl'),
        ('n_criterios', 'n_criterios'),
    ]
    results = []
    for name, col in alt_metrics:
        if col not in df.columns:
            continue
        r = safe_corr(df[col], df['fwd_pnl']) if 'fwd_pnl' in df.columns else np.nan
        results.append((name, r))

    results.sort(key=lambda x: abs(x[1] or 0), reverse=True)
    for name, r in results:
        star = "**" if abs(r or 0) > 0.15 else "*" if abs(r or 0) > 0.1 else ""
        L.append(f"    {name:<25s}: r={fmt(r or 0)} {star}")


# ============================================
# 6. COMBINED SCORE DECOMPOSITION
# ============================================

def section_scoring(df, L):
    L.append("")
    L.append("=" * 90)
    L.append("6. COMBINED SCORE DECOMPOSITION — BUSQUEDA DE PESOS OPTIMOS")
    L.append("=" * 90)

    score_cols = ['score_tr', 'score_te', 'score_fu']
    # Fallback to opt/ext
    if not all(c in df.columns for c in score_cols):
        if all(c in df.columns for c in ['opt_pnl_ann', 'ext_pnl_ann']):
            L.append("  (Usando opt/ext como proxy de score_tr/score_te)")
            score_cols = ['opt_pnl_ann', 'ext_pnl_ann']
        else:
            L.append("  [SKIP] Sin score_tr/score_te/score_fu")
            return

    target = 'fwd_pnl' if 'fwd_pnl' in df.columns else None
    if not target:
        return

    # Current weights
    L.append(f"\n  Pesos actuales: W_TRAIN=0.35, W_TEST=0.40, W_FULL=0.25")

    avail_scores = [c for c in score_cols if c in df.columns]

    if 'combined_score' in df.columns:
        r_current = safe_corr(df['combined_score'], df[target])
        L.append(f"  combined_score vs {target}: r={fmt(r_current or 0)}")

    # Grid search over weight combinations
    L.append(f"\n  Grid search de pesos (w1*{avail_scores[0]} + w2*{avail_scores[1]}"
             + (f" + w3*{avail_scores[2]}" if len(avail_scores) > 2 else "")
             + f") vs {target}:")

    best_r = -1
    best_weights = None
    results = []

    steps = np.arange(0, 1.05, 0.1)
    valid_mask = df[avail_scores + [target]].notna().all(axis=1)
    df_v = df[valid_mask]

    if len(df_v) < 100:
        L.append("  [SKIP] Insuficientes observaciones validas")
        return

    if len(avail_scores) == 3:
        for w1 in steps:
            for w2 in steps:
                w3 = 1.0 - w1 - w2
                if w3 < -0.01 or w3 > 1.01:
                    continue
                w3 = max(0, w3)
                combo = w1 * df_v[avail_scores[0]] + w2 * df_v[avail_scores[1]] + w3 * df_v[avail_scores[2]]
                r = combo.corr(df_v[target])
                if not np.isnan(r):
                    results.append((w1, w2, w3, r))
                    if abs(r) > best_r:
                        best_r = abs(r)
                        best_weights = (w1, w2, w3, r)
    else:
        for w1 in steps:
            w2 = 1.0 - w1
            combo = w1 * df_v[avail_scores[0]] + w2 * df_v[avail_scores[1]]
            r = combo.corr(df_v[target])
            if not np.isnan(r):
                results.append((w1, w2, 0, r))
                if abs(r) > best_r:
                    best_r = abs(r)
                    best_weights = (w1, w2, 0, r)

    results.sort(key=lambda x: abs(x[3]), reverse=True)

    L.append(f"\n  Top 15 combinaciones por |r|:")
    header = f"    {'w_train':>7s} {'w_test':>7s} {'w_full':>7s} | {'r':>9s}"
    L.append(header)
    L.append(f"    {'-'*7} {'-'*7} {'-'*7}-+-{'-'*9}")
    for w1, w2, w3, r in results[:15]:
        L.append(f"    {w1:>7.2f} {w2:>7.2f} {w3:>7.2f} | {r:>+9.4f}")

    if best_weights:
        L.append(f"\n  Mejor combinacion: w1={best_weights[0]:.2f} w2={best_weights[1]:.2f} w3={best_weights[2]:.2f} -> r={best_weights[3]:+.4f}")


# ============================================
# 7. ARBOL DE DECISION CON TODAS LAS FEATURES
# ============================================

def section_tree(df, L):
    L.append("")
    L.append("=" * 90)
    L.append("7. ARBOL DE DECISION CON TODAS LAS FEATURES")
    L.append("=" * 90)

    try:
        from sklearn.tree import DecisionTreeClassifier, export_text
        from sklearn.model_selection import cross_val_score
        from sklearn.preprocessing import LabelEncoder
    except ImportError:
        L.append("  [SKIP] sklearn no instalado (pip install scikit-learn)")
        return

    # All candidate features
    candidate_features = [
        # Lab train/test
        'pnl_tr', 'pnl_ann_tr', 'pf_tr', 'score_tr', 'wr_tr', 'maxdd_tr', 'trades_tr',
        'pnl_te', 'pnl_ann_te', 'pf_te', 'score_te', 'wr_te', 'maxdd_te', 'trades_te',
        'pnl_fu', 'pnl_ann_fu', 'pf_fu', 'score_fu', 'wr_fu', 'maxdd_fu', 'trades_fu',
        'robustness', 'combined_score',
        # Slices
        'opt_pnl', 'opt_pf', 'opt_trades', 'opt_maxdd', 'opt_wr', 'opt_pnl_ann',
        'ext_pnl', 'ext_pf', 'ext_trades', 'ext_maxdd', 'ext_wr',
        'combined_7k_pf', 'combined_7k_dd', 'combined_7k_pnl', 'combined_7k_trades',
        'delta_pf_opt_7k', 'delta_dd_opt_7k',
        # Asset context
        'asset_return_ext', 'asset_volatility_ext', 'asset_maxdd_ext',
        # Other
        'n_criterios', 'fwd_h2_ratio',
    ]

    feature_cols = [f for f in candidate_features if f in df.columns]
    L.append(f"  Features disponibles: {len(feature_cols)}")

    X = df[feature_cols].copy()
    y = df['fwd_label'].copy()

    mask = X.notna().all(axis=1) & y.notna()
    X = X[mask]
    y = y[mask]
    L.append(f"  Observaciones validas: {len(X)}")

    if len(X) < 200:
        L.append("  [SKIP] Insuficientes observaciones")
        return

    le = LabelEncoder()
    y_enc = le.fit_transform(y)

    # Depth 6 tree
    for depth in [5, 6, 7]:
        L.append(f"\n  --- max_depth={depth} ---")
        clf = DecisionTreeClassifier(
            max_depth=depth,
            min_samples_leaf=max(20, len(X) // 100),
            class_weight='balanced',
            random_state=42
        )
        clf.fit(X, y_enc)

        importances = pd.Series(clf.feature_importances_, index=feature_cols)
        importances = importances.sort_values(ascending=False)

        L.append(f"  Feature importances (top 20):")
        for feat, imp in importances.head(20).items():
            if imp > 0.001:
                # Categorize
                if feat.endswith(('_tr', '_ann_tr')):
                    cat = "[TRAIN]"
                elif feat.endswith(('_te', '_ann_te')):
                    cat = "[TEST] "
                elif feat.endswith(('_fu', '_ann_fu')):
                    cat = "[FULL] "
                elif feat.startswith('asset_'):
                    cat = "[ASSET]"
                elif feat.startswith(('opt_', 'ext_', 'combined')):
                    cat = "[SLICE]"
                else:
                    cat = "[OTHER]"
                L.append(f"    {cat} {feat:<25s}: {imp:.4f}")

        # Cross-validation
        n_folds = min(5, max(2, len(X) // 500))
        scores = cross_val_score(clf, X, y_enc, cv=n_folds, scoring='accuracy')
        baseline = max(np.bincount(y_enc)) / len(y_enc)
        L.append(f"\n  Accuracy ({n_folds}-fold CV): {scores.mean():.3f} +/- {scores.std():.3f}")
        L.append(f"  Baseline (mayoria): {baseline:.3f}")
        L.append(f"  Lift: {scores.mean() / baseline:.2f}x")

    # Print tree rules for depth=6
    L.append(f"\n  Reglas del arbol (depth=6, primeras 60 lineas):")
    clf6 = DecisionTreeClassifier(
        max_depth=6,
        min_samples_leaf=max(20, len(X) // 100),
        class_weight='balanced',
        random_state=42
    )
    clf6.fit(X, y_enc)
    rules = export_text(clf6, feature_names=feature_cols, class_names=list(le.classes_))
    for line in rules.split('\n')[:60]:
        L.append(f"    {line}")

    # Dominance analysis: lab vs context
    L.append(f"\n  Dominancia por categoria:")
    categories = {
        'TRAIN': [f for f in feature_cols if f.endswith(('_tr', '_ann_tr')) or f == 'cancels_tr'],
        'TEST': [f for f in feature_cols if f.endswith(('_te', '_ann_te')) or f == 'cancels_te'],
        'FULL': [f for f in feature_cols if f.endswith(('_fu', '_ann_fu')) or f == 'cancels_fu'],
        'ROBUSTNESS': [f for f in feature_cols if f in ('robustness', 'combined_score')],
        'SLICE': [f for f in feature_cols if f.startswith(('opt_', 'ext_', 'combined_7k', 'delta_'))],
        'ASSET': [f for f in feature_cols if f.startswith('asset_')],
        'OTHER': [f for f in feature_cols if f in ('n_criterios', 'fwd_h2_ratio')],
    }

    importances = pd.Series(clf6.feature_importances_, index=feature_cols)
    for cat, cols in categories.items():
        if not cols:
            continue
        total_imp = importances[cols].sum()
        L.append(f"    {cat:<12s}: {total_imp:.4f} ({total_imp*100:.1f}%) [{len(cols)} features]")


# ============================================
# 8. PROPUESTA DE NUEVO SCORING
# ============================================

def section_new_scoring(df, L):
    L.append("")
    L.append("=" * 90)
    L.append("8. PROPUESTA DE NUEVO SCORING Y SIMULACION")
    L.append("=" * 90)

    label_col = 'fwd_label'
    if label_col not in df.columns:
        L.append("  [SKIP] Sin fwd_label")
        return

    # Find the most predictive features from available data
    all_feats = [c for c in df.columns if df[c].dtype in ('float64', 'int64')
                 and not c.startswith('fwd_') and c not in ('anchor_idx', 'config_id', 'fwd_start', 'fwd_end')]

    # Compute correlation with fwd_alpha for each
    feat_corrs = []
    for feat in all_feats:
        if 'fwd_alpha' in df.columns:
            r = safe_corr(df[feat], df['fwd_alpha'])
            if r is not None and not np.isnan(r):
                feat_corrs.append((feat, r))

    feat_corrs.sort(key=lambda x: abs(x[1]), reverse=True)

    L.append(f"\n  Top 10 features mas correlacionadas con fwd_alpha:")
    for feat, r in feat_corrs[:10]:
        L.append(f"    {feat:<30s}: r={r:+.4f}")

    # Simulate filter strategies
    L.append(f"\n  Simulacion de filtros:")
    L.append(f"  {'Filtro':<55s} | {'N':>6s} | {'%BUENA':>7s} | {'%MALA':>7s} | {'avg_fwd':>9s} | {'avg_alpha':>10s}")
    L.append(f"  {'-'*55}-+-{'-'*6}-+-{'-'*7}-+-{'-'*7}-+-{'-'*9}-+-{'-'*10}")

    def eval_filter(name, mask):
        sub = df[mask]
        n = len(sub)
        if n < 10:
            return
        pct_b = (sub[label_col] == 'BUENA').mean() * 100
        pct_m = (sub[label_col] == 'MALA').mean() * 100
        avg_fwd = sub['fwd_pnl'].mean() if 'fwd_pnl' in sub.columns else np.nan
        avg_alpha = sub['fwd_alpha'].mean() if 'fwd_alpha' in sub.columns else np.nan
        L.append(f"  {name:<55s} | {n:>6d} | {pct_b:>6.1f}% | {pct_m:>6.1f}% | {avg_fwd:>+9.3f} | {avg_alpha:>+10.3f}")

    # Baseline: all
    eval_filter("ALL (baseline)", pd.Series(True, index=df.index))

    # Current filter
    if 'pasa_7k' in df.columns:
        eval_filter("pasa_7k (filtro actual)", df['pasa_7k'] == True)

    # Lab-based filters (if available)
    if 'pf_te' in df.columns:
        eval_filter("pf_te >= 1.5", df['pf_te'] >= 1.5)
        eval_filter("pf_te >= 2.0", df['pf_te'] >= 2.0)
        eval_filter("pf_te >= 2.5", df['pf_te'] >= 2.5)

    if 'score_te' in df.columns:
        med = df['score_te'].median()
        p75 = df['score_te'].quantile(0.75)
        eval_filter(f"score_te > median ({med:.2f})", df['score_te'] > med)
        eval_filter(f"score_te > p75 ({p75:.2f})", df['score_te'] > p75)

    if 'robustness' in df.columns:
        eval_filter("robustness >= 0.7", df['robustness'] >= 0.7)
        eval_filter("robustness >= 1.0", df['robustness'] >= 1.0)

    if 'combined_score' in df.columns:
        med = df['combined_score'].median()
        p75 = df['combined_score'].quantile(0.75)
        eval_filter(f"combined_score > median ({med:.2f})", df['combined_score'] > med)
        eval_filter(f"combined_score > p75 ({p75:.2f})", df['combined_score'] > p75)

    # Slice-based filters
    if 'ext_pf' in df.columns:
        eval_filter("ext_pf >= 1.5", df['ext_pf'] >= 1.5)
        eval_filter("ext_pf >= 2.0", df['ext_pf'] >= 2.0)

    if 'combined_7k_pf' in df.columns and 'combined_7k_dd' in df.columns:
        eval_filter("7k_pf>=2 AND 7k_dd<=10 (actual)", (df['combined_7k_pf'] >= 2.0) & (df['combined_7k_dd'] <= 10.0))
        eval_filter("7k_pf>=1.5 AND 7k_dd<=15 (relajado)", (df['combined_7k_pf'] >= 1.5) & (df['combined_7k_dd'] <= 15.0))
        eval_filter("7k_pf>=2.5 AND 7k_dd<=8 (estricto)", (df['combined_7k_pf'] >= 2.5) & (df['combined_7k_dd'] <= 8.0))

    # Combined filters
    if 'ext_pf' in df.columns and 'combined_7k_pf' in df.columns:
        eval_filter("ext_pf>=1.5 AND 7k_pf>=1.5",
                    (df['ext_pf'] >= 1.5) & (df['combined_7k_pf'] >= 1.5))

    if 'pf_te' in df.columns and 'combined_7k_pf' in df.columns:
        eval_filter("pf_te>=1.5 AND 7k_pf>=1.5",
                    (df['pf_te'] >= 1.5) & (df['combined_7k_pf'] >= 1.5))

    if 'robustness' in df.columns and 'pf_te' in df.columns:
        eval_filter("robustness>=0.7 AND pf_te>=1.5",
                    (df['robustness'] >= 0.7) & (df['pf_te'] >= 1.5))

    # Top features combined
    if len(feat_corrs) >= 2:
        f1, r1 = feat_corrs[0]
        f2, r2 = feat_corrs[1]
        if f1 in df.columns and f2 in df.columns:
            med1 = df[f1].median()
            med2 = df[f2].median()
            if r1 > 0:
                m1 = df[f1] >= med1
            else:
                m1 = df[f1] <= med1
            if r2 > 0:
                m2 = df[f2] >= med2
            else:
                m2 = df[f2] <= med2
            eval_filter(f"top2_corr: {f1} {'>' if r1>0 else '<'} med AND {f2} {'>' if r2>0 else '<'} med", m1 & m2)

    # Scoring formula proposal
    L.append(f"\n  Propuesta de scoring basada en hallazgos:")
    L.append(f"  Se seleccionan los filtros con mayor %BUENA y menor %MALA de la tabla anterior.")
    L.append(f"  Un buen filtro maximiza %BUENA (>20%) mientras mantiene N suficiente (>1000).")


# ============================================
# 9. CORRELACIONES POR REGIMEN DE MERCADO
# ============================================

REGIME_FEATURES = [
    'pnl_tr', 'pnl_ann_tr', 'score_tr', 'pf_tr', 'wr_tr', 'maxdd_tr', 'trades_tr',
    'pnl_te', 'pnl_ann_te', 'score_te', 'pf_te', 'wr_te', 'maxdd_te', 'trades_te',
    'pnl_fu', 'pnl_ann_fu', 'score_fu', 'pf_fu', 'wr_fu', 'maxdd_fu', 'trades_fu',
    'robustness', 'combined_score', 'ratio_pnl_te_tr',
]


def section_regime_correlations(df, L):
    L.append("")
    L.append("=" * 90)
    L.append("9. CORRELACIONES POR REGIMEN DE MERCADO")
    L.append("=" * 90)

    required = ['regime_opt', 'regime_fwd', 'regime_pair', 'chaos_opt']
    missing = [c for c in required if c not in df.columns]
    if missing:
        L.append(f"  Columnas de regimen no disponibles (dataset antiguo): {missing}")
        L.append(f"  Regenerar checkpoints con walk_forward_experiment.py para obtener columnas de regimen.")
        return

    avail_feats = [f for f in REGIME_FEATURES if f in df.columns]
    if 'fwd_pnl' not in df.columns or not avail_feats:
        L.append("  [SKIP] Sin fwd_pnl o features disponibles")
        return

    # --- 9a. Distribution matrix ---
    L.append(f"\n  9a. DISTRIBUCION REGIMEN OPT x FWD:")
    regimes = ['BULL', 'NEUTRAL', 'BEAR']
    cw = 16  # cell width
    header = f"    {'opt\\fwd':<10s}"
    for r in regimes:
        header += f" | {r:>{cw}s}"
    header += f" | {'TOTAL':>{cw}s}"
    L.append(header)
    L.append(f"    {'-'*10}" + "".join(f"-+-{'-'*cw}" for _ in regimes) + f"-+-{'-'*cw}")

    total_n = len(df)
    for r_opt in regimes:
        line = f"    {r_opt:<10s}"
        row_total = 0
        for r_fwd in regimes:
            n = int(((df['regime_opt'] == r_opt) & (df['regime_fwd'] == r_fwd)).sum())
            row_total += n
            pct_val = n / total_n * 100 if total_n > 0 else 0
            cell = f"{n:>8,d} ({pct_val:>4.1f}%)"
            line += f" | {cell:>{cw}s}"
        pct_row = row_total / total_n * 100 if total_n > 0 else 0
        cell = f"{row_total:>8,d} ({pct_row:>4.1f}%)"
        line += f" | {cell:>{cw}s}"
        L.append(line)

    # --- 9b. Correlations per regime_pair ---
    L.append(f"\n  9b. CORRELACIONES POR REGIME PAIR (features vs fwd_pnl, N >= 1000):")
    pairs = sorted(df['regime_pair'].unique())
    valid_pairs = []
    pair_corrs = {}  # pair -> {feat -> r}

    for pair in pairs:
        sub = df[df['regime_pair'] == pair]
        if len(sub) < 1000:
            continue
        valid_pairs.append(pair)
        pair_corrs[pair] = {}
        for feat in avail_feats:
            r = safe_corr(sub[feat], sub['fwd_pnl'])
            pair_corrs[pair][feat] = r if r is not None else np.nan

    if valid_pairs:
        L.append(f"    Pares con N >= 1000:")
        for pair in valid_pairs:
            n_pair = int((df['regime_pair'] == pair).sum())
            L.append(f"      {pair}: N={n_pair:,}")
        L.append("")
        # Determine column widths
        pw = max(10, max(len(p) for p in valid_pairs))
        header = f"    {'Feature':<25s}"
        for p in valid_pairs:
            header += f" | {p:>{pw}s}"
        header += " | CONSIST"
        L.append(header)
        L.append(f"    {'-'*25}" + "".join(f"-+-{'-'*pw}" for _ in valid_pairs) + "-+---------")

        for feat in avail_feats:
            line = f"    {feat:<25s}"
            signs = set()
            any_notable = False
            for p in valid_pairs:
                r = pair_corrs[p].get(feat, np.nan)
                if np.isnan(r):
                    line += f" | {'--':>{pw}s}"
                else:
                    star = "**" if abs(r) > 0.30 else " *" if abs(r) > 0.15 else "  "
                    line += f" | {r:>+{pw-2}.4f}{star}"
                    if abs(r) > 0.01:
                        any_notable = True
                        signs.add('+' if r > 0 else '-')
            if len(signs) == 1:
                line += " | CONSIST"
            elif len(signs) == 2:
                line += " | CONTRAD"
            else:
                line += " |        "
            L.append(line)
    else:
        L.append("    (ninguna regime_pair con N >= 1000)")

    # --- 9c. Clean vs chaotic ---
    L.append(f"\n  9c. VENTANAS LIMPIAS vs CAOTICAS:")
    chaos = df['chaos_opt'].dropna()
    if len(chaos) < 100:
        L.append("    [SKIP] Insuficientes valores de chaos_opt")
    else:
        p75 = chaos.quantile(0.75)
        clean_mask = df['chaos_opt'] <= p75
        chaotic_mask = df['chaos_opt'] > p75
        n_clean = int(clean_mask.sum())
        n_chaotic = int(chaotic_mask.sum())
        L.append(f"    Umbral chaos_opt p75 = {p75:.4f}")
        L.append(f"    LIMPIA:  N={n_clean:,}  |  CAOTICA: N={n_chaotic:,}")

        header = f"    {'Feature':<25s} | {'r LIMPIA':>10s} | {'r CAOTICA':>10s} | {'diff':>8s}"
        L.append(header)
        L.append(f"    {'-'*25}-+-{'-'*10}-+-{'-'*10}-+-{'-'*8}")

        for feat in avail_feats:
            r_clean = safe_corr(df.loc[clean_mask, feat], df.loc[clean_mask, 'fwd_pnl'], min_n=100)
            r_chaotic = safe_corr(df.loc[chaotic_mask, feat], df.loc[chaotic_mask, 'fwd_pnl'], min_n=100)
            rc = r_clean if r_clean is not None else np.nan
            rch = r_chaotic if r_chaotic is not None else np.nan
            diff = (rc - rch) if not (np.isnan(rc) or np.isnan(rch)) else np.nan
            L.append(f"    {feat:<25s} | {fmt(rc, 10)} | {fmt(rch, 10)} | {fmt(diff, 8)}")

    # --- 9d. Match vs mismatch ---
    L.append(f"\n  9d. MATCH vs MISMATCH (regimen opt == regimen fwd):")
    if 'regime_match' in df.columns:
        match_mask = df['regime_match'] == True
        mismatch_mask = df['regime_match'] == False
        n_match = int(match_mask.sum())
        n_mismatch = int(mismatch_mask.sum())
        L.append(f"    MATCH: N={n_match:,}  |  MISMATCH: N={n_mismatch:,}")

        header = f"    {'Feature':<25s} | {'r MATCH':>10s} | {'r MISMATCH':>10s} | {'diff':>8s}"
        L.append(header)
        L.append(f"    {'-'*25}-+-{'-'*10}-+-{'-'*10}-+-{'-'*8}")

        for feat in avail_feats:
            r_match = safe_corr(df.loc[match_mask, feat], df.loc[match_mask, 'fwd_pnl'], min_n=100)
            r_mis = safe_corr(df.loc[mismatch_mask, feat], df.loc[mismatch_mask, 'fwd_pnl'], min_n=100)
            rm = r_match if r_match is not None else np.nan
            rmm = r_mis if r_mis is not None else np.nan
            diff = (rm - rmm) if not (np.isnan(rm) or np.isnan(rmm)) else np.nan
            L.append(f"    {feat:<25s} | {fmt(rm, 10)} | {fmt(rmm, 10)} | {fmt(diff, 8)}")


# ============================================
# 10. BUCKETS POR REGIMEN
# ============================================

def section_buckets_by_regime(df, L):
    L.append("")
    L.append("=" * 90)
    L.append("10. DISTRIBUCION FWD_PNL POR BUCKETS — ESTRATIFICADO POR REGIMEN")
    L.append("=" * 90)

    bucket_feats = ['pnl_tr', 'score_tr', 'trades_fu', 'wr_tr']
    avail = [f for f in bucket_feats if f in df.columns]
    if not avail or 'fwd_pnl' not in df.columns:
        L.append("  [SKIP] Sin features o fwd_pnl")
        return

    has_regime = 'regime_pair' in df.columns

    if has_regime:
        pairs = sorted(df['regime_pair'].unique())
        valid_pairs = [p for p in pairs if (df['regime_pair'] == p).sum() >= 1000]
    else:
        valid_pairs = []
        L.append("  (Sin columna regime_pair — analisis global sin estratificar)")

    groups = [('GLOBAL', df)]
    for p in valid_pairs:
        groups.append((p, df[df['regime_pair'] == p]))

    for feat in avail:
        L.append(f"\n  Feature: {feat}")
        for group_name, sub in groups:
            f_vals = sub[feat].values
            t_vals = sub['fwd_pnl'].values
            valid_mask = ~(np.isnan(f_vals) | np.isnan(t_vals))
            n_valid = int(valid_mask.sum())
            if n_valid < 50:
                continue

            try:
                chunk = pd.DataFrame({
                    'feat': f_vals[valid_mask],
                    'fwd_pnl': t_vals[valid_mask]
                })
                chunk['bucket'] = pd.qcut(chunk['feat'], q=5, duplicates='drop')
                bstats = chunk.groupby('bucket', observed=True)['fwd_pnl'].agg(['mean', 'count'])
                bstats['pct_pos'] = chunk.groupby('bucket', observed=True)['fwd_pnl'].apply(
                    lambda x: (x > 0).mean() * 100)
            except Exception:
                continue

            L.append(f"    {group_name} (N={n_valid:,}):")
            L.append(f"      {'Bucket':<30s} | {'Mean':>9s} | {'N':>8s} | {'%Pos':>6s}")
            L.append(f"      {'-'*30}-+-{'-'*9}-+-{'-'*8}-+-{'-'*6}")
            for bucket_label, row in bstats.iterrows():
                L.append(f"      {str(bucket_label):<30s} | {row['mean']:>+9.3f} | {int(row['count']):>8d} | {row['pct_pos']:>5.1f}%")


# ============================================
# 11. ARBOLES DE DECISION PER-SYMBOL
# ============================================

def section_trees_per_symbol(df, L):
    L.append("")
    L.append("=" * 90)
    L.append("11. ARBOLES DE DECISION PER-SYMBOL (fwd_pnl > 0)")
    L.append("=" * 90)

    try:
        from sklearn.tree import DecisionTreeClassifier, export_text
        from sklearn.model_selection import cross_val_score
    except ImportError:
        L.append("  [SKIP] sklearn no instalado (pip install scikit-learn)")
        return

    if 'fwd_pnl' not in df.columns or 'symbol' not in df.columns:
        L.append("  [SKIP] Sin columna fwd_pnl o symbol")
        return

    import gc

    TREE_FEATURES = REGIME_FEATURES + [
        'opt_pnl', 'opt_pf', 'opt_trades', 'opt_maxdd', 'opt_wr',
        'ext_pnl', 'ext_pf', 'ext_trades', 'ext_maxdd', 'ext_wr',
        'combined_7k_pf', 'combined_7k_dd', 'combined_7k_pnl',
        'delta_pf_opt_7k', 'delta_dd_opt_7k',
        'asset_return_ext', 'asset_volatility_ext', 'asset_maxdd_ext',
        'asset_return_fwd', 'asset_volatility_fwd', 'asset_maxdd_fwd',
        'asset_return_opt', 'asset_volatility_opt', 'asset_maxdd_opt',
        'n_criterios',
    ]
    feat_cols = [f for f in TREE_FEATURES if f in df.columns]
    if not feat_cols:
        L.append("  [SKIP] Sin features disponibles")
        return

    has_regime = 'regime_pair' in df.columns

    symbols = sorted(df['symbol'].unique())
    all_importances = {}
    all_accuracies = {}
    biggest_symbol = None
    biggest_n = 0
    biggest_tree_rules = ""

    MAX_SAMPLE = 500_000

    for sym in symbols:
        sym_df = df[df['symbol'] == sym]
        n_sym_total = len(sym_df)
        if n_sym_total < 200:
            L.append(f"\n  {sym}: insuficientes filas ({n_sym_total}) — saltando")
            continue

        # Sample if too large
        if n_sym_total > MAX_SAMPLE:
            sym_df = sym_df.sample(n=MAX_SAMPLE, random_state=42)

        # Filter NaN fwd_pnl BEFORE converting to binary
        valid_fwd = sym_df['fwd_pnl'].notna()
        avail_feats = [f for f in feat_cols if f in sym_df.columns]
        X = sym_df.loc[valid_fwd, avail_feats].fillna(0)
        y = (sym_df.loc[valid_fwd, 'fwd_pnl'] > 0).astype(int)
        n_rows = len(X)

        if n_rows < 200:
            continue

        min_leaf = max(50, n_rows // 200)
        clf = DecisionTreeClassifier(
            max_depth=5,
            min_samples_leaf=min_leaf,
            class_weight='balanced',
            random_state=42
        )
        clf.fit(X, y)

        importances = pd.Series(clf.feature_importances_, index=avail_feats)
        all_importances[sym] = (n_rows, importances)

        scores = cross_val_score(clf, X, y, cv=3, scoring='accuracy')
        all_accuracies[sym] = (scores.mean(), scores.std(), n_rows)

        tree_rules = export_text(clf, feature_names=avail_feats,
                                 class_names=['fwd_neg', 'fwd_pos'])
        if n_rows > biggest_n:
            biggest_n = n_rows
            biggest_symbol = sym
            biggest_tree_rules = tree_rules

        # Per-symbol output
        L.append(f"\n  {sym} (N={n_rows:,}, sample={'SI' if n_sym_total > MAX_SAMPLE else 'NO'}):")
        L.append(f"    Accuracy (3-fold CV): {scores.mean():.3f} +/- {scores.std():.3f}")
        top_imp = importances.sort_values(ascending=False).head(10)
        L.append(f"    Top-10 feature importances:")
        for feat, imp in top_imp.items():
            if imp > 0.001:
                L.append(f"      {feat:<25s}: {imp:.4f}")

        # Tree rules (max 60 lines)
        L.append(f"    Reglas (max 60 lineas):")
        for line in tree_rules.split('\n')[:60]:
            L.append(f"      {line}")

        # --- Per-symbol regime tree (BUG 3: inside loop, not global) ---
        if has_regime:
            try:
                sym_valid = sym_df.loc[valid_fwd]
                regime_dummies = pd.get_dummies(sym_valid['regime_pair'], prefix='regime')
                extra_cols = list(regime_dummies.columns)
                X_reg = pd.concat([X.reset_index(drop=True), regime_dummies.reset_index(drop=True)], axis=1)
                y_reg = y.reset_index(drop=True)

                all_feat_names = avail_feats + extra_cols
                clf_reg = DecisionTreeClassifier(
                    max_depth=5, min_samples_leaf=min_leaf,
                    class_weight='balanced', random_state=42
                )
                clf_reg.fit(X_reg, y_reg)
                scores_reg = cross_val_score(clf_reg, X_reg, y_reg, cv=3, scoring='accuracy')

                acc_diff = scores_reg.mean() - scores.mean()
                L.append(f"    Con regimen: acc={scores_reg.mean():.3f} +/- {scores_reg.std():.3f}  (delta={acc_diff:+.3f})")

                imp_reg = pd.Series(clf_reg.feature_importances_, index=all_feat_names)
                imp_regime_total = imp_reg[extra_cols].sum()
                L.append(f"    Importancia regime cols: {imp_regime_total:.4f} ({imp_regime_total*100:.1f}%)")

                del X_reg, y_reg, regime_dummies
            except Exception as e:
                L.append(f"    Error arbol con regimen: {e}")

        del sym_df, X, y
        gc.collect()

    # Weighted-average feature importances
    if all_importances:
        total_n = sum(n for n, _ in all_importances.values())
        avg_imp = None
        for sym, (n_rows, imp) in all_importances.items():
            weighted = imp * (n_rows / total_n)
            if avg_imp is None:
                avg_imp = weighted.copy()
            else:
                avg_imp = avg_imp.add(weighted, fill_value=0.0)

        avg_imp = avg_imp.sort_values(ascending=False)
        L.append(f"\n  Feature importances promediadas (ponderadas por N, total={total_n:,}):")
        for feat, imp in avg_imp.head(15).items():
            if imp > 0.001:
                L.append(f"    {feat:<30s}: {imp:.4f}")

        # Accuracy per symbol
        L.append(f"\n  Accuracy por simbolo (3-fold CV):")
        for sym in sorted(all_accuracies, key=lambda s: all_accuracies[s][2], reverse=True):
            acc_mean, acc_std, n = all_accuracies[sym]
            L.append(f"    {sym:<20s}: acc={acc_mean:.3f} +/- {acc_std:.3f}  (N={n:,})")

        # Tree rules for biggest symbol
        if biggest_symbol and biggest_tree_rules:
            L.append(f"\n  Reglas del arbol mas grande — {biggest_symbol} (N={biggest_n:,}):")
            for line in biggest_tree_rules.split('\n')[:60]:
                L.append(f"    {line}")
    else:
        L.append(f"\n  No se pudo entrenar arbol para ningun simbolo.")


# ============================================
# MAIN
# ============================================

def main():
    parser = argparse.ArgumentParser(description='Analisis train/test vs forward')
    parser.add_argument('--input', type=str, required=True,
                        help='Path to .parquet file or directory with checkpoint_*_all_train_v*.parquet files')
    parser.add_argument('--output', type=str, default=None, help='Output path for report')
    args = parser.parse_args()

    if args.output is None:
        base = args.input if os.path.isdir(args.input) else os.path.dirname(args.input)
        args.output = os.path.join(base or '.', "train_test_analysis.txt")

    print(f"Cargando: {args.input}")

    if os.path.isdir(args.input):
        import glob as _glob
        pattern = os.path.join(args.input, "checkpoint_*_all_train_v*.parquet")
        cp_files = sorted(_glob.glob(pattern))
        if not cp_files:
            print(f"  ERROR: No se encontraron archivos checkpoint_*_all_train_v*.parquet en {args.input}")
            sys.exit(1)
        print(f"  Encontrados {len(cp_files)} checkpoints, concatenando...")
        dfs = []
        for cp in cp_files:
            try:
                use_cols = _select_columns(cp)
                part = pd.read_parquet(cp, columns=use_cols)
                part = _optimize_dtypes(part)
                print(f"    {os.path.basename(cp)}: {len(part):,} filas, {len(use_cols)} cols")
                dfs.append(part)
                del part
                gc.collect()
            except Exception as e:
                print(f"    WARNING: {os.path.basename(cp)}: {e}")
        if not dfs:
            print("  ERROR: No se pudo leer ningun checkpoint")
            sys.exit(1)
        df = pd.concat(dfs, ignore_index=True)
        del dfs
        gc.collect()
        print(f"  Total concatenado: {len(df):,} filas")
    else:
        use_cols = _select_columns(args.input)
        df = pd.read_parquet(args.input, columns=use_cols)
        df = _optimize_dtypes(df)

    sym_col = 'symbol' if 'symbol' in df.columns else None
    n_symbols = df[sym_col].nunique() if sym_col else 0
    print(f"  {len(df):,} filas, {len(df.columns)} columnas, {n_symbols} simbolos")

    mem_mb = df.memory_usage(deep=True).sum() / 1024**2
    print(f"  RAM del DataFrame: {mem_mb:,.0f} MB")

    # --- Generar fwd_label si no existe ---
    if 'fwd_label' not in df.columns and 'fwd_pnl' in df.columns:
        print("  Generando fwd_label (no presente en checkpoint)...")
        if 'asset_return_fwd' in df.columns:
            df['fwd_alpha'] = df['fwd_pnl'] - df['asset_return_fwd']
        else:
            df['fwd_alpha'] = df['fwd_pnl']

        alpha_good = 2.0
        alpha_bad = -2.0
        pf_good = 1.2
        pf_bad = 0.8

        df['fwd_label'] = 'NEUTRA'
        if 'fwd_pf' in df.columns:
            df.loc[(df['fwd_alpha'] > alpha_good) & (df['fwd_pf'] > pf_good), 'fwd_label'] = 'BUENA'
            df.loc[(df['fwd_alpha'] < alpha_bad) | (df['fwd_pf'] < pf_bad), 'fwd_label'] = 'MALA'
        else:
            df.loc[df['fwd_alpha'] > alpha_good, 'fwd_label'] = 'BUENA'
            df.loc[df['fwd_alpha'] < alpha_bad, 'fwd_label'] = 'MALA'

        for label in ['BUENA', 'NEUTRA', 'MALA']:
            n = (df['fwd_label'] == label).sum()
            print(f"    {label}: {n:,} ({100*n/len(df):.1f}%)")
        # Optimize newly created columns
        df = _optimize_dtypes(df)

    # Check for train/test columns
    has_lab = 'pnl_tr' in df.columns
    print(f"  Columnas train/test del lab: {'SI' if has_lab else 'NO (usando opt/ext como proxy)'}")

    L = []
    L.append("=" * 90)
    L.append("ANALISIS TRAIN/TEST VS FORWARD")
    L.append("=" * 90)
    L.append(f"Dataset: {args.input}")
    L.append(f"Observaciones: {len(df):,}")
    L.append(f"Simbolos: {n_symbols}")
    L.append(f"Columnas train/test lab: {'SI' if has_lab else 'NO'}")
    if 'fwd_label' in df.columns:
        L.append(f"Labels: {df['fwd_label'].value_counts().to_dict()}")
    L.append("")

    section_correlations(df, L); gc.collect()
    section_distribution(df, L); gc.collect()
    section_degradation(df, L); gc.collect()
    section_ratios(df, L); gc.collect()
    section_robustness(df, L); gc.collect()
    section_scoring(df, L); gc.collect()
    section_tree(df, L); gc.collect()
    section_new_scoring(df, L); gc.collect()
    section_regime_correlations(df, L); gc.collect()
    section_buckets_by_regime(df, L); gc.collect()
    section_trees_per_symbol(df, L); gc.collect()

    report = "\n".join(L)

    os.makedirs(os.path.dirname(args.output) or '.', exist_ok=True)
    with open(args.output, 'w', encoding='utf-8') as f:
        f.write(report)

    print(f"\nReporte guardado: {args.output}")
    print(report)


if __name__ == "__main__":
    main()
