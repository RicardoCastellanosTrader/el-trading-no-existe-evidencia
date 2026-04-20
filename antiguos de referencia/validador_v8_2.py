# ============================================
# 🔍 VALIDADOR v8.0 - Auditoría Trade-by-Trade
# ============================================
# BASE: v7.1 con todas las correcciones
# v8.1: Multi-MA Zones + Histéresis ATR (Pine v10.0)
# Fidelidad absoluta al laboratorio v8.0 y al indicador Pine v9.0
#
# Ejecuta UNA config y exporta cada trade con detalle completo.
# Comisiones round-trip integradas.
# ============================================

import numpy as np
import pandas as pd
import ccxt
import time
import sys
import os
from datetime import datetime

# ============================================
# CONFIGURACIÓN — CAMBIAR AQUÍ
# ============================================
SYMBOL = "ETH/USDT"
CONFIG_ID = 14807813      # ETH v7.1 #1
TIMEFRAME = "1h"
TOTAL_CANDLES = 20000

# Parámetros fijos — Medias Móviles (v8.0: optimizadas por Lab LITE)
# ============================================
# PRESETS DE ZONAS v10.0 (Lab LITE v3)
# ============================================
# PRESETS DE ZONAS v11.0 (Lab LITE v5c — 48 symbols, 13.5M configs)
# ============================================
# Formato: lista de tuplas por símbolo
#   (fast_type, fast_len, fast_p1, fast_p2,
#    slow_type, slow_len, slow_p1, slow_p2,
#    trend_type, trend_len, trend_p1, trend_p2)
# Top 5 por score + agresivo (mejor PnL) si fuera del top 5
SYMBOL_ZONE_PRESETS = {
    "AAVE/USDT": [
        ("VIDYA",20,0.0,0.0, "VWMA",60,0.0,0.0, "VWMA",240,0.0,0.0),  # #1 VIDYA(20)/VWMA(60)/ft5:VWMA(240)
        ("VIDYA",16,0.0,0.0, "VWMA",54,0.0,0.0, "VWMA",216,0.0,0.0),  # #2 VIDYA(16)/VWMA(54)/ft5:VWMA(216)
        ("McGinley",12,0.0,0.0, "DEMA",72,0.0,0.0, "DEMA",288,0.0,0.0),  # #3 McGinley(12)/DEMA(72)/ft5:DEMA(288)
        ("VIDYA",20,0.0,0.0, "VWMA",54,0.0,0.0, "VWMA",216,0.0,0.0),  # #4 VIDYA(20)/VWMA(54)/ft5:VWMA(216)
        ("ALMA",22,0.5,4.0, "SSmoother",51,0.0,0.0, "SSmoother",204,0.0,0.0),  # #5 ALMA(22,0.5,4)/SSmoother(51)/ft5:SSmoother(204)
    ],
    "ADA/USDT": [
        ("McGinley",24,0.0,0.0, "KAMA",51,0.0,0.0, "KAMA",204,0.0,0.0),  # #1 McGinley(24)/KAMA(51)/ft5:KAMA(204)
        ("McGinley",22,0.0,0.0, "KAMA",51,0.0,0.0, "KAMA",204,0.0,0.0),  # #2 McGinley(22)/KAMA(51)/ft5:KAMA(204)
        ("VIDYA",12,0.0,0.0, "VWMA",69,0.0,0.0, "VWMA",276,0.0,0.0),  # #3 VIDYA(12)/VWMA(69)/ft5:VWMA(276)
        ("McGinley",22,0.0,0.0, "KAMA",49,0.0,0.0, "KAMA",196,0.0,0.0),  # #4 McGinley(22)/KAMA(49)/ft5:KAMA(196)
        ("McGinley",24,0.0,0.0, "KAMA",49,0.0,0.0, "KAMA",196,0.0,0.0),  # #5 McGinley(24)/KAMA(49)/ft5:KAMA(196)
    ],
    "ALGO/USDT": [
        ("VIDYA",24,0.0,0.0, "VWMA",57,0.0,0.0, "VWMA",228,0.0,0.0),  # #1 VIDYA(24)/VWMA(57)/ft5:VWMA(228)
        ("McGinley",24,0.0,0.0, "KAMA",51,0.0,0.0, "KAMA",204,0.0,0.0),  # #2 McGinley(24)/KAMA(51)/ft5:KAMA(204)
        ("VIDYA",24,0.0,0.0, "VWMA",54,0.0,0.0, "VWMA",216,0.0,0.0),  # #3 VIDYA(24)/VWMA(54)/ft5:VWMA(216)
        ("McGinley",16,0.0,0.0, "VWMA",30,0.0,0.0, "VWMA",120,0.0,0.0),  # #4 McGinley(16)/VWMA(30)/ft5:VWMA(120)
        ("VIDYA",22,0.0,0.0, "VWMA",51,0.0,0.0, "VWMA",204,0.0,0.0),  # #5 VIDYA(22)/VWMA(51)/ft5:VWMA(204)
    ],
    "APT/USDT": [
        ("Tenkan",24,0.0,0.0, "KAMA",72,0.0,0.0, "KAMA",288,0.0,0.0),  # #1 Tenkan(24)/KAMA(72)/ft5:KAMA(288)
        ("KAMA",24,0.0,0.0, "KAMA",72,0.0,0.0, "KAMA",288,0.0,0.0),  # #2 KAMA(24)/KAMA(72)/ft5:KAMA(288)
        ("Tenkan",22,0.0,0.0, "KAMA",72,0.0,0.0, "KAMA",288,0.0,0.0),  # #3 Tenkan(22)/KAMA(72)/ft5:KAMA(288)
        ("Tenkan",24,0.0,0.0, "KAMA",66,0.0,0.0, "KAMA",264,0.0,0.0),  # #4 Tenkan(24)/KAMA(66)/ft5:KAMA(264)
        ("Tenkan",22,0.0,0.0, "KAMA",66,0.0,0.0, "KAMA",264,0.0,0.0),  # #5 Tenkan(22)/KAMA(66)/ft5:KAMA(264)
    ],
    "ARB/USDT": [
        ("McGinley",24,0.0,0.0, "ALMA",33,0.5,4.0, "ALMA",132,0.5,4.0),  # #1 McGinley(24)/ALMA(33,0.5,4)/ft5:ALMA(132)
        ("McGinley",8,0.0,0.0, "TEMA",75,0.0,0.0, "TEMA",300,0.0,0.0),  # #2 McGinley(8)/TEMA(75)/ft5:TEMA(300)
        ("McGinley",8,0.0,0.0, "TEMA",75,0.0,0.0, "VIDYA",250,0.0,0.0),  # #3 McGinley(8)/TEMA(75)/VIDYA(250)
        ("McGinley",8,0.0,0.0, "TEMA",75,0.0,0.0, "VIDYA",240,0.0,0.0),  # #4 McGinley(8)/TEMA(75)/VIDYA(240)
        ("McGinley",8,0.0,0.0, "TEMA",75,0.0,0.0, "VIDYA",230,0.0,0.0),  # #5 McGinley(8)/TEMA(75)/VIDYA(230)
    ],
    "ATOM/USDT": [
        ("McGinley",20,0.0,0.0, "KAMA",36,0.0,0.0, "KAMA",144,0.0,0.0),  # #1 McGinley(20)/KAMA(36)/ft5:KAMA(144)
        ("KAMA",16,0.0,0.0, "SSmoother",63,0.0,0.0, "SSmoother",252,0.0,0.0),  # #2 KAMA(16)/SSmoother(63)/ft5:SSmoother(252)
        ("McGinley",20,0.0,0.0, "KAMA",36,0.0,0.0, "Tenkan",190,0.0,0.0),  # #3 McGinley(20)/KAMA(36)/Tenkan(190)
        ("McGinley",10,0.0,0.0, "ZLEMA",36,0.0,0.0, "ZLEMA",144,0.0,0.0),  # #4 McGinley(10)/ZLEMA(36)/ft5:ZLEMA(144)
        ("McGinley",20,0.0,0.0, "ALMA",36,0.85,6.0, "ALMA",144,0.85,6.0),  # #5 McGinley(20)/ALMA(36,0.85,6)/ft5:ALMA(144)
    ],
    "AVAX/USDT": [
        ("VIDYA",12,0.0,0.0, "T3",33,0.8,0.0, "T3",132,0.8,0.0),  # #1 VIDYA(12)/T3(33,v0.8)/ft5:T3(132)
        ("VIDYA",14,0.0,0.0, "ALMA",57,0.5,6.0, "ALMA",228,0.5,6.0),  # #2 VIDYA(14)/ALMA(57,0.5,6)/ft5:ALMA(228)
        ("KAMA",18,0.0,0.0, "DEMA",42,0.0,0.0, "DEMA",168,0.0,0.0),  # #3 KAMA(18)/DEMA(42)/ft5:DEMA(168)
        ("VIDYA",14,0.0,0.0, "T3",33,0.7,0.0, "T3",132,0.7,0.0),  # #4 VIDYA(14)/T3(33,v0.7)/ft5:T3(132)
        ("KAMA",14,0.0,0.0, "T3",36,0.8,0.0, "T3",144,0.8,0.0),  # #5 KAMA(14)/T3(36,v0.8)/ft5:T3(144)
    ],
    "BCH/USDT": [
        ("VIDYA",10,0.0,0.0, "DEMA",72,0.0,0.0, "DEMA",288,0.0,0.0),  # #1 VIDYA(10)/DEMA(72)/ft5:DEMA(288)
        ("VIDYA",10,0.0,0.0, "DEMA",75,0.0,0.0, "DEMA",300,0.0,0.0),  # #2 VIDYA(10)/DEMA(75)/ft5:DEMA(300)
        ("McGinley",24,0.0,0.0, "ZLEMA",51,0.0,0.0, "ZLEMA",204,0.0,0.0),  # #3 McGinley(24)/ZLEMA(51)/ft5:ZLEMA(204)
        ("VIDYA",22,0.0,0.0, "ZLEMA",48,0.0,0.0, "ZLEMA",192,0.0,0.0),  # #4 VIDYA(22)/ZLEMA(48)/ft5:ZLEMA(192)
        ("VIDYA",22,0.0,0.0, "ZLEMA",49,0.0,0.0, "ZLEMA",196,0.0,0.0),  # #5 VIDYA(22)/ZLEMA(49)/ft5:ZLEMA(196)
    ],
    "BNB/USDT": [
        ("KAMA",14,0.0,0.0, "T3",30,0.8,0.0, "T3",120,0.8,0.0),  # #1 KAMA(14)/T3(30,v0.8)/ft5:T3(120)
        ("KAMA",14,0.0,0.0, "ALMA",39,0.5,4.0, "ALMA",156,0.5,4.0),  # #2 KAMA(14)/ALMA(39,0.5,4)/ft5:ALMA(156)
        ("McGinley",14,0.0,0.0, "SMA",33,0.0,0.0, "SMA",132,0.0,0.0),  # #3 McGinley(14)/SMA(33)/ft5:SMA(132)
        ("KAMA",14,0.0,0.0, "ALMA",42,0.5,6.0, "ALMA",168,0.5,6.0),  # #4 KAMA(14)/ALMA(42,0.5,6)/ft5:ALMA(168)
        ("KAMA",16,0.0,0.0, "T3",30,0.8,0.0, "T3",120,0.8,0.0),  # #5 KAMA(16)/T3(30,v0.8)/ft5:T3(120)
    ],
    "BONK/USDT": [
        ("McGinley",24,0.0,0.0, "KAMA",39,0.0,0.0, "KAMA",156,0.0,0.0),  # #1 McGinley(24)/KAMA(39)/ft5:KAMA(156)
        ("VIDYA",24,0.0,0.0, "SMA",54,0.0,0.0, "SMA",216,0.0,0.0),  # #2 VIDYA(24)/SMA(54)/ft5:SMA(216)
        ("T3",22,0.8,0.0, "ALMA",69,0.85,4.0, "ALMA",276,0.85,4.0),  # #3 T3(22,v0.8)/ALMA(69,0.85,4)/ft5:ALMA(276)
        ("McGinley",24,0.0,0.0, "KAMA",42,0.0,0.0, "KAMA",168,0.0,0.0),  # #4 McGinley(24)/KAMA(42)/ft5:KAMA(168)
        ("T3",22,0.7,0.0, "ALMA",75,0.85,4.0, "ALMA",300,0.85,4.0),  # #5 T3(22,v0.7)/ALMA(75,0.85,4)/ft5:ALMA(300)
    ],
    "BTC/USDT": [
        ("McGinley",20,0.0,0.0, "EMA",42,0.0,0.0, "EMA",168,0.0,0.0),  # #1 McGinley(20)/EMA(42)/ft5:EMA(168)
        ("SMA",22,0.0,0.0, "EMA",39,0.0,0.0, "EMA",156,0.0,0.0),  # #2 SMA(22)/EMA(39)/ft5:EMA(156)
        ("T3",20,0.8,0.0, "SMA",33,0.0,0.0, "SMA",132,0.0,0.0),  # #3 T3(20,v0.8)/SMA(33)/ft5:SMA(132)
        ("T3",18,0.7,0.0, "ALMA",66,0.85,4.0, "ALMA",264,0.85,4.0),  # #4 T3(18,v0.7)/ALMA(66,0.85,4)/ft5:ALMA(264)
        ("T3",20,0.8,0.0, "SMA",36,0.0,0.0, "SMA",144,0.0,0.0),  # #5 T3(20,v0.8)/SMA(36)/ft5:SMA(144)
    ],
    "DOGE/USDT": [
        ("KAMA",14,0.0,0.0, "TEMA",63,0.0,0.0, "TEMA",252,0.0,0.0),  # #1 KAMA(14)/TEMA(63)/ft5:TEMA(252)
        ("KAMA",14,0.0,0.0, "HMA",49,0.0,0.0, "HMA",196,0.0,0.0),  # #2 KAMA(14)/HMA(49)/ft5:HMA(196)
        ("KAMA",12,0.0,0.0, "TEMA",66,0.0,0.0, "TEMA",264,0.0,0.0),  # #3 KAMA(12)/TEMA(66)/ft5:TEMA(264)
        ("KAMA",16,0.0,0.0, "TEMA",63,0.0,0.0, "TEMA",252,0.0,0.0),  # #4 KAMA(16)/TEMA(63)/ft5:TEMA(252)
        ("KAMA",16,0.0,0.0, "HMA",57,0.0,0.0, "HMA",228,0.0,0.0),  # #5 KAMA(16)/HMA(57)/ft5:HMA(228)
    ],
    "DOT/USDT": [
        ("VIDYA",14,0.0,0.0, "KAMA",33,0.0,0.0, "KAMA",132,0.0,0.0),  # #1 VIDYA(14)/KAMA(33)/ft5:KAMA(132)
        ("VIDYA",14,0.0,0.0, "KAMA",36,0.0,0.0, "KAMA",144,0.0,0.0),  # #2 VIDYA(14)/KAMA(36)/ft5:KAMA(144)
        ("McGinley",24,0.0,0.0, "KAMA",49,0.0,0.0, "KAMA",196,0.0,0.0),  # #3 McGinley(24)/KAMA(49)/ft5:KAMA(196)
        ("VIDYA",18,0.0,0.0, "KAMA",36,0.0,0.0, "KAMA",144,0.0,0.0),  # #4 VIDYA(18)/KAMA(36)/ft5:KAMA(144)
        ("McGinley",24,0.0,0.0, "KAMA",51,0.0,0.0, "KAMA",204,0.0,0.0),  # #5 McGinley(24)/KAMA(51)/ft5:KAMA(204)
    ],
    "ENA/USDT": [
        ("McGinley",24,0.0,0.0, "VWMA",75,0.0,0.0, "VWMA",300,0.0,0.0),  # #1 McGinley(24)/VWMA(75)/ft5:VWMA(300)
        ("EMA",22,0.0,0.0, "KAMA",45,0.0,0.0, "KAMA",180,0.0,0.0),  # #2 EMA(22)/KAMA(45)/ft5:KAMA(180)
        ("McGinley",18,0.0,0.0, "VWMA",48,0.0,0.0, "VWMA",192,0.0,0.0),  # #3 McGinley(18)/VWMA(48)/ft5:VWMA(192)
        ("Tenkan",24,0.0,0.0, "KAMA",54,0.0,0.0, "KAMA",216,0.0,0.0),  # #4 Tenkan(24)/KAMA(54)/ft5:KAMA(216)
        ("Tenkan",20,0.0,0.0, "KAMA",72,0.0,0.0, "KAMA",288,0.0,0.0),  # #5 Tenkan(20)/KAMA(72)/ft5:KAMA(288)
    ],
    "ETC/USDT": [
        ("VIDYA",24,0.0,0.0, "KAMA",49,0.0,0.0, "KAMA",196,0.0,0.0),  # #1 VIDYA(24)/KAMA(49)/ft5:KAMA(196)
        ("KAMA",14,0.0,0.0, "TEMA",54,0.0,0.0, "TEMA",216,0.0,0.0),  # #2 KAMA(14)/TEMA(54)/ft5:TEMA(216)
        ("KAMA",12,0.0,0.0, "TEMA",54,0.0,0.0, "TEMA",216,0.0,0.0),  # #3 KAMA(12)/TEMA(54)/ft5:TEMA(216)
        ("VIDYA",24,0.0,0.0, "KAMA",48,0.0,0.0, "KAMA",192,0.0,0.0),  # #4 VIDYA(24)/KAMA(48)/ft5:KAMA(192)
        ("VIDYA",14,0.0,0.0, "SSmoother",60,0.0,0.0, "SSmoother",240,0.0,0.0),  # #5 VIDYA(14)/SSmoother(60)/ft5:SSmoother(240)
        ("VIDYA",14,0.0,0.0, "EMA",36,0.0,0.0, "EMA",144,0.0,0.0),  # #6 VIDYA(14)/EMA(36)/ft5:EMA(144)  # AGRESIVO
    ],
    "ETH/USDT": [
        ("McGinley",20,0.0,0.0, "KAMA",48,0.0,0.0, "KAMA",192,0.0,0.0),  # #1 McGinley(20)/KAMA(48)/ft5:KAMA(192)
        ("McGinley",16,0.0,0.0, "KAMA",49,0.0,0.0, "KAMA",196,0.0,0.0),  # #2 McGinley(16)/KAMA(49)/ft5:KAMA(196)
        ("Tenkan",22,0.0,0.0, "EMA",51,0.0,0.0, "EMA",204,0.0,0.0),  # #3 Tenkan(22)/EMA(51)/ft5:EMA(204)
        ("Tenkan",22,0.0,0.0, "SMA",57,0.0,0.0, "SMA",228,0.0,0.0),  # #4 Tenkan(22)/SMA(57)/ft5:SMA(228)
        ("Tenkan",22,0.0,0.0, "EMA",54,0.0,0.0, "EMA",216,0.0,0.0),  # #5 Tenkan(22)/EMA(54)/ft5:EMA(216)
        ("Tenkan",22,0.0,0.0, "EMA",45,0.0,0.0, "EMA",180,0.0,0.0),  # #6 Tenkan(22)/EMA(45)/ft5:EMA(180)  # AGRESIVO
    ],
    "FET/USDT": [
        ("ALMA",20,0.5,4.0, "T3",36,0.8,0.0, "T3",144,0.8,0.0),  # #1 ALMA(20,0.5,4)/T3(36,v0.8)/ft5:T3(144)
        ("ALMA",22,0.5,4.0, "T3",36,0.8,0.0, "T3",144,0.8,0.0),  # #2 ALMA(22,0.5,4)/T3(36,v0.8)/ft5:T3(144)
        ("McGinley",16,0.0,0.0, "T3",39,0.8,0.0, "T3",156,0.8,0.0),  # #3 McGinley(16)/T3(39,v0.8)/ft5:T3(156)
        ("McGinley",14,0.0,0.0, "T3",33,0.7,0.0, "T3",132,0.7,0.0),  # #4 McGinley(14)/T3(33,v0.7)/ft5:T3(132)
        ("McGinley",12,0.0,0.0, "ALMA",69,0.85,4.0, "ALMA",276,0.85,4.0),  # #5 McGinley(12)/ALMA(69,0.85,4)/ft5:ALMA(276)
    ],
    "FIL/USDT": [
        ("VIDYA",10,0.0,0.0, "DEMA",75,0.0,0.0, "DEMA",300,0.0,0.0),  # #1 VIDYA(10)/DEMA(75)/ft5:DEMA(300)
        ("VIDYA",12,0.0,0.0, "DEMA",75,0.0,0.0, "DEMA",300,0.0,0.0),  # #2 VIDYA(12)/DEMA(75)/ft5:DEMA(300)
        ("KAMA",14,0.0,0.0, "TEMA",69,0.0,0.0, "TEMA",276,0.0,0.0),  # #3 KAMA(14)/TEMA(69)/ft5:TEMA(276)
        ("KAMA",12,0.0,0.0, "DEMA",48,0.0,0.0, "DEMA",192,0.0,0.0),  # #4 KAMA(12)/DEMA(48)/ft5:DEMA(192)
        ("KAMA",14,0.0,0.0, "DEMA",49,0.0,0.0, "DEMA",196,0.0,0.0),  # #5 KAMA(14)/DEMA(49)/ft5:DEMA(196)
    ],
    "GRT/USDT": [
        ("VIDYA",24,0.0,0.0, "KAMA",39,0.0,0.0, "KAMA",156,0.0,0.0),  # #1 VIDYA(24)/KAMA(39)/ft5:KAMA(156)
        ("McGinley",10,0.0,0.0, "DEMA",39,0.0,0.0, "DEMA",156,0.0,0.0),  # #2 McGinley(10)/DEMA(39)/ft5:DEMA(156)
        ("VIDYA",24,0.0,0.0, "KAMA",36,0.0,0.0, "KAMA",144,0.0,0.0),  # #3 VIDYA(24)/KAMA(36)/ft5:KAMA(144)
        ("McGinley",10,0.0,0.0, "TEMA",60,0.0,0.0, "TEMA",240,0.0,0.0),  # #4 McGinley(10)/TEMA(60)/ft5:TEMA(240)
        ("EMA",12,0.0,0.0, "TEMA",60,0.0,0.0, "TEMA",240,0.0,0.0),  # #5 EMA(12)/TEMA(60)/ft5:TEMA(240)
        ("ALMA",18,0.5,6.0, "TEMA",63,0.0,0.0, "TEMA",252,0.0,0.0),  # #15 ALMA(18,0.5,6)/TEMA(63)/ft5:TEMA(252)  # AGRESIVO
    ],
    "HBAR/USDT": [
        ("McGinley",24,0.0,0.0, "KAMA",49,0.0,0.0, "KAMA",196,0.0,0.0),  # #1 McGinley(24)/KAMA(49)/ft5:KAMA(196)
        ("McGinley",18,0.0,0.0, "KAMA",42,0.0,0.0, "KAMA",168,0.0,0.0),  # #2 McGinley(18)/KAMA(42)/ft5:KAMA(168)
        ("McGinley",24,0.0,0.0, "KAMA",48,0.0,0.0, "KAMA",192,0.0,0.0),  # #3 McGinley(24)/KAMA(48)/ft5:KAMA(192)
        ("McGinley",22,0.0,0.0, "KAMA",45,0.0,0.0, "KAMA",180,0.0,0.0),  # #4 McGinley(22)/KAMA(45)/ft5:KAMA(180)
        ("VIDYA",16,0.0,0.0, "VWMA",54,0.0,0.0, "VWMA",216,0.0,0.0),  # #5 VIDYA(16)/VWMA(54)/ft5:VWMA(216)
    ],
    "ICP/USDT": [
        ("VIDYA",12,0.0,0.0, "KAMA",45,0.0,0.0, "KAMA",180,0.0,0.0),  # #1 VIDYA(12)/KAMA(45)/ft5:KAMA(180)
        ("VIDYA",14,0.0,0.0, "KAMA",48,0.0,0.0, "KAMA",192,0.0,0.0),  # #2 VIDYA(14)/KAMA(48)/ft5:KAMA(192)
        ("VIDYA",12,0.0,0.0, "KAMA",48,0.0,0.0, "KAMA",192,0.0,0.0),  # #3 VIDYA(12)/KAMA(48)/ft5:KAMA(192)
        ("VIDYA",10,0.0,0.0, "KAMA",42,0.0,0.0, "KAMA",168,0.0,0.0),  # #4 VIDYA(10)/KAMA(42)/ft5:KAMA(168)
        ("T3",18,0.8,0.0, "SMA",48,0.0,0.0, "SMA",192,0.0,0.0),  # #5 T3(18,v0.8)/SMA(48)/ft5:SMA(192)
    ],
    "IMX/USDT": [
        ("KAMA",14,0.0,0.0, "TEMA",66,0.0,0.0, "TEMA",264,0.0,0.0),  # #1 KAMA(14)/TEMA(66)/ft5:TEMA(264)
        ("SMA",22,0.0,0.0, "DEMA",39,0.0,0.0, "DEMA",156,0.0,0.0),  # #2 SMA(22)/DEMA(39)/ft5:DEMA(156)
        ("ALMA",24,0.5,4.0, "TEMA",54,0.0,0.0, "TEMA",216,0.0,0.0),  # #3 ALMA(24,0.5,4)/TEMA(54)/ft5:TEMA(216)
        ("KAMA",14,0.0,0.0, "TEMA",63,0.0,0.0, "TEMA",252,0.0,0.0),  # #4 KAMA(14)/TEMA(63)/ft5:TEMA(252)
        ("SMA",22,0.0,0.0, "JMA",72,0.0,0.0, "JMA",288,0.0,0.0),  # #5 SMA(22)/JMA(72)/ft5:JMA(288)
    ],
    "INJ/USDT": [
        ("McGinley",24,0.0,0.0, "KAMA",42,0.0,0.0, "KAMA",168,0.0,0.0),  # #1 McGinley(24)/KAMA(42)/ft5:KAMA(168)
        ("McGinley",24,0.0,0.0, "KAMA",49,0.0,0.0, "KAMA",196,0.0,0.0),  # #2 McGinley(24)/KAMA(49)/ft5:KAMA(196)
        ("SMA",14,0.0,0.0, "TEMA",60,0.0,0.0, "TEMA",240,0.0,0.0),  # #3 SMA(14)/TEMA(60)/ft5:TEMA(240)
        ("SMA",14,0.0,0.0, "TEMA",57,0.0,0.0, "TEMA",228,0.0,0.0),  # #4 SMA(14)/TEMA(57)/ft5:TEMA(228)
        ("McGinley",14,0.0,0.0, "KAMA",39,0.0,0.0, "KAMA",156,0.0,0.0),  # #5 McGinley(14)/KAMA(39)/ft5:KAMA(156)
        ("T3",12,0.8,0.0, "TEMA",49,0.0,0.0, "TEMA",196,0.0,0.0),  # #7 T3(12,v0.8)/TEMA(49)/ft5:TEMA(196)  # AGRESIVO
    ],
    "LINK/USDT": [
        ("McGinley",20,0.0,0.0, "ALMA",33,0.85,4.0, "ALMA",132,0.85,4.0),  # #1 McGinley(20)/ALMA(33,0.85,4)/ft5:ALMA(132)
        ("McGinley",18,0.0,0.0, "ALMA",30,0.85,6.0, "ALMA",120,0.85,6.0),  # #2 McGinley(18)/ALMA(30,0.85,6)/ft5:ALMA(120)
        ("McGinley",12,0.0,0.0, "HMA",30,0.0,0.0, "HMA",120,0.0,0.0),  # #3 McGinley(12)/HMA(30)/ft5:HMA(120)
        ("McGinley",20,0.0,0.0, "ALMA",48,0.85,6.0, "ALMA",192,0.85,6.0),  # #4 McGinley(20)/ALMA(48,0.85,6)/ft5:ALMA(192)
        ("McGinley",22,0.0,0.0, "SSmoother",33,0.0,0.0, "SSmoother",132,0.0,0.0),  # #5 McGinley(22)/SSmoother(33)/ft5:SSmoother(132)
        ("KAMA",14,0.0,0.0, "ALMA",36,0.85,6.0, "ALMA",144,0.85,6.0),  # #7 KAMA(14)/ALMA(36,0.85,6)/ft5:ALMA(144)  # AGRESIVO
    ],
    "LTC/USDT": [
        ("SMA",16,0.0,0.0, "TEMA",63,0.0,0.0, "TEMA",252,0.0,0.0),  # #1 SMA(16)/TEMA(63)/ft5:TEMA(252)
        ("EMA",14,0.0,0.0, "TEMA",69,0.0,0.0, "TEMA",276,0.0,0.0),  # #2 EMA(14)/TEMA(69)/ft5:TEMA(276)
        ("VWMA",24,0.0,0.0, "DEMA",45,0.0,0.0, "DEMA",180,0.0,0.0),  # #3 VWMA(24)/DEMA(45)/ft5:DEMA(180)
        ("KAMA",12,0.0,0.0, "DEMA",33,0.0,0.0, "DEMA",132,0.0,0.0),  # #4 KAMA(12)/DEMA(33)/ft5:DEMA(132)
        ("KAMA",12,0.0,0.0, "JMA",72,0.0,0.0, "JMA",288,0.0,0.0),  # #5 KAMA(12)/JMA(72)/ft5:JMA(288)
    ],
    "MANA/USDT": [
        ("EMA",14,0.0,0.0, "ZLEMA",30,0.0,0.0, "ZLEMA",120,0.0,0.0),  # #1 EMA(14)/ZLEMA(30)/ft5:ZLEMA(120)
        ("McGinley",22,0.0,0.0, "KAMA",45,0.0,0.0, "KAMA",180,0.0,0.0),  # #2 McGinley(22)/KAMA(45)/ft5:KAMA(180)
        ("McGinley",22,0.0,0.0, "KAMA",42,0.0,0.0, "KAMA",168,0.0,0.0),  # #3 McGinley(22)/KAMA(42)/ft5:KAMA(168)
        ("McGinley",24,0.0,0.0, "KAMA",42,0.0,0.0, "KAMA",168,0.0,0.0),  # #4 McGinley(24)/KAMA(42)/ft5:KAMA(168)
        ("McGinley",22,0.0,0.0, "KAMA",39,0.0,0.0, "KAMA",156,0.0,0.0),  # #5 McGinley(22)/KAMA(39)/ft5:KAMA(156)
    ],
    "NEAR/USDT": [
        ("KAMA",22,0.0,0.0, "ZLEMA",72,0.0,0.0, "ZLEMA",288,0.0,0.0),  # #1 KAMA(22)/ZLEMA(72)/ft5:ZLEMA(288)
        ("KAMA",14,0.0,0.0, "DEMA",45,0.0,0.0, "DEMA",180,0.0,0.0),  # #2 KAMA(14)/DEMA(45)/ft5:DEMA(180)
        ("KAMA",16,0.0,0.0, "DEMA",42,0.0,0.0, "DEMA",168,0.0,0.0),  # #3 KAMA(16)/DEMA(42)/ft5:DEMA(168)
        ("KAMA",22,0.0,0.0, "ZLEMA",69,0.0,0.0, "ZLEMA",276,0.0,0.0),  # #4 KAMA(22)/ZLEMA(69)/ft5:ZLEMA(276)
        ("KAMA",24,0.0,0.0, "HMA",60,0.0,0.0, "HMA",240,0.0,0.0),  # #5 KAMA(24)/HMA(60)/ft5:HMA(240)
    ],
    "ONDO/USDT": [
        ("T3",10,0.8,0.0, "EMA",36,0.0,0.0, "EMA",144,0.0,0.0),  # #1 T3(10,v0.8)/EMA(36)/ft5:EMA(144)
        ("VIDYA",24,0.0,0.0, "T3",33,0.7,0.0, "T3",132,0.7,0.0),  # #2 VIDYA(24)/T3(33,v0.7)/ft5:T3(132)
        ("T3",10,0.7,0.0, "EMA",36,0.0,0.0, "EMA",144,0.0,0.0),  # #3 T3(10,v0.7)/EMA(36)/ft5:EMA(144)
        ("T3",10,0.7,0.0, "EMA",33,0.0,0.0, "EMA",132,0.0,0.0),  # #4 T3(10,v0.7)/EMA(33)/ft5:EMA(132)
        ("VIDYA",18,0.0,0.0, "T3",33,0.8,0.0, "T3",132,0.8,0.0),  # #5 VIDYA(18)/T3(33,v0.8)/ft5:T3(132)
    ],
    "OP/USDT": [
        ("T3",20,0.8,0.0, "SMA",63,0.0,0.0, "SMA",252,0.0,0.0),  # #1 T3(20,v0.8)/SMA(63)/ft5:SMA(252)
        ("T3",20,0.8,0.0, "SMA",60,0.0,0.0, "SMA",240,0.0,0.0),  # #2 T3(20,v0.8)/SMA(60)/ft5:SMA(240)
        ("T3",20,0.7,0.0, "SMA",63,0.0,0.0, "SMA",252,0.0,0.0),  # #3 T3(20,v0.7)/SMA(63)/ft5:SMA(252)
        ("KAMA",22,0.0,0.0, "HMA",66,0.0,0.0, "VIDYA",210,0.0,0.0),  # #4 KAMA(22)/HMA(66)/VIDYA(210)
        ("KAMA",22,0.0,0.0, "HMA",66,0.0,0.0, "VIDYA",180,0.0,0.0),  # #5 KAMA(22)/HMA(66)/VIDYA(180)
    ],
    "PEPE/USDT": [
        ("KAMA",16,0.0,0.0, "EMA",33,0.0,0.0, "EMA",132,0.0,0.0),  # #1 KAMA(16)/EMA(33)/ft5:EMA(132)
        ("KAMA",16,0.0,0.0, "EMA",30,0.0,0.0, "EMA",120,0.0,0.0),  # #2 KAMA(16)/EMA(30)/ft5:EMA(120)
        ("KAMA",14,0.0,0.0, "ALMA",75,0.5,4.0, "ALMA",300,0.5,4.0),  # #3 KAMA(14)/ALMA(75,0.5,4)/ft5:ALMA(300)
        ("KAMA",20,0.0,0.0, "KAMA",33,0.0,0.0, "KAMA",132,0.0,0.0),  # #4 KAMA(20)/KAMA(33)/ft5:KAMA(132)
        ("KAMA",16,0.0,0.0, "ALMA",75,0.5,4.0, "ALMA",300,0.5,4.0),  # #5 KAMA(16)/ALMA(75,0.5,4)/ft5:ALMA(300)
    ],
    "POL/USDT": [
        ("T3",16,0.7,0.0, "VWMA",51,0.0,0.0, "VWMA",204,0.0,0.0),  # #1 T3(16,v0.7)/VWMA(51)/ft5:VWMA(204)
        ("T3",16,0.7,0.0, "KAMA",48,0.0,0.0, "KAMA",192,0.0,0.0),  # #2 T3(16,v0.7)/KAMA(48)/ft5:KAMA(192)
        ("T3",16,0.8,0.0, "KAMA",54,0.0,0.0, "KAMA",216,0.0,0.0),  # #3 T3(16,v0.8)/KAMA(54)/ft5:KAMA(216)
        ("T3",16,0.8,0.0, "KAMA",49,0.0,0.0, "KAMA",196,0.0,0.0),  # #4 T3(16,v0.8)/KAMA(49)/ft5:KAMA(196)
        ("McGinley",22,0.0,0.0, "KAMA",42,0.0,0.0, "KAMA",168,0.0,0.0),  # #5 McGinley(22)/KAMA(42)/ft5:KAMA(168)
    ],
    "QNT/USDT": [
        ("VWMA",12,0.0,0.0, "JMA",39,0.0,0.0, "JMA",156,0.0,0.0),  # #1 VWMA(12)/JMA(39)/ft5:JMA(156)
        ("VWMA",12,0.0,0.0, "JMA",36,0.0,0.0, "JMA",144,0.0,0.0),  # #2 VWMA(12)/JMA(36)/ft5:JMA(144)
        ("VWMA",12,0.0,0.0, "JMA",33,0.0,0.0, "JMA",132,0.0,0.0),  # #3 VWMA(12)/JMA(33)/ft5:JMA(132)
        ("VIDYA",24,0.0,0.0, "KAMA",36,0.0,0.0, "KAMA",144,0.0,0.0),  # #4 VIDYA(24)/KAMA(36)/ft5:KAMA(144)
        ("ALMA",18,0.5,6.0, "ZLEMA",45,0.0,0.0, "ZLEMA",180,0.0,0.0),  # #5 ALMA(18,0.5,6)/ZLEMA(45)/ft5:ZLEMA(180)
    ],
    "RENDER/USDT": [
        ("VIDYA",12,0.0,0.0, "VWMA",54,0.0,0.0, "VWMA",216,0.0,0.0),  # #1 VIDYA(12)/VWMA(54)/ft5:VWMA(216)
        ("VIDYA",20,0.0,0.0, "VWMA",66,0.0,0.0, "VWMA",264,0.0,0.0),  # #2 VIDYA(20)/VWMA(66)/ft5:VWMA(264)
        ("VIDYA",16,0.0,0.0, "VWMA",54,0.0,0.0, "VWMA",216,0.0,0.0),  # #3 VIDYA(16)/VWMA(54)/ft5:VWMA(216)
        ("VIDYA",20,0.0,0.0, "VWMA",72,0.0,0.0, "VWMA",288,0.0,0.0),  # #4 VIDYA(20)/VWMA(72)/ft5:VWMA(288)
        ("VIDYA",10,0.0,0.0, "VWMA",54,0.0,0.0, "VWMA",216,0.0,0.0),  # #5 VIDYA(10)/VWMA(54)/ft5:VWMA(216)
    ],
    "SAND/USDT": [
        ("KAMA",22,0.0,0.0, "KAMA",33,0.0,0.0, "KAMA",132,0.0,0.0),  # #1 KAMA(22)/KAMA(33)/ft5:KAMA(132)
        ("KAMA",24,0.0,0.0, "KAMA",33,0.0,0.0, "KAMA",132,0.0,0.0),  # #2 KAMA(24)/KAMA(33)/ft5:KAMA(132)
        ("KAMA",18,0.0,0.0, "KAMA",33,0.0,0.0, "KAMA",132,0.0,0.0),  # #3 KAMA(18)/KAMA(33)/ft5:KAMA(132)
        ("KAMA",20,0.0,0.0, "KAMA",33,0.0,0.0, "KAMA",132,0.0,0.0),  # #4 KAMA(20)/KAMA(33)/ft5:KAMA(132)
        ("KAMA",20,0.0,0.0, "KAMA",36,0.0,0.0, "KAMA",144,0.0,0.0),  # #5 KAMA(20)/KAMA(36)/ft5:KAMA(144)
    ],
    "SEI/USDT": [
        ("McGinley",20,0.0,0.0, "KAMA",45,0.0,0.0, "KAMA",180,0.0,0.0),  # #1 McGinley(20)/KAMA(45)/ft5:KAMA(180)
        ("McGinley",20,0.0,0.0, "KAMA",42,0.0,0.0, "KAMA",168,0.0,0.0),  # #2 McGinley(20)/KAMA(42)/ft5:KAMA(168)
        ("McGinley",22,0.0,0.0, "KAMA",48,0.0,0.0, "KAMA",192,0.0,0.0),  # #3 McGinley(22)/KAMA(48)/ft5:KAMA(192)
        ("McGinley",22,0.0,0.0, "KAMA",49,0.0,0.0, "KAMA",196,0.0,0.0),  # #4 McGinley(22)/KAMA(49)/ft5:KAMA(196)
        ("McGinley",24,0.0,0.0, "KAMA",51,0.0,0.0, "KAMA",204,0.0,0.0),  # #5 McGinley(24)/KAMA(51)/ft5:KAMA(204)
    ],
    "SHIB/USDT": [
        ("McGinley",24,0.0,0.0, "KAMA",49,0.0,0.0, "KAMA",196,0.0,0.0),  # #1 McGinley(24)/KAMA(49)/ft5:KAMA(196)
        ("McGinley",24,0.0,0.0, "KAMA",42,0.0,0.0, "KAMA",168,0.0,0.0),  # #2 McGinley(24)/KAMA(42)/ft5:KAMA(168)
        ("T3",16,0.7,0.0, "EMA",45,0.0,0.0, "EMA",180,0.0,0.0),  # #3 T3(16,v0.7)/EMA(45)/ft5:EMA(180)
        ("McGinley",22,0.0,0.0, "KAMA",42,0.0,0.0, "KAMA",168,0.0,0.0),  # #4 McGinley(22)/KAMA(42)/ft5:KAMA(168)
        ("T3",20,0.8,0.0, "KAMA",51,0.0,0.0, "KAMA",204,0.0,0.0),  # #5 T3(20,v0.8)/KAMA(51)/ft5:KAMA(204)
    ],
    "SOL/USDT": [
        ("KAMA",22,0.0,0.0, "HMA",69,0.0,0.0, "HMA",276,0.0,0.0),  # #1 KAMA(22)/HMA(69)/ft5:HMA(276)
        ("McGinley",18,0.0,0.0, "KAMA",48,0.0,0.0, "KAMA",192,0.0,0.0),  # #2 McGinley(18)/KAMA(48)/ft5:KAMA(192)
        ("KAMA",20,0.0,0.0, "HMA",69,0.0,0.0, "HMA",276,0.0,0.0),  # #3 KAMA(20)/HMA(69)/ft5:HMA(276)
        ("VIDYA",14,0.0,0.0, "EMA",49,0.0,0.0, "EMA",196,0.0,0.0),  # #4 VIDYA(14)/EMA(49)/ft5:EMA(196)
        ("KAMA",20,0.0,0.0, "HMA",72,0.0,0.0, "HMA",288,0.0,0.0),  # #5 KAMA(20)/HMA(72)/ft5:HMA(288)
    ],
    "STX/USDT": [
        ("VIDYA",20,0.0,0.0, "VWMA",54,0.0,0.0, "VWMA",216,0.0,0.0),  # #1 VIDYA(20)/VWMA(54)/ft5:VWMA(216)
        ("VIDYA",22,0.0,0.0, "ALMA",63,0.5,6.0, "ALMA",252,0.5,6.0),  # #2 VIDYA(22)/ALMA(63,0.5,6)/ft5:ALMA(252)
        ("VIDYA",24,0.0,0.0, "ALMA",66,0.5,6.0, "ALMA",264,0.5,6.0),  # #3 VIDYA(24)/ALMA(66,0.5,6)/ft5:ALMA(264)
        ("VIDYA",24,0.0,0.0, "ALMA",69,0.5,6.0, "ALMA",276,0.5,6.0),  # #4 VIDYA(24)/ALMA(69,0.5,6)/ft5:ALMA(276)
        ("VIDYA",22,0.0,0.0, "VWMA",57,0.0,0.0, "VWMA",228,0.0,0.0),  # #5 VIDYA(22)/VWMA(57)/ft5:VWMA(228)
    ],
    "SUI/USDT": [
        ("VIDYA",22,0.0,0.0, "McGinley",36,0.0,0.0, "McGinley",144,0.0,0.0),  # #1 VIDYA(22)/McGinley(36)/ft5:McGinley(144)
        ("SSmoother",24,0.0,0.0, "KAMA",36,0.0,0.0, "KAMA",144,0.0,0.0),  # #2 SSmoother(24)/KAMA(36)/ft5:KAMA(144)
        ("VIDYA",20,0.0,0.0, "KAMA",33,0.0,0.0, "KAMA",132,0.0,0.0),  # #3 VIDYA(20)/KAMA(33)/ft5:KAMA(132)
        ("McGinley",18,0.0,0.0, "KAMA",39,0.0,0.0, "KAMA",156,0.0,0.0),  # #4 McGinley(18)/KAMA(39)/ft5:KAMA(156)
        ("McGinley",20,0.0,0.0, "KAMA",45,0.0,0.0, "KAMA",180,0.0,0.0),  # #5 McGinley(20)/KAMA(45)/ft5:KAMA(180)
        ("SSmoother",20,0.0,0.0, "KAMA",33,0.0,0.0, "KAMA",132,0.0,0.0),  # #6 SSmoother(20)/KAMA(33)/ft5:KAMA(132)  # AGRESIVO
    ],
    "TAO/USDT": [
        ("VIDYA",24,0.0,0.0, "SMA",45,0.0,0.0, "SMA",180,0.0,0.0),  # #1 VIDYA(24)/SMA(45)/ft5:SMA(180)
        ("VIDYA",24,0.0,0.0, "SMA",45,0.0,0.0, "T3",250,0.8,0.0),  # #2 VIDYA(24)/SMA(45)/T3(250,v0.8)
        ("VIDYA",20,0.0,0.0, "KAMA",51,0.0,0.0, "KAMA",204,0.0,0.0),  # #3 VIDYA(20)/KAMA(51)/ft5:KAMA(204)
        ("VIDYA",12,0.0,0.0, "McGinley",33,0.0,0.0, "McGinley",132,0.0,0.0),  # #4 VIDYA(12)/McGinley(33)/ft5:McGinley(132)
        ("VIDYA",14,0.0,0.0, "ALMA",75,0.85,4.0, "ALMA",300,0.85,4.0),  # #5 VIDYA(14)/ALMA(75,0.85,4)/ft5:ALMA(300)
    ],
    "THETA/USDT": [
        ("McGinley",22,0.0,0.0, "KAMA",42,0.0,0.0, "KAMA",168,0.0,0.0),  # #1 McGinley(22)/KAMA(42)/ft5:KAMA(168)
        ("VIDYA",24,0.0,0.0, "KAMA",48,0.0,0.0, "KAMA",192,0.0,0.0),  # #2 VIDYA(24)/KAMA(48)/ft5:KAMA(192)
        ("VIDYA",24,0.0,0.0, "KAMA",49,0.0,0.0, "KAMA",196,0.0,0.0),  # #3 VIDYA(24)/KAMA(49)/ft5:KAMA(196)
        ("McGinley",22,0.0,0.0, "KAMA",45,0.0,0.0, "KAMA",180,0.0,0.0),  # #4 McGinley(22)/KAMA(45)/ft5:KAMA(180)
        ("McGinley",22,0.0,0.0, "KAMA",39,0.0,0.0, "KAMA",156,0.0,0.0),  # #5 McGinley(22)/KAMA(39)/ft5:KAMA(156)
    ],
    "TON/USDT": [
        ("SMA",16,0.0,0.0, "ALMA",30,0.85,4.0, "ALMA",120,0.85,4.0),  # #1 SMA(16)/ALMA(30,0.85,4)/ft5:ALMA(120)
        ("T3",16,0.8,0.0, "SSmoother",39,0.0,0.0, "SSmoother",156,0.0,0.0),  # #2 T3(16,v0.8)/SSmoother(39)/ft5:SSmoother(156)
        ("T3",14,0.8,0.0, "SSmoother",33,0.0,0.0, "SSmoother",132,0.0,0.0),  # #3 T3(14,v0.8)/SSmoother(33)/ft5:SSmoother(132)
        ("T3",16,0.7,0.0, "SSmoother",45,0.0,0.0, "SSmoother",180,0.0,0.0),  # #4 T3(16,v0.7)/SSmoother(45)/ft5:SSmoother(180)
        ("T3",18,0.8,0.0, "SSmoother",51,0.0,0.0, "SSmoother",204,0.0,0.0),  # #5 T3(18,v0.8)/SSmoother(51)/ft5:SSmoother(204)
    ],
    "TRX/USDT": [
        ("McGinley",24,0.0,0.0, "KAMA",69,0.0,0.0, "KAMA",276,0.0,0.0),  # #1 McGinley(24)/KAMA(69)/ft5:KAMA(276)
        ("McGinley",22,0.0,0.0, "KAMA",66,0.0,0.0, "KAMA",264,0.0,0.0),  # #2 McGinley(22)/KAMA(66)/ft5:KAMA(264)
        ("VIDYA",18,0.0,0.0, "KAMA",57,0.0,0.0, "KAMA",228,0.0,0.0),  # #3 VIDYA(18)/KAMA(57)/ft5:KAMA(228)
        ("McGinley",22,0.0,0.0, "KAMA",63,0.0,0.0, "KAMA",252,0.0,0.0),  # #4 McGinley(22)/KAMA(63)/ft5:KAMA(252)
        ("McGinley",24,0.0,0.0, "KAMA",57,0.0,0.0, "KAMA",228,0.0,0.0),  # #5 McGinley(24)/KAMA(57)/ft5:KAMA(228)
    ],
    "UNI/USDT": [
        ("KAMA",16,0.0,0.0, "HMA",54,0.0,0.0, "HMA",216,0.0,0.0),  # #1 KAMA(16)/HMA(54)/ft5:HMA(216)
        ("KAMA",16,0.0,0.0, "HMA",57,0.0,0.0, "HMA",228,0.0,0.0),  # #2 KAMA(16)/HMA(57)/ft5:HMA(228)
        ("KAMA",16,0.0,0.0, "HMA",51,0.0,0.0, "HMA",204,0.0,0.0),  # #3 KAMA(16)/HMA(51)/ft5:HMA(204)
        ("McGinley",14,0.0,0.0, "TEMA",45,0.0,0.0, "TEMA",180,0.0,0.0),  # #4 McGinley(14)/TEMA(45)/ft5:TEMA(180)
        ("KAMA",14,0.0,0.0, "DEMA",39,0.0,0.0, "DEMA",156,0.0,0.0),  # #5 KAMA(14)/DEMA(39)/ft5:DEMA(156)
    ],
    "VET/USDT": [
        ("McGinley",22,0.0,0.0, "KAMA",42,0.0,0.0, "KAMA",168,0.0,0.0),  # #1 McGinley(22)/KAMA(42)/ft5:KAMA(168)
        ("McGinley",20,0.0,0.0, "KAMA",45,0.0,0.0, "KAMA",180,0.0,0.0),  # #2 McGinley(20)/KAMA(45)/ft5:KAMA(180)
        ("McGinley",22,0.0,0.0, "KAMA",45,0.0,0.0, "KAMA",180,0.0,0.0),  # #3 McGinley(22)/KAMA(45)/ft5:KAMA(180)
        ("McGinley",16,0.0,0.0, "KAMA",39,0.0,0.0, "KAMA",156,0.0,0.0),  # #4 McGinley(16)/KAMA(39)/ft5:KAMA(156)
        ("McGinley",20,0.0,0.0, "KAMA",42,0.0,0.0, "KAMA",168,0.0,0.0),  # #5 McGinley(20)/KAMA(42)/ft5:KAMA(168)
    ],
    "WLD/USDT": [
        ("VIDYA",18,0.0,0.0, "T3",39,0.8,0.0, "T3",156,0.8,0.0),  # #1 VIDYA(18)/T3(39,v0.8)/ft5:T3(156)
        ("SMA",16,0.0,0.0, "HMA",69,0.0,0.0, "HMA",276,0.0,0.0),  # #2 SMA(16)/HMA(69)/ft5:HMA(276)
        ("VIDYA",18,0.0,0.0, "T3",39,0.7,0.0, "T3",156,0.7,0.0),  # #3 VIDYA(18)/T3(39,v0.7)/ft5:T3(156)
        ("McGinley",8,0.0,0.0, "DEMA",66,0.0,0.0, "DEMA",264,0.0,0.0),  # #4 McGinley(8)/DEMA(66)/ft5:DEMA(264)
        ("McGinley",8,0.0,0.0, "DEMA",69,0.0,0.0, "DEMA",276,0.0,0.0),  # #5 McGinley(8)/DEMA(69)/ft5:DEMA(276)
    ],
    "XLM/USDT": [
        ("VIDYA",14,0.0,0.0, "KAMA",48,0.0,0.0, "KAMA",192,0.0,0.0),  # #1 VIDYA(14)/KAMA(48)/ft5:KAMA(192)
        ("VIDYA",18,0.0,0.0, "KAMA",51,0.0,0.0, "KAMA",204,0.0,0.0),  # #2 VIDYA(18)/KAMA(51)/ft5:KAMA(204)
        ("VIDYA",24,0.0,0.0, "KAMA",30,0.0,0.0, "KAMA",120,0.0,0.0),  # #3 VIDYA(24)/KAMA(30)/ft5:KAMA(120)
        ("VIDYA",12,0.0,0.0, "KAMA",54,0.0,0.0, "KAMA",216,0.0,0.0),  # #4 VIDYA(12)/KAMA(54)/ft5:KAMA(216)
        ("VIDYA",14,0.0,0.0, "KAMA",49,0.0,0.0, "KAMA",196,0.0,0.0),  # #5 VIDYA(14)/KAMA(49)/ft5:KAMA(196)
    ],
    "XRP/USDT": [
        ("McGinley",14,0.0,0.0, "EMA",33,0.0,0.0, "EMA",132,0.0,0.0),  # #1 McGinley(14)/EMA(33)/ft5:EMA(132)
        ("McGinley",16,0.0,0.0, "EMA",39,0.0,0.0, "EMA",156,0.0,0.0),  # #2 McGinley(16)/EMA(39)/ft5:EMA(156)
        ("KAMA",12,0.0,0.0, "HMA",69,0.0,0.0, "HMA",276,0.0,0.0),  # #3 KAMA(12)/HMA(69)/ft5:HMA(276)
        ("McGinley",24,0.0,0.0, "KAMA",66,0.0,0.0, "KAMA",264,0.0,0.0),  # #4 McGinley(24)/KAMA(66)/ft5:KAMA(264)
        ("McGinley",14,0.0,0.0, "EMA",30,0.0,0.0, "EMA",120,0.0,0.0),  # #5 McGinley(14)/EMA(30)/ft5:EMA(120)
        ("KAMA",14,0.0,0.0, "SSmoother",33,0.0,0.0, "SSmoother",132,0.0,0.0),  # #8 KAMA(14)/SSmoother(33)/ft5:SSmoother(132)  # AGRESIVO
    ],
}

# Histéresis ATR: probar ambas variantes
HYST_VALUES = [0.0, 0.50]
HYST_ATR_LEN = 14

SL_PERCENT = 3.0
SL_EMERGENCY_PERCENT = 5.0
TS_PERCENT = 0.5
COOLDOWN_BARS = 1
COMMISSION_ROUND_TRIP = 0.10  # 0.10% round-trip por trade

# Divergencias (idénticos al lab v6.2)
DIV_RSI_LEN = 14
DIV_MACD_FAST = 12
DIV_MACD_SLOW = 26
DIV_MACD_SIGNAL = 9
DIV_STOCH_K = 14
DIV_STOCH_D = 3
DIV_STOCH_SMOOTH = 3
DIV_VWMACD_FAST = 12
DIV_VWMACD_SLOW = 26
DIV_CMF_LEN = 21
DIV_CCI_LEN = 10
DIV_MOM_LEN = 10
DIV_PIVOT_PERIOD = 5
DIV_MAX_PIVOTS = 10
DIV_MAX_BARS = 100

# ============================================
# EXCHANGE + DESCARGA (idéntico al lab)
# ============================================
exchange = ccxt.binance({'enableRateLimit': True})

def fetch_all_candles(symbol, timeframe, total_candles, max_retries=3):
    print(f"📥 Descargando {total_candles} velas de {symbol} ({timeframe})...")
    all_candles = []
    tf_ms = {'1h': 3600000, '4h': 14400000, '1d': 86400000}
    interval_ms = tf_ms.get(timeframe, 3600000)
    current_since = int(time.time() * 1000) - (total_candles + 200) * interval_ms
    requests_made = 0
    consecutive_errors = 0
    while len(all_candles) < total_candles + 100:
        try:
            ohlcv = exchange.fetch_ohlcv(symbol, timeframe, since=current_since, limit=1000)
            if not ohlcv: break
            all_candles.extend(ohlcv)
            current_since = ohlcv[-1][0] + interval_ms
            requests_made += 1
            consecutive_errors = 0
            time.sleep(0.1)
        except Exception as e:
            consecutive_errors += 1
            if consecutive_errors >= max_retries:
                print(f"❌ Error tras {max_retries} reintentos: {e}")
                return None
            print(f"⚠️ Reintento {consecutive_errors}: {e}")
            time.sleep(2 * consecutive_errors)
    df = pd.DataFrame(all_candles, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
    df = df.drop_duplicates(subset=['timestamp']).sort_values('timestamp').reset_index(drop=True)
    if len(df) > total_candles:
        df = df.tail(total_candles).reset_index(drop=True)
    print(f"✅ {len(df)} velas descargadas ({requests_made} requests)")
    return df

# ============================================
# INDICADORES — COPIADOS TEXTUALMENTE DEL LAB v6.2
# ============================================

def calc_heikin_ashi(df):
    n = len(df)
    ha_open = np.zeros(n)
    ha_close = np.zeros(n)
    ha_high = np.zeros(n)
    ha_low = np.zeros(n)
    o = df['open'].values
    h = df['high'].values
    l = df['low'].values
    c = df['close'].values
    ha_close[0] = (o[0] + h[0] + l[0] + c[0]) / 4
    ha_open[0] = (o[0] + c[0]) / 2
    ha_high[0] = max(h[0], ha_open[0], ha_close[0])
    ha_low[0] = min(l[0], ha_open[0], ha_close[0])
    for i in range(1, n):
        ha_close[i] = (o[i] + h[i] + l[i] + c[i]) / 4
        ha_open[i] = (ha_open[i-1] + ha_close[i-1]) / 2
        ha_high[i] = max(h[i], ha_open[i], ha_close[i])
        ha_low[i] = min(l[i], ha_open[i], ha_close[i])
    return pd.DataFrame({'open': ha_open, 'high': ha_high, 'low': ha_low, 'close': ha_close}, index=df.index)

def calc_ha_trend(df):
    avg_price = (df['open'] + df['high'] + df['low'] + df['close']) / 4
    avg_oc = (df['open'] + df['close'].shift(1)) / 2
    return avg_price > avg_oc

def resample_to_timeframe(df, target_tf):
    df_indexed = df.set_index('timestamp')
    if target_tf == "4h": rule = '4h'
    elif target_tf == "1d": rule = '1D'
    else: return df_indexed
    return df_indexed.resample(rule, closed='left', label='left').agg({
        'open': 'first', 'high': 'max', 'low': 'min', 'close': 'last', 'volume': 'sum'
    }).dropna()

def calc_rsi(close, length=14):
    delta = close.diff()
    gain = delta.where(delta > 0, 0.0)
    loss = (-delta.where(delta < 0, 0.0))
    avg_gain = gain.ewm(alpha=1.0/length, adjust=False, min_periods=1).mean()
    avg_loss = loss.ewm(alpha=1.0/length, adjust=False, min_periods=1).mean()
    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))

def calc_macd(close, fast=12, slow=26, signal=9):
    ema_fast = close.ewm(span=fast, adjust=False, min_periods=1).mean()
    ema_slow = close.ewm(span=slow, adjust=False, min_periods=1).mean()
    macd_line = ema_fast - ema_slow
    signal_line = macd_line.ewm(span=signal, adjust=False, min_periods=1).mean()
    return macd_line, macd_line - signal_line

def calc_stochastic(high, low, close, k=14, d=3, smooth=3):
    lowest_low = low.rolling(window=k, min_periods=1).min()
    highest_high = high.rolling(window=k, min_periods=1).max()
    stoch_range = highest_high - lowest_low
    stoch_raw = np.where(stoch_range > 0, 100 * (close - lowest_low) / stoch_range, 0.0)
    return pd.Series(stoch_raw, index=close.index).rolling(window=smooth, min_periods=1).mean()

def calc_vwmacd(close, volume, fast=12, slow=26):
    def vwma(price, vol, length):
        return (price * vol).rolling(window=length, min_periods=1).sum() / vol.rolling(window=length, min_periods=1).sum()
    return vwma(close, volume, fast) - vwma(close, volume, slow)

def calc_cmf(high, low, close, volume, length=21):
    h_l = high - low
    ad = ((close - low) - (high - close)) / h_l.replace(0, np.nan) * volume
    ad = ad.fillna(0.0)
    sma_ad = ad.rolling(window=length, min_periods=1).mean()
    sma_vol = volume.rolling(window=length, min_periods=1).mean()
    result = sma_ad / sma_vol.replace(0, np.nan)
    return result.fillna(0.0)

def calc_cci(high, low, close, length=10):
    tp = (high + low + close) / 3
    sma_tp = tp.rolling(window=length, min_periods=1).mean()
    mad = tp.rolling(window=length, min_periods=1).apply(lambda x: np.abs(x - x.mean()).mean(), raw=True)
    return (tp - sma_tp) / (0.015 * mad)

def calc_momentum(close, length=10):
    return close - close.shift(length)

# ============================================
# DIVERGENCIAS — COPIADA TEXTUALMENTE DEL LAB v6.2
# precalculate_divergences_pine_faithful con:
#   - can_check_pos/neg
#   - trajectory validation
#   - pivot_bar = t - period, almacena t como posición
# ============================================

def precalculate_divergences_pine_faithful(close_arr, high_arr, low_arr, indicators_dict, 
                                            n_bars, period=5, max_pivots=10, max_bars=100):
    n_indicators = len(indicators_dict)
    div_bits_arr = np.zeros((n_bars, n_indicators), dtype=np.uint8)
    
    pl_positions = []
    pl_vals = []
    ph_positions = []
    ph_vals = []
    
    indicator_arrays = list(indicators_dict.values())
    
    startpoint = 1
    
    for t in range(period, n_bars):
        pivot_bar = t - period
        
        if pivot_bar >= period:
            is_pivot_low = True
            for j in range(1, period + 1):
                if close_arr[pivot_bar] > close_arr[pivot_bar - j] or close_arr[pivot_bar] > close_arr[pivot_bar + j]:
                    is_pivot_low = False
                    break
            if is_pivot_low:
                pl_positions.insert(0, t)
                pl_vals.insert(0, close_arr[pivot_bar])
                if len(pl_positions) > 20:
                    pl_positions.pop()
                    pl_vals.pop()

            is_pivot_high = True
            for j in range(1, period + 1):
                if close_arr[pivot_bar] < close_arr[pivot_bar - j] or close_arr[pivot_bar] < close_arr[pivot_bar + j]:
                    is_pivot_high = False
                    break
            if is_pivot_high:
                ph_positions.insert(0, t)
                ph_vals.insert(0, close_arr[pivot_bar])
                if len(ph_positions) > 20:
                    ph_positions.pop()
                    ph_vals.pop()
        
        if t < 1:
            continue
        
        for ind_idx in range(n_indicators):
            src = indicator_arrays[ind_idx]
            if np.isnan(src[t]):
                continue
            
            bull_reg = False
            bull_hid = False
            bear_reg = False
            bear_hid = False
            
            can_check_pos = t >= 1 and ((src[t] > src[t-1]) or (close_arr[t] > close_arr[t-1]))
            if can_check_pos and len(pl_positions) > 0:
                for x in range(min(max_pivots, len(pl_positions))):
                    pos = pl_positions[x]
                    if pos == 0: break
                    length = t - pos + period
                    if length > max_bars: break
                    if length > 5 and t >= length:
                        ss = src[t - startpoint]; se = src[t - length] if (t - length) >= 0 else np.nan
                        ps = close_arr[t - startpoint]; pe = pl_vals[x]
                        if np.isnan(ss) or np.isnan(se): continue
                        is_reg = (ss > se) and (ps < pe)
                        is_hid = (ss < se) and (ps > pe)
                        if is_reg or is_hid:
                            span = length - startpoint
                            if span <= 0: continue
                            sl_s = (ss - se) / span; sl_p = (ps - pe) / span
                            vs = ss - sl_s; vp = ps - sl_p
                            ok = True
                            for y in range(1 + startpoint, length):
                                bb = t - y
                                if bb < 0 or src[bb] < vs or close_arr[bb] < vp: ok = False; break
                                vs -= sl_s; vp -= sl_p
                            if ok:
                                if is_reg: bull_reg = True
                                if is_hid: bear_hid = True
                                break
            
            can_check_neg = t >= 1 and ((src[t] < src[t-1]) or (close_arr[t] < close_arr[t-1]))
            if can_check_neg and len(ph_positions) > 0:
                for x in range(min(max_pivots, len(ph_positions))):
                    pos = ph_positions[x]
                    if pos == 0: break
                    length = t - pos + period
                    if length > max_bars: break
                    if length > 5 and t >= length:
                        ss = src[t - startpoint]; se = src[t - length] if (t - length) >= 0 else np.nan
                        ps = close_arr[t - startpoint]; pe = ph_vals[x]
                        if np.isnan(ss) or np.isnan(se): continue
                        is_reg = (ss < se) and (ps > pe)
                        is_hid = (ss > se) and (ps < pe)
                        if is_reg or is_hid:
                            span = length - startpoint
                            if span <= 0: continue
                            sl_s = (ss - se) / span; sl_p = (ps - pe) / span
                            vs = ss - sl_s; vp = ps - sl_p
                            ok = True
                            for y in range(1 + startpoint, length):
                                bb = t - y
                                if bb < 0 or src[bb] > vs or close_arr[bb] > vp: ok = False; break
                                vs -= sl_s; vp -= sl_p
                            if ok:
                                if is_reg: bear_reg = True
                                if is_hid: bull_hid = True
                                break
            
            bits = 0
            if bull_reg: bits |= 1
            if bull_hid: bits |= 2
            if bear_reg: bits |= 4
            if bear_hid: bits |= 8
            div_bits_arr[t, ind_idx] = bits
    
    return div_bits_arr

# ============================================
# CÁLCULO MEDIAS MÓVILES v8.1 — 16 FAMILIAS (Pine-faithful)
# ============================================

def calc_ema(src, period):
    """EMA — fiel a Pine Script ta.ema()"""
    n = len(src)
    result = np.full(n, np.nan)
    k = 2.0 / (period + 1)
    result[0] = src[0]
    for i in range(1, n):
        if np.isnan(result[i-1]):
            result[i] = src[i]
        else:
            result[i] = src[i] * k + result[i-1] * (1 - k)
    return result

def calc_sma(src, period):
    """SMA"""
    n = len(src)
    result = np.full(n, np.nan)
    for i in range(period - 1, n):
        result[i] = np.mean(src[i - period + 1:i + 1])
    return result

def calc_kama(close_arr, period, fast_sc=2, slow_sc=30):
    """KAMA — fiel a Pine Script"""
    n = len(close_arr)
    result = np.full(n, np.nan)
    if period >= n: return result
    result[period - 1] = close_arr[period - 1]
    fast_k = 2.0 / (fast_sc + 1)
    slow_k = 2.0 / (slow_sc + 1)
    for i in range(period, n):
        direction = abs(close_arr[i] - close_arr[i - period])
        volatility = np.sum(np.abs(np.diff(close_arr[i - period:i + 1])))
        er = direction / volatility if volatility != 0 else 0.0
        sc = (er * (fast_k - slow_k) + slow_k) ** 2
        result[i] = result[i - 1] + sc * (close_arr[i] - result[i - 1])
    return result

def calc_zlema(close_arr, period):
    """ZLEMA — fiel a Pine Script"""
    n = len(close_arr)
    lag = (period - 1) // 2
    adjusted = np.full(n, np.nan)
    for i in range(lag, n): adjusted[i] = 2.0 * close_arr[i] - close_arr[i - lag]
    result = np.full(n, np.nan)
    k = 2.0 / (period + 1)
    start = lag; end = start + period
    if end > n: return result
    result[end - 1] = np.mean(adjusted[start:end])
    for i in range(end, n): result[i] = adjusted[i] * k + result[i - 1] * (1 - k)
    return result

def calc_alma(close_arr, period, offset=0.85, sigma=6):
    """ALMA — fiel a Pine Script ta.alma()"""
    n = len(close_arr)
    result = np.full(n, np.nan)
    if period < 1: return result
    m = offset * (period - 1)
    s = period / sigma
    weights = np.array([np.exp(-((i - m) ** 2) / (2 * s * s)) for i in range(period)])
    w_sum = np.sum(weights)
    if w_sum == 0: return result
    weights = weights / w_sum
    for i in range(period - 1, n): result[i] = np.sum(close_arr[i - period + 1:i + 1] * weights)
    return result

def calc_dema(src, period):
    """DEMA — fiel a Pine Script"""
    e1 = calc_ema(src, period)
    n = len(src)
    e2 = np.full(n, np.nan)
    k = 2.0 / (period + 1)
    for i in range(n):
        if not np.isnan(e1[i]):
            e2[i] = e1[i] if np.isnan(e2[i-1] if i > 0 else np.nan) else e1[i] * k + e2[i-1] * (1 - k)
    return 2 * e1 - e2

def calc_tema(src, period):
    """TEMA — fiel a Pine Script"""
    e1 = calc_ema(src, period)
    n = len(src)
    k = 2.0 / (period + 1)
    e2 = np.full(n, np.nan)
    for i in range(n):
        if not np.isnan(e1[i]):
            e2[i] = e1[i] if (i == 0 or np.isnan(e2[i-1])) else e1[i] * k + e2[i-1] * (1 - k)
    e3 = np.full(n, np.nan)
    for i in range(n):
        if not np.isnan(e2[i]):
            e3[i] = e2[i] if (i == 0 or np.isnan(e3[i-1])) else e2[i] * k + e3[i-1] * (1 - k)
    return 3 * e1 - 3 * e2 + e3

def calc_jma(src, period, phase=0.0, power=2.0):
    """JMA (Jurik approximation) — fiel a Pine Script"""
    n = len(src)
    phase_ratio = 0.5 if phase < -100 else (2.5 if phase > 100 else phase / 100.0 + 1.5)
    beta = 0.45 * (period - 1) / (0.45 * (period - 1) + 2)
    alpha = beta ** power
    e0 = np.zeros(n); e1 = np.zeros(n); e2 = np.zeros(n)
    result = np.full(n, np.nan)
    e0[0] = src[0]; result[0] = src[0]
    for i in range(1, n):
        e0[i] = (1 - alpha) * src[i] + alpha * e0[i-1]
        e1[i] = (src[i] - e0[i]) * (1 - beta) + beta * e1[i-1]
        e2[i] = (e0[i] + phase_ratio * e1[i] - result[i-1]) * (1 - alpha)**2 + alpha**2 * e2[i-1]
        result[i] = result[i-1] + e2[i]
    return result

def calc_mcginley(src, period):
    """McGinley Dynamic — fiel a Pine Script"""
    n = len(src)
    result = np.full(n, np.nan); result[0] = src[0]
    for i in range(1, n):
        prev = result[i-1] if not np.isnan(result[i-1]) else src[i]
        ratio = src[i] / prev if prev != 0 else 1.0
        denom = 0.6 * period * (ratio ** 4)
        result[i] = prev + (src[i] - prev) / denom if denom != 0 else prev
    return result

def calc_vidya(src, period):
    """VIDYA — fiel a Pine Script"""
    n = len(src)
    sc = 2.0 / (period + 1)
    result = np.full(n, np.nan); result[0] = src[0]
    for i in range(period, n):
        gains = np.sum(np.maximum(np.diff(src[i-period:i+1]), 0))
        losses = np.sum(np.maximum(-np.diff(src[i-period:i+1]), 0))
        total = gains + losses
        cmo = abs((gains - losses) / total) if total != 0 else 0.0
        prev = result[i-1] if not np.isnan(result[i-1]) else src[i]
        result[i] = src[i] * sc * cmo + prev * (1 - sc * cmo)
    return result

def calc_frama(src, high_arr, low_arr, period):
    """FRAMA — fiel a Pine Script"""
    n = len(src); half = period // 2
    result = np.full(n, np.nan); result[0] = src[0]
    for i in range(period, n):
        n1 = (np.max(high_arr[i-half+1:i+1]) - np.min(low_arr[i-half+1:i+1])) / half if half > 0 else 1
        n2 = (np.max(high_arr[i-period+1:i-half+1]) - np.min(low_arr[i-period+1:i-half+1])) / half if half > 0 else 1
        n3 = (np.max(high_arr[i-period+1:i+1]) - np.min(low_arr[i-period+1:i+1])) / period if period > 0 else 1
        d = (np.log(n1 + n2) - np.log(n3)) / np.log(2) if (n1+n2) > 0 and n3 > 0 else 1.0
        alpha_c = max(0.01, min(np.exp(-4.6 * (d - 1)), 1.0))
        prev = result[i-1] if not np.isnan(result[i-1]) else src[i]
        result[i] = alpha_c * src[i] + (1 - alpha_c) * prev
    return result

def calc_t3(src, period, v=0.7):
    """T3 (Tillson) — fiel a Pine Script"""
    c1 = -(v**3); c2 = 3*v**2 + 3*v**3; c3 = -6*v**2 - 3*v - 3*v**3; c4 = 1 + 3*v + v**3 + 3*v**2
    e1 = calc_ema(src, period); e2 = calc_ema(e1, period); e3 = calc_ema(e2, period)
    e4 = calc_ema(e3, period); e5 = calc_ema(e4, period); e6 = calc_ema(e5, period)
    return c1*e6 + c2*e5 + c3*e4 + c4*e3

def calc_ssmoother(src, period):
    """SuperSmoother (Ehlers) — fiel a Pine Script"""
    n = len(src)
    a = np.exp(-np.sqrt(2) * np.pi / period)
    b = 2 * a * np.cos(np.sqrt(2) * np.pi / period)
    c2 = b; c3 = -(a * a); c1 = 1 - c2 - c3
    result = np.full(n, np.nan); result[0] = src[0]
    if n > 1: result[1] = src[1]
    for i in range(2, n):
        result[i] = c1 * (src[i] + src[i-1]) / 2 + c2 * result[i-1] + c3 * result[i-2]
    return result

def calc_hma(src, period):
    """HMA — fiel a Pine Script"""
    half_len = max(period // 2, 1); sqrt_len = max(round(np.sqrt(period)), 1)
    def wma(x, p):
        s = pd.Series(x)
        return s.rolling(p).apply(lambda x: np.sum(x * np.arange(1,len(x)+1)) / np.sum(np.arange(1,len(x)+1)), raw=True).values
    diff = 2 * wma(src, half_len) - wma(src, period)
    return wma(diff, sqrt_len)

def calc_vwma(src, volume, period):
    """VWMA — fiel a Pine Script"""
    n = len(src); result = np.full(n, np.nan)
    for i in range(period - 1, n):
        sv = np.sum(src[i-period+1:i+1] * volume[i-period+1:i+1])
        v = np.sum(volume[i-period+1:i+1])
        result[i] = sv / v if v != 0 else src[i]
    return result

def calc_tenkan(high_arr, low_arr, period):
    """Tenkan — fiel a Pine Script"""
    n = len(high_arr); result = np.full(n, np.nan)
    for i in range(period - 1, n):
        result[i] = (np.max(high_arr[i-period+1:i+1]) + np.min(low_arr[i-period+1:i+1])) / 2
    return result

def calc_atr(high_arr, low_arr, close_arr, period):
    """ATR — fiel a Pine Script ta.atr()"""
    n = len(close_arr); tr = np.zeros(n)
    tr[0] = high_arr[0] - low_arr[0]
    for i in range(1, n):
        tr[i] = max(high_arr[i]-low_arr[i], abs(high_arr[i]-close_arr[i-1]), abs(low_arr[i]-close_arr[i-1]))
    atr = np.full(n, np.nan); atr[period-1] = np.mean(tr[:period])
    for i in range(period, n): atr[i] = atr[i-1] + (tr[i] - atr[i-1]) / period
    return atr

# ============================================
# MA DISPATCHER (idéntico a f_calc_ma de Pine v10.0)
# ============================================
def calc_ma(ma_type, close_arr, high_arr, low_arr, volume_arr, period, p1=0.0, p2=0.0):
    if ma_type == "NONE": return np.full(len(close_arr), np.nan)
    elif ma_type == "EMA": return calc_ema(close_arr, period)
    elif ma_type == "SMA": return calc_sma(close_arr, period)
    elif ma_type == "HMA": return calc_hma(close_arr, period)
    elif ma_type == "ALMA": return calc_alma(close_arr, period, offset=p1 if p1>0 else 0.85, sigma=p2 if p2>0 else 6)
    elif ma_type == "KAMA": return calc_kama(close_arr, period)
    elif ma_type == "ZLEMA": return calc_zlema(close_arr, period)
    elif ma_type == "DEMA": return calc_dema(close_arr, period)
    elif ma_type == "TEMA": return calc_tema(close_arr, period)
    elif ma_type == "JMA": return calc_jma(close_arr, period)
    elif ma_type == "McGinley": return calc_mcginley(close_arr, period)
    elif ma_type == "VIDYA": return calc_vidya(close_arr, period)
    elif ma_type == "FRAMA": return calc_frama(close_arr, high_arr, low_arr, period)
    elif ma_type == "T3": return calc_t3(close_arr, period, v=p1 if p1>0 else 0.7)
    elif ma_type in ("SuperSmoother", "SSmoother"): return calc_ssmoother(close_arr, period)
    elif ma_type == "VWMA": return calc_vwma(close_arr, volume_arr, period)
    elif ma_type == "Tenkan": return calc_tenkan(high_arr, low_arr, period)
    else: return calc_ema(close_arr, period)

# ============================================
# HISTÉRESIS ATR (idéntico a Pine v10.0)
# ============================================
def calc_zone_with_hysteresis(ma_fast_arr, ma_slow_arr, atr_arr, hyst_mult):
    n = len(ma_fast_arr)
    zone_bull = np.zeros(n, dtype=np.bool_)
    zone_bear = np.zeros(n, dtype=np.bool_)
    hyst_zone = 0
    for i in range(n):
        if np.isnan(ma_fast_arr[i]) or np.isnan(ma_slow_arr[i]): continue
        hyst_band = hyst_mult * atr_arr[i] if not np.isnan(atr_arr[i]) else 0.0
        if hyst_mult == 0.0:
            hyst_zone = 1 if ma_fast_arr[i] > ma_slow_arr[i] else (-1 if ma_fast_arr[i] < ma_slow_arr[i] else hyst_zone)
        else:
            if hyst_zone <= 0 and ma_fast_arr[i] > ma_slow_arr[i] + hyst_band: hyst_zone = 1
            if hyst_zone >= 0 and ma_fast_arr[i] < ma_slow_arr[i] - hyst_band: hyst_zone = -1
            if hyst_zone == 0:
                hyst_zone = 1 if ma_fast_arr[i] > ma_slow_arr[i] + hyst_band else (-1 if ma_fast_arr[i] < ma_slow_arr[i] - hyst_band else 0)
        zone_bull[i] = (hyst_zone == 1)
        zone_bear[i] = (hyst_zone == -1)
    return zone_bull, zone_bear

# ============================================
# PRE-CÁLCULO COMPLETO (v8.1: Multi-MA + Histéresis)
# ============================================
def precalculate_all_data(df_1h, preset=None, hyst_mult=0.0, symbol=None):
    n = len(df_1h)
    print(f"⚙️ Pre-calculando indicadores para {n} velas...")
    
    # preset passed directly as parameter
    fast_type, fast_len, fast_p1, fast_p2 = preset[0], preset[1], preset[2], preset[3]
    slow_type, slow_len, slow_p1, slow_p2 = preset[4], preset[5], preset[6], preset[7]
    trend_type, trend_len, trend_p1, trend_p2 = preset[8], preset[9], preset[10], preset[11]
    
    print(f"📊 Fase 1: MAs — {fast_type}({fast_len})/{slow_type}({slow_len})/{trend_type}({trend_len})")
    print(f"      Fast: {fast_type}({fast_len}) | Slow: {slow_type}({slow_len}) | Trend: {trend_type}({trend_len}) | Hyst: {hyst_mult}×ATR({HYST_ATR_LEN})")
    
    df_1h_indexed = df_1h.set_index('timestamp')
    
    df_4h_full = df_1h_indexed.resample('4h', closed='left', label='left').agg({
        'open': 'first', 'high': 'max', 'low': 'min', 'close': 'last', 'volume': 'sum'
    }).dropna()
    df_1d_full = df_1h_indexed.resample('1D', closed='left', label='left').agg({
        'open': 'first', 'high': 'max', 'low': 'min', 'close': 'last', 'volume': 'sum'
    }).dropna()
    
    tf2_trend_resolved = calc_ha_trend(df_4h_full)
    tf2_bull_resolved = tf2_trend_resolved.shift(1).reindex(df_1h_indexed.index).ffill().fillna(True).values
    tf3_trend_resolved = calc_ha_trend(df_1d_full)
    tf3_bull_resolved = tf3_trend_resolved.shift(1).reindex(df_1h_indexed.index).ffill().fillna(True).values
    
    close_arr = df_1h['close'].values.astype(np.float64)
    high_arr = df_1h['high'].values.astype(np.float64)
    low_arr = df_1h['low'].values.astype(np.float64)
    volume_arr = df_1h['volume'].values.astype(np.float64)
    
    # v8.1: Multi-MA por dispatcher (idéntico a Pine v10.0)
    ma_fast_arr = calc_ma(fast_type, close_arr, high_arr, low_arr, volume_arr, fast_len, fast_p1, fast_p2)
    ma_slow_arr = calc_ma(slow_type, close_arr, high_arr, low_arr, volume_arr, slow_len, slow_p1, slow_p2)
    
    # v8.1: Histéresis ATR
    atr_arr = calc_atr(high_arr, low_arr, close_arr, HYST_ATR_LEN)
    zone_bull_arr, zone_bear_arr = calc_zone_with_hysteresis(ma_fast_arr, ma_slow_arr, atr_arr, hyst_mult)
    
    # TF4: close vs Slow MA
    tf4_bull_arr = close_arr > ma_slow_arr
    tf4_bear_arr = close_arr < ma_slow_arr
    
    # TF5: Trend MA
    ma_trend_arr = calc_ma(trend_type, close_arr, high_arr, low_arr, volume_arr, trend_len, trend_p1, trend_p2)
    tf5_bull_resolved = np.where(np.isnan(ma_trend_arr), False, close_arr > ma_trend_arr)
    tf5_bear_resolved = np.where(np.isnan(ma_trend_arr), False, close_arr < ma_trend_arr)
    
    print(f"✅ Fase 1 completada")
    print(f"⚙️ Fase 2: Simulando forward testing (forming para TF2/TF3)...")
    
    filters_forming_arr = np.zeros(n, dtype=np.uint32)
    filters_resolved_arr = np.zeros(n, dtype=np.uint32)
    
    for bar_idx in range(100, n):
        df_until_now = df_1h.iloc[:bar_idx+1].copy()
        df_4h = resample_to_timeframe(df_until_now, "4h")
        df_1d = resample_to_timeframe(df_until_now, "1d")
        tf1_bull = calc_ha_trend(df_until_now).iloc[-1] if len(df_until_now) > 1 else True
        tf2_trend = calc_ha_trend(df_4h)
        tf2_bull_forming = tf2_trend.iloc[-1] if len(tf2_trend) > 0 else True
        tf3_trend = calc_ha_trend(df_1d)
        tf3_bull_forming = tf3_trend.iloc[-1] if len(tf3_trend) > 0 else True
        
        tf4_bull = tf4_bull_arr[bar_idx]
        tf4_bear = tf4_bear_arr[bar_idx]
        tf5_bull = tf5_bull_resolved[bar_idx]
        tf5_bear = tf5_bear_resolved[bar_idx]
        
        f_forming = 0
        if tf1_bull: f_forming |= (1 << 0)
        if tf2_bull_forming: f_forming |= (1 << 1)
        if tf3_bull_forming: f_forming |= (1 << 2)
        if tf4_bull: f_forming |= (1 << 3)
        if tf5_bull: f_forming |= (1 << 4)
        if tf4_bear: f_forming |= (1 << 11)
        if tf5_bear: f_forming |= (1 << 12)
        filters_forming_arr[bar_idx] = f_forming
        
        f_resolved = 0
        if tf1_bull: f_resolved |= (1 << 0)
        if tf2_bull_resolved[bar_idx]: f_resolved |= (1 << 1)
        if tf3_bull_resolved[bar_idx]: f_resolved |= (1 << 2)
        if tf4_bull: f_resolved |= (1 << 3)
        if tf5_bull: f_resolved |= (1 << 4)
        if tf4_bear: f_resolved |= (1 << 11)
        if tf5_bear: f_resolved |= (1 << 12)
        filters_resolved_arr[bar_idx] = f_resolved
        
        if bar_idx % 2000 == 0:
            print(f"   Vela {bar_idx}/{n}...")
    
    print(f"⚙️ Calculando divergencias (Pine-faithful)...")
    rsi_full = calc_rsi(df_1h['close'], DIV_RSI_LEN).values
    macd_line_full, macd_hist_full = calc_macd(df_1h['close'], DIV_MACD_FAST, DIV_MACD_SLOW, DIV_MACD_SIGNAL)
    macd_line_full = macd_line_full.values
    macd_hist_full = macd_hist_full.values
    stoch_full = calc_stochastic(df_1h['high'], df_1h['low'], df_1h['close'], DIV_STOCH_K, DIV_STOCH_D, DIV_STOCH_SMOOTH).values
    vwmacd_full = calc_vwmacd(df_1h['close'], df_1h['volume'], DIV_VWMACD_FAST, DIV_VWMACD_SLOW).values
    cmf_full = calc_cmf(df_1h['high'], df_1h['low'], df_1h['close'], df_1h['volume'], DIV_CMF_LEN).values
    cci_full = calc_cci(df_1h['high'], df_1h['low'], df_1h['close'], DIV_CCI_LEN).values
    mom_full = calc_momentum(df_1h['close'], DIV_MOM_LEN).values
    
    indicators = {
        'rsi': rsi_full, 'macd_hist': macd_hist_full, 'macd_line': macd_line_full,
        'stoch': stoch_full, 'vwmacd': vwmacd_full, 'cmf': cmf_full,
        'cci': cci_full, 'mom': mom_full
    }
    
    div_bits_arr = precalculate_divergences_pine_faithful(
        close_arr, high_arr, low_arr, indicators,
        n, DIV_PIVOT_PERIOD, DIV_MAX_PIVOTS, DIV_MAX_BARS
    )
    
    ind_names = ["RSI", "MACD_H", "MACD_L", "STOCH", "VWMACD", "CMF", "CCI", "MOM"]
    print(f"📊 Divergencias detectadas:")
    print(f"   {'Ind':<8} {'BullR':>6} {'BullH':>6} {'BearR':>6} {'BearH':>6}")
    for ii, name in enumerate(ind_names):
        br = int(np.sum((div_bits_arr[100:, ii] & 1) > 0))
        bh = int(np.sum((div_bits_arr[100:, ii] & 2) > 0))
        ber = int(np.sum((div_bits_arr[100:, ii] & 4) > 0))
        beh = int(np.sum((div_bits_arr[100:, ii] & 8) > 0))
        print(f"   {name:<8} {br:>6} {bh:>6} {ber:>6} {beh:>6}")
    
    return {
        'close': close_arr, 'high': high_arr, 'low': low_arr,
        'open': df_1h['open'].values.astype(np.float64),
        'volume': volume_arr,
        'ma_trend': ma_trend_arr,
        'timestamps': df_1h['timestamp'].values,
        'zone_bull': zone_bull_arr, 'zone_bear': zone_bear_arr,
        'ema_fast': ma_fast_arr, 'ema_slow': ma_slow_arr,
        'filters_forming': filters_forming_arr, 'filters_resolved': filters_resolved_arr,
        'div_bits': div_bits_arr,
    }

# ============================================
# DECODE CONFIG (idéntico al lab)
# ============================================

def decode_config(config_id):
    exit_mask = config_id & 0xF
    entry_mask = (config_id >> 4) & 0x1F
    div_entry_mode = (config_id >> 9) & 0x3
    div_exit = (config_id >> 11) & 0x1
    div_type = (config_id >> 12) & 0x3
    div_ind_mask = (config_id >> 14) & 0xFF
    cancel_tf = (config_id >> 22) & 0x1
    use_ts = (config_id >> 23) & 0x1
    reg_inv = (config_id >> 24) & 0x1
    hid_inv = (config_id >> 25) & 0x1
    
    entry_tfs = []
    if entry_mask & 1: entry_tfs.append("TF1")
    if entry_mask & 2: entry_tfs.append("TF2")
    if entry_mask & 4: entry_tfs.append("TF3")
    if entry_mask & 8: entry_tfs.append("TF4")
    if entry_mask & 16: entry_tfs.append("TF5")
    
    exit_tfs = []
    if exit_mask & 1: exit_tfs.append("TF1")
    if exit_mask & 2: exit_tfs.append("TF2")
    if exit_mask & 4: exit_tfs.append("TF3")
    if exit_mask & 8: exit_tfs.append("TF4")
    if exit_mask == 0: exit_tfs.append("ZONA")
    
    ind_names = ["RSI", "MACD_H", "MACD_L", "STOCH", "VWMACD", "CMF", "CCI", "MOM"]
    indicators = [ind_names[i] for i in range(8) if (div_ind_mask >> i) & 1]
    
    variant_map = {(0,0): "FIX", (0,1): "ORIGINAL", (1,1): "ALLINV", (1,0): "REGINV"}
    variant_str = variant_map.get((reg_inv, hid_inv), "?")
    
    return {
        'exit_mask': exit_mask, 'entry_mask': entry_mask,
        'div_entry_mode': div_entry_mode, 'div_exit': div_exit,
        'div_type': div_type, 'div_ind_mask': div_ind_mask,
        'cancel_tf': cancel_tf, 'use_ts': use_ts,
        'reg_inv': reg_inv, 'hid_inv': hid_inv,
        'entry_tfs': entry_tfs, 'exit_tfs': exit_tfs,
        'div_indicators': indicators,
        'div_mode_str': ["OFF", "CONTEXTUAL", "OR"][div_entry_mode],
        'div_type_str': ["NONE", "REGULAR", "HIDDEN", "BOTH"][div_type],
        'cancel_str': "TF" if cancel_tf else "OFF",
        'ts_str': "TS" if use_ts else "SL_FIJO",
        'n_entry_tfs': bin(entry_mask).count('1'),
        'variant': variant_str,
    }

def encode_config_id(entry_mask, exit_mask, div_entry_mode, div_exit,
                     div_type, div_ind_mask, cancel_tf, use_ts, reg_inv, hid_inv):
    """Inverse of decode_config. Packs individual params into 26-bit CONFIG_ID."""
    cfg = (exit_mask & 0xF)
    cfg |= (entry_mask & 0x1F) << 4
    cfg |= (div_entry_mode & 0x3) << 9
    cfg |= (div_exit & 0x1) << 11
    cfg |= (div_type & 0x3) << 12
    cfg |= (div_ind_mask & 0xFF) << 14
    cfg |= (cancel_tf & 0x1) << 22
    cfg |= (use_ts & 0x1) << 23
    cfg |= (reg_inv & 0x1) << 24
    cfg |= (hid_inv & 0x1) << 25
    return cfg

# ============================================
# ENGINE — Traducción LITERAL del Numba engine a Python
# con registro trade-by-trade
# ============================================

def run_single_config(data, cfg_id):
    cfg = decode_config(cfg_id)
    exit_mask = cfg['exit_mask']
    entry_mask = cfg['entry_mask']
    div_entry_mode = cfg['div_entry_mode']
    div_exit = cfg['div_exit']
    div_type = cfg['div_type']
    div_ind_mask = cfg['div_ind_mask']
    cancel_tf = cfg['cancel_tf']
    use_ts = cfg['use_ts']
    reg_inv = cfg['reg_inv']
    hid_inv = cfg['hid_inv']
    
    close_arr = data['close']
    high_arr = data['high']
    low_arr = data['low']
    timestamps = data['timestamps']
    zone_bull_arr = data['zone_bull']
    zone_bear_arr = data['zone_bear']
    filters_forming_arr = data['filters_forming']
    filters_resolved_arr = data['filters_resolved']
    div_bits_arr = data['div_bits']
    
    n_bars = len(close_arr)
    timestamps_i64 = timestamps.astype('datetime64[ms]').astype(np.int64)
    
    # State variables (idénticas al Numba engine)
    position = 0
    entry_price = 0.0
    entry_bar = 0
    entry_filters_forming = 0
    sl_level = 0.0
    
    pnl = 0.0
    peak_pnl = 0.0
    max_dd = 0.0
    gross_profit = 0.0
    gross_loss = 0.0
    
    div_ctx_bull = False
    div_ctx_bear = False
    last_zone_bull = False
    
    # Pine-faithful: entries use div from PREVIOUS bar
    div_bull_now_saved = False
    div_bear_now_saved = False
    
    cooldown_until = 0
    
    entry_tf_count = 0
    for bit in range(5):
        if (entry_mask >> bit) & 1:
            entry_tf_count += 1
    
    exit_tf_count = 0
    for bit in range(4):
        if (exit_mask >> bit) & 1:
            exit_tf_count += 1
    
    trades = []
    entry_div_ctx_str = ""
    
    for t in range(100, n_bars):
        z_bull = zone_bull_arr[t]
        z_bear = zone_bear_arr[t]
        f_forming = int(filters_forming_arr[t])
        f_resolved = int(filters_resolved_arr[t])
        
        close_p = close_arr[t]
        high_p = high_arr[t]
        low_p = low_arr[t]
        
        # Pine-faithful: save previous bar's div state for entry evaluation
        prev_div_bull_now = div_bull_now_saved
        prev_div_bear_now = div_bear_now_saved
        
        # Phase 1: Zone change resets (uses current bar's zone)
        zone_changed_to_bear = z_bear and last_zone_bull
        zone_changed_to_bull = z_bull and not last_zone_bull
        
        if zone_changed_to_bear:
            div_ctx_bull = False
        if zone_changed_to_bull:
            div_ctx_bear = False
        
        # Phase 2: div_ctx update from PREVIOUS bar's div_raw (Pine L.447-452)
        if prev_div_bull_now:
            div_ctx_bull = True
            div_ctx_bear = False
        if prev_div_bear_now:
            div_ctx_bear = True
            div_ctx_bull = False
        
        # Snapshot div_ctx for entry evaluation
        entry_div_ctx_bull = div_ctx_bull
        entry_div_ctx_bear = div_ctx_bear
        
        last_zone_bull = z_bull
        
        # Phase 3: Calculate divergence for CURRENT bar (Pine isconfirmed)
        div_bull_now = False
        div_bear_now = False
        
        if div_type > 0 and div_ind_mask > 0:
            net_div_score = 0
            for ind in range(8):
                if not (div_ind_mask & (1 << ind)):
                    continue
                bits = div_bits_arr[t, ind]
                ind_bull = False
                ind_bear = False
                if div_type == 1:  # REGULAR only
                    if reg_inv == 0:
                        ind_bull = (bits & 1) > 0
                        ind_bear = (bits & 4) > 0
                    else:
                        ind_bull = (bits & 4) > 0
                        ind_bear = (bits & 1) > 0
                elif div_type == 2:  # HIDDEN only
                    if hid_inv == 0:
                        ind_bull = (bits & 8) > 0
                        ind_bear = (bits & 2) > 0
                    else:
                        ind_bull = (bits & 2) > 0
                        ind_bear = (bits & 8) > 0
                elif div_type == 3:  # BOTH
                    if reg_inv == 0:
                        reg_bull = (bits & 1) > 0
                        reg_bear = (bits & 4) > 0
                    else:
                        reg_bull = (bits & 4) > 0
                        reg_bear = (bits & 1) > 0
                    if hid_inv == 0:
                        hid_bull = (bits & 8) > 0
                        hid_bear = (bits & 2) > 0
                    else:
                        hid_bull = (bits & 2) > 0
                        hid_bear = (bits & 8) > 0
                    ind_bull = reg_bull or hid_bull
                    ind_bear = reg_bear or hid_bear
                if ind_bull:
                    net_div_score += 1
                if ind_bear:
                    net_div_score -= 1
            # Umbral consenso = 1 (matches Pine i_div_showlimit default)
            div_bull_now = net_div_score >= 1
            div_bear_now = net_div_score <= -1
        
        # Save current bar's div_now for next bar's entry evaluation
        div_bull_now_saved = div_bull_now
        div_bear_now_saved = div_bear_now
        
        # Phase 4: Update div_ctx with CURRENT bar's div (Pine isconfirmed L.608-616)
        if div_bull_now:
            div_ctx_bull = True
        if div_bear_now:
            div_ctx_bear = True
        
        # ===== GESTIÓN DE POSICIÓN (idéntico al Numba) =====
        if position != 0:
            exit_signal = False
            cancel_signal = False
            div_exit_signal = False
            sl_exit_signal = False
            sl_emergency_signal = False
            normal_exit_signal = False
            exit_price = close_p
            
            # Trailing Stop update
            if use_ts == 1 and t > entry_bar:
                if position == 1:
                    potential_stop = low_arr[t - 1] * (1 - TS_PERCENT / 100)
                    if potential_stop > sl_level:
                        sl_level = potential_stop
                elif position == -1:
                    potential_stop = high_arr[t - 1] * (1 + TS_PERCENT / 100)
                    if sl_level == 0.0 or potential_stop < sl_level:
                        sl_level = potential_stop
            
            # P1: SL Emergency
            if position == 1:
                emerg_level = entry_price * (1 - SL_EMERGENCY_PERCENT / 100)
                if low_p <= emerg_level:
                    exit_signal = True
                    sl_exit_signal = True
                    sl_emergency_signal = True
                    exit_price = emerg_level
            elif position == -1:
                emerg_level = entry_price * (1 + SL_EMERGENCY_PERCENT / 100)
                if high_p >= emerg_level:
                    exit_signal = True
                    sl_exit_signal = True
                    sl_emergency_signal = True
                    exit_price = emerg_level
            
            # P2: SL/TS Normal
            if not exit_signal and sl_level > 0:
                if position == 1 and close_p < sl_level:
                    exit_signal = True
                    sl_exit_signal = True
                elif position == -1 and close_p > sl_level:
                    exit_signal = True
                    sl_exit_signal = True
            
            # P3: Div exit
            if not exit_signal and div_exit == 1 and div_type > 0:
                if position == 1 and div_bear_now:
                    exit_signal = True
                    div_exit_signal = True
                elif position == -1 and div_bull_now:
                    exit_signal = True
                    div_exit_signal = True
            
            # P4: TF exit
            if not exit_signal and exit_mask > 0:
                exit_count_bull = 0
                exit_count_active = 0
                for bit in range(4):
                    if (exit_mask >> bit) & 1:
                        exit_count_active += 1
                        if (f_forming >> bit) & 1:
                            exit_count_bull += 1
                if position == 1 and exit_count_active > 0 and exit_count_bull == 0:
                    exit_signal = True
                    normal_exit_signal = True
                elif position == -1 and exit_count_active > 0 and exit_count_bull == exit_count_active:
                    exit_signal = True
                    normal_exit_signal = True
            
            # P5: Zone exit
            if not exit_signal:
                if position == 1 and z_bear:
                    exit_signal = True
                    normal_exit_signal = True
                elif position == -1 and z_bull:
                    exit_signal = True
                    normal_exit_signal = True
            
            # P6: Cancel TF
            if not exit_signal and cancel_tf == 1:
                cancel_signal = False
                ts_entry_i = timestamps_i64[entry_bar]
                ts_now_i = timestamps_i64[t]
                entry_day = ts_entry_i // 86400000
                current_day = ts_now_i // 86400000
                same_daily = (entry_day == current_day)
                
                eff = entry_filters_forming
                f_now = f_forming
                # Fix fidelidad: usar resolved[t] (barra HTF actual finalizada)
                efr = int(filters_resolved_arr[t])
                
                if (entry_mask >> 1) & 1:
                    entry_4h = (ts_entry_i // 3600000) // 4
                    now_4h = (ts_now_i // 3600000) // 4
                    if entry_4h == now_4h:
                        if ((eff >> 1) & 1) != ((f_now >> 1) & 1):
                            cancel_signal = True
                    else:
                        if ((eff >> 1) & 1) != ((efr >> 1) & 1):
                            cancel_signal = True
                
                if not cancel_signal and (entry_mask >> 2) & 1:
                    if same_daily:
                        if ((eff >> 2) & 1) != ((f_now >> 2) & 1):
                            cancel_signal = True
                    else:
                        if ((eff >> 2) & 1) != ((efr >> 2) & 1):
                            cancel_signal = True
            
            # EJECUTAR SALIDA
            if exit_signal or cancel_signal:
                if position == 1:
                    trade_pnl = (exit_price - entry_price) / entry_price * 100
                else:
                    trade_pnl = (entry_price - exit_price) / entry_price * 100
                
                # Restar comisión round-trip
                trade_pnl -= COMMISSION_ROUND_TRIP
                
                pnl += trade_pnl
                if trade_pnl > 0:
                    gross_profit += trade_pnl
                else:
                    gross_loss += abs(trade_pnl)
                
                if pnl > peak_pnl:
                    peak_pnl = pnl
                dd = peak_pnl - pnl
                if dd > max_dd:
                    max_dd = dd
                
                # Determine exit reason
                if sl_emergency_signal:
                    exit_reason = "SL_EMERG"
                elif sl_exit_signal:
                    exit_reason = "SL_TS" if use_ts else "SL_FIJO"
                elif div_exit_signal:
                    exit_reason = "DIV_EXIT"
                elif cancel_signal:
                    exit_reason = "CANCEL_TF"
                elif normal_exit_signal:
                    # Distinguish TF_EXIT from ZONA_EXIT
                    if exit_mask > 0:
                        ecb = 0
                        eca = 0
                        for bit in range(4):
                            if (exit_mask >> bit) & 1:
                                eca += 1
                                if (f_forming >> bit) & 1:
                                    ecb += 1
                        if (position == 1 and ecb == 0) or (position == -1 and ecb == eca):
                            exit_reason = "TF_EXIT"
                        else:
                            exit_reason = "ZONA_EXIT"
                    else:
                        exit_reason = "ZONA_EXIT"
                else:
                    exit_reason = "UNKNOWN"
                
                dur = t - entry_bar
                
                # Entry filters detail
                tf_names = ["TF1","TF2","TF3","TF4","TF5"]
                fs = ""
                for b in range(5):
                    if (entry_mask >> b) & 1:
                        v = "B" if (filters_forming_arr[entry_bar] >> b) & 1 else "b"
                        fs += f"{tf_names[b]}={v} "
                
                trades.append({
                    'num': len(trades) + 1,
                    'side': 'L' if position == 1 else 'S',
                    'entry_date': str(pd.Timestamp(timestamps[entry_bar]))[:16],
                    'exit_date': str(pd.Timestamp(timestamps[t]))[:16],
                    'entry_price': round(entry_price, 4),
                    'exit_price': round(exit_price, 4),
                    'pnl': round(trade_pnl, 4),
                    'cumul': round(pnl, 4),
                    'bars': dur,
                    'reason': exit_reason,
                    'sl_at_exit': round(sl_level, 4),
                    'entry_filters': fs.strip(),
                    'entry_ctx': entry_div_ctx_str,
                    'zone_exit': 'B' if z_bull else 'b',
                    'div_bull': div_bull_now,
                    'div_bear': div_bear_now,
                    'max_dd': round(max_dd, 4),
                })
                
                # Post-exit context reset (idéntico al Numba)
                if position == 1:
                    div_ctx_bull = False
                else:
                    div_ctx_bear = False
                
                # Cooldown (idéntico al Numba)
                if sl_emergency_signal:
                    cooldown_until = t
                elif sl_exit_signal:
                    cooldown_until = t + COOLDOWN_BARS - 1
                elif div_exit_signal:
                    cooldown_until = t + COOLDOWN_BARS - 1
                elif cancel_signal:
                    cooldown_until = t
                
                position = 0
                entry_price = 0.0
                sl_level = 0.0
                entry_filters_forming = 0
        
        # Post-exit zone context reset (idéntico al Numba)
        if z_bear:
            div_ctx_bull = False
        if z_bull:
            div_ctx_bear = False
        
        # ===== ENTRADA (idéntico al Numba) =====
        if position == 0:
            if t <= cooldown_until:
                continue
            
            long_cond = False
            short_cond = False
            
            tf_entry_ok_bull = True
            tf_entry_ok_bear = True
            
            if (entry_mask >> 0) & 1:
                if not ((f_forming >> 0) & 1): tf_entry_ok_bull = False
                if ((f_forming >> 0) & 1): tf_entry_ok_bear = False
            if (entry_mask >> 1) & 1:
                if not ((f_forming >> 1) & 1): tf_entry_ok_bull = False
                if ((f_forming >> 1) & 1): tf_entry_ok_bear = False
            if (entry_mask >> 2) & 1:
                if not ((f_forming >> 2) & 1): tf_entry_ok_bull = False
                if ((f_forming >> 2) & 1): tf_entry_ok_bear = False
            if (entry_mask >> 3) & 1:
                if not ((f_forming >> 3) & 1): tf_entry_ok_bull = False
                if not ((f_forming >> 11) & 1): tf_entry_ok_bear = False
            if (entry_mask >> 4) & 1:
                if not ((f_forming >> 4) & 1): tf_entry_ok_bull = False
                if not ((f_forming >> 12) & 1): tf_entry_ok_bear = False
            
            # Pine-faithful: entries use div state from PREVIOUS bar
            effective_ctx_bull = entry_div_ctx_bull or prev_div_bull_now
            effective_ctx_bear = entry_div_ctx_bear or prev_div_bear_now
            
            if div_entry_mode == 0:
                if z_bull:
                    long_cond = tf_entry_ok_bull if entry_tf_count > 0 else True
                if z_bear:
                    short_cond = tf_entry_ok_bear if entry_tf_count > 0 else True
            elif div_entry_mode == 1:
                if z_bull:
                    if entry_tf_count > 0:
                        long_cond = tf_entry_ok_bull and effective_ctx_bull
                    elif exit_tf_count > 0:
                        long_cond = effective_ctx_bull
                    else:
                        long_cond = prev_div_bull_now
                if z_bear:
                    if entry_tf_count > 0:
                        short_cond = tf_entry_ok_bear and effective_ctx_bear
                    elif exit_tf_count > 0:
                        short_cond = effective_ctx_bear
                    else:
                        short_cond = prev_div_bear_now
            elif div_entry_mode == 2:
                if z_bull:
                    long_cond = (tf_entry_ok_bull or prev_div_bull_now) if entry_tf_count > 0 else True
                if z_bear:
                    short_cond = (tf_entry_ok_bear or prev_div_bear_now) if entry_tf_count > 0 else True
            
            # Gatekeeper (idéntico al Numba)
            if long_cond and exit_mask > 0:
                exit_count_bull = 0
                for bit in range(4):
                    if (exit_mask >> bit) & 1 and (f_forming >> bit) & 1:
                        exit_count_bull += 1
                if exit_count_bull == 0:
                    long_cond = False
            
            if short_cond and exit_mask > 0:
                exit_count_bull = 0
                exit_count_active = 0
                for bit in range(4):
                    if (exit_mask >> bit) & 1:
                        exit_count_active += 1
                        if (f_forming >> bit) & 1:
                            exit_count_bull += 1
                if exit_count_bull == exit_count_active:
                    short_cond = False
            
            if long_cond:
                position = 1
                entry_price = close_p
                entry_bar = t
                entry_filters_forming = f_forming
                sl_level = low_p * (1 - SL_PERCENT / 100)
                entry_div_ctx_str = f"ctx_b={div_ctx_bull} now={div_bull_now}"
            elif short_cond:
                position = -1
                entry_price = close_p
                entry_bar = t
                entry_filters_forming = f_forming
                sl_level = high_p * (1 + SL_PERCENT / 100)
                entry_div_ctx_str = f"ctx_s={div_ctx_bear} now={div_bear_now}"
    
    return trades, pnl, max_dd, gross_profit, gross_loss

# ============================================
# RUN VALIDATION (callable wrapper)
# ============================================

def run_validation(symbol, config_id, timeframe="1h", total_candles=20000,
                   preset=None, hyst_mult=0.0, df_raw=None):
    """
    Run full validation pipeline. Returns structured results.
    If df_raw is provided, skips download. If preset is None, uses first symbol preset.
    """
    c = decode_config(config_id)

    if df_raw is None:
        df_raw = fetch_all_candles(symbol, timeframe, total_candles)
        if df_raw is None:
            return None

    if preset is None:
        zone_presets = SYMBOL_ZONE_PRESETS.get(symbol, [])
        if not zone_presets:
            return None
        preset = zone_presets[0]

    data = precalculate_all_data(df_raw, preset=preset, hyst_mult=hyst_mult, symbol=symbol)

    t0 = time.time()
    trades, total_pnl, max_dd, gp, gl = run_single_config(data, config_id)
    elapsed = time.time() - t0

    trades_df = pd.DataFrame(trades) if trades else pd.DataFrame()
    pf = gp / gl if gl > 0 else 999.0

    return {
        'trades': trades,
        'trades_df': trades_df,
        'total_pnl': total_pnl,
        'max_dd': max_dd,
        'gross_profit': gp,
        'gross_loss': gl,
        'profit_factor': pf,
        'data': data,
        'config_decoded': c,
        'df_raw': df_raw,
        'preset': preset,
        'hyst_mult': hyst_mult,
        'elapsed': elapsed,
    }

# ============================================
# MAIN
# ============================================

if __name__ == "__main__":
    c = decode_config(CONFIG_ID)
    print(f"{'='*70}")
    print(f"🔍 VALIDADOR v6.3 — {SYMBOL} — Config {CONFIG_ID}")
    print(f"{'='*70}")
    print(f"Entry: {'+'.join(c['entry_tfs']) or 'ZONA'} ({c['n_entry_tfs']} TFs)")
    print(f"Exit:  {'+'.join(c['exit_tfs'])}")
    print(f"Div:   Entry={c['div_mode_str']}, Exit={'ON' if c['div_exit'] else 'OFF'}, Type={c['div_type_str']}")
    print(f"Inds:  {'+'.join(c['div_indicators'])}")
    print(f"Cancel: {c['cancel_str']} | SL: {c['ts_str']}")
    print(f"Commission: {COMMISSION_ROUND_TRIP}% round-trip")
    print(f"{'='*70}")

    zone_presets = SYMBOL_ZONE_PRESETS.get(SYMBOL, [])
    if not zone_presets:
        print(f'⚠️ Sin presets para {SYMBOL}')
        sys.exit(1)
    _preset = zone_presets[0]
    _hyst = 0.0

    result = run_validation(SYMBOL, CONFIG_ID, TIMEFRAME, TOTAL_CANDLES,
                            preset=_preset, hyst_mult=_hyst)
    if result is None:
        print("ERROR: Validación fallida")
        sys.exit(1)

    trades = result['trades']
    total_pnl = result['total_pnl']
    max_dd = result['max_dd']
    gp = result['gross_profit']
    gl = result['gross_loss']
    data = result['data']
    elapsed = result['elapsed']
    pf = result['profit_factor']

    print(f"\n✅ Simulación completada en {elapsed:.1f}s")
    print(f"\n{'='*70}")
    print(f"📊 RESULTADOS: {len(trades)} trades | PnL: {total_pnl:+.2f}% | MaxDD: {max_dd:.2f}%")
    print(f"   PF: {pf:.2f} | Gross Profit: {gp:.2f}% | Gross Loss: {gl:.2f}%")
    print(f"{'='*70}")

    if trades:
        tdf = pd.DataFrame(trades)
        w = tdf[tdf['pnl'] > 0]
        l = tdf[tdf['pnl'] <= 0]

        print(f"\nWR: {len(w)}/{len(trades)} = {len(w)/len(trades)*100:.1f}%")
        if len(w) > 0: print(f"Avg Win: {w['pnl'].mean():+.2f}%")
        if len(l) > 0: print(f"Avg Loss: {l['pnl'].mean():+.2f}%")
        print(f"Max Win: {tdf['pnl'].max():+.2f}% | Max Loss: {tdf['pnl'].min():+.2f}%")
        print(f"Avg Duration: {tdf['bars'].mean():.1f} bars ({tdf['bars'].mean()/24:.1f} days)")

        print(f"\nExit Reasons:")
        for r, cnt in tdf['reason'].value_counts().items():
            ap = tdf[tdf['reason'] == r]['pnl'].mean()
            print(f"  {r}: {cnt} ({cnt/len(trades)*100:.0f}%) | Avg: {ap:+.2f}%")

        print(f"\nSides:")
        for s in ['L', 'S']:
            sub = tdf[tdf['side'] == s]
            if len(sub) > 0:
                sw = sub[sub['pnl'] > 0]
                print(f"  {s}: {len(sub)} trades | PnL: {sub['pnl'].sum():+.2f}% | WR: {len(sw)/len(sub)*100:.0f}%")

        print(f"\nDuration:")
        for lb, lo, hi in [("1 bar", 1, 1), ("2-5", 2, 5), ("6-24", 6, 24), ("1-7d", 25, 168), (">7d", 169, 99999)]:
            sub = tdf[(tdf['bars'] >= lo) & (tdf['bars'] <= hi)]
            if len(sub) > 0:
                print(f"  {lb}: {len(sub)} trades | Avg: {sub['pnl'].mean():+.2f}%")

        # Train/Test split info
        n_bars = len(data['close'])
        train_end = int(n_bars * 0.75)
        train_trades = tdf[tdf['entry_date'] <= str(pd.Timestamp(data['timestamps'][train_end]))[:16]]
        test_trades = tdf[tdf['entry_date'] > str(pd.Timestamp(data['timestamps'][train_end]))[:16]]
        print(f"\nTrain/Test Split (75/25):")
        print(f"  Train: {len(train_trades)} trades | PnL: {train_trades['pnl'].sum():+.2f}%")
        print(f"  Test:  {len(test_trades)} trades | PnL: {test_trades['pnl'].sum():+.2f}%")

        # First and last trades
        print(f"\n{'='*70}")
        print(f"📋 PRIMEROS 20 TRADES:")
        print(f"{'='*70}")
        for _, tr in tdf.head(20).iterrows():
            print(f"  #{tr['num']:3d} {tr['side']} {tr['entry_date']} → {tr['exit_date']} "
                  f"| {tr['bars']:3d}b | {tr['pnl']:+6.2f}% | {tr['reason']:10s} | cum:{tr['cumul']:+.2f}%")

        print(f"\n📋 ÚLTIMOS 20 TRADES:")
        for _, tr in tdf.tail(20).iterrows():
            print(f"  #{tr['num']:3d} {tr['side']} {tr['entry_date']} → {tr['exit_date']} "
                  f"| {tr['bars']:3d}b | {tr['pnl']:+6.2f}% | {tr['reason']:10s} | cum:{tr['cumul']:+.2f}%")

        # Save CSV
        outdir = "validacion_v6_5_FIX"
        os.makedirs(outdir, exist_ok=True)
        outf = f"{outdir}/trades_{SYMBOL.replace('/','')}_cfg{CONFIG_ID}.csv"
        tdf.to_csv(outf, index=False)
        print(f"\n💾 CSV: {outf}")

    # Sanity checks
    print(f"\n{'='*70}")
    print(f"🔍 SANITY CHECKS:")
    print(f"{'='*70}")
    if trades:
        tdf = pd.DataFrame(trades)

        # 1. Overlap check
        overlaps = 0
        for i in range(1, len(tdf)):
            if tdf.iloc[i]['entry_date'] < tdf.iloc[i-1]['exit_date']:
                overlaps += 1
                if overlaps <= 5:
                    print(f"  ⚠️ OVERLAP: #{tdf.iloc[i]['num']} entra antes de que #{tdf.iloc[i-1]['num']} salga")
        if overlaps == 0:
            print(f"  ✅ Sin overlaps")
        elif overlaps > 5:
            print(f"  ⚠️ ... y {overlaps-5} más")

        # 2. PnL consistency
        errs = 0
        for _, tr in tdf.iterrows():
            if tr['entry_price'] == 0:
                continue
            if tr['side'] == 'L':
                expected = (tr['exit_price'] - tr['entry_price']) / tr['entry_price'] * 100 - 0.10
            else:
                expected = (tr['entry_price'] - tr['exit_price']) / tr['entry_price'] * 100 - 0.10
            if abs(expected - tr['pnl']) > 0.01:
                errs += 1
                if errs <= 3:
                    print(f"  ⚠️ PnL mismatch #{tr['num']}: calc={expected:.4f} vs stored={tr['pnl']:.4f}")
        if errs == 0:
            print(f"  ✅ PnL consistente")

        # 3. Max streak
        streak = 0; max_streak = 0
        for _, tr in tdf.iterrows():
            if tr['pnl'] <= 0: streak += 1; max_streak = max(max_streak, streak)
            else: streak = 0
        print(f"  📊 Max racha perdedora: {max_streak}")

        # 4. Compare with lab
        print(f"\n  📊 VALIDADOR: {len(tdf)} trades | PnL: {total_pnl:+.2f}% | MaxDD: {max_dd:.2f}%")
        print(f"  📊 (Comparar con ranking del lab para esta config)")

    print(f"\n✅ Validación completada")
