# Fase D.5.1 RECICLAJE hookup — COMPLETE 2026-05-19

## Scope

`AutomationOrchestrator.run_reciclaje_real_compute` + `compute_runner.launch_reciclaje_per_sym` + CLI `--stage RECICLAJE`.

Mirror of Fase D.5.2 CROSS_CLASS pattern adapted to per-sym sequential strict reciclaje (Caveat #14 sequential strict mandatory cross-Sub-Sesiones precedent absoluto).

## Files modified

- `automation_orchestrator.py` — new method `run_reciclaje_real_compute` (~160 LOC) + CLI `--stage RECICLAJE` + `--chunk-size` + `--from-step` + `--timeout-per-sym` args + NEXT_GRUPO → RECICLAJE auto-transition.
- `compute_runner.py` — refactor `launch_reciclaje` → `launch_reciclaje_per_sym` (single sym, full pipeline default, `--recycle` flag default True, R1 v18 chunk_size=1M default).
- `tests/test_automation_orchestrator_reciclaje.py` — 9 tests greenfield (D51.1–D51.9).

## Tests coverage (D51.1–D51.9)

| ID | Scenario | Validates |
|---|---|---|
| D51.1 | Per-sym launches + marks done on DONE_SUCCESS | Happy path + sym_done_grupo_N updated |
| D51.2 | Requires fase_actual == RECICLAJE | OrchestratorError raised on wrong state |
| D51.3 | CRASHED → Tier 3 + halt remaining | Caveat #14 sequential strict halt-on-fail |
| D51.4 | BUGCHECK → Tier 3 | TDR escalation path |
| D51.5 | DONE_PARTIAL → Tier 3 | Outputs incomplete path |
| D51.6 | DONE_SUCCESS + primary-source MISSING → Tier 3 | Caveat #15 primary-source verification |
| D51.7 | Sequential strict — once per sym | Each sym launched exactly once, no parallel |
| D51.8 | active_subprocess record lifecycle | State persisted during run + popped on success |
| D51.9 | All 5 sym DONE → Tier 2 announce | Final announce + state stays RECICLAJE (caller drives transition) |

**Result: 9/9 PASS** al primer intento. Zero regression: full orchestrator suite 59/59 PASS.

## Pattern alignment with D.5.2

| Aspect | D.5.2 CROSS_CLASS | D.5.1 RECICLAJE |
|---|---|---|
| State guard | `fase_actual == CROSS_CLASS` | `fase_actual == RECICLAJE` |
| Sequential strict | Per-target loop, halt on fail | Per-sym loop, halt on fail |
| Primary-source verify | `expected_outputs` checked by waiter | Caveat #15 explicit re-check post-success |
| State persistence | `active_subprocess[option_target]` | `active_subprocess[RECICLAJE_sym]` |
| Done marking | `mark_cross_option_done(grupo_id, option)` | `mark_sym_done(grupo_id, sym)` |
| Caller transition | reports Tier 2 → caller transitions to ANALYSIS | reports Tier 2 → caller transitions to CROSS_CLASS |

## Empirical context

R1 v18 chunk_size=1M default — cross-2-sym XRP+TRX validated 2026-05-12 cumulative (TDR 0x116 fix robust ZERO crashes cross 16h51m runtime cumulative cross-Sub-Sesiones precedent absoluto).

`--recycle` flag default True in `launch_reciclaje_per_sym` — master.py skips sym whose `regime_wf/{SYM}USDT_specialist_configs.json` exists otherwise. Default True is canonical reciclaje semantics (force re-download + re-train + re-generate + new specialists).

Per-sym timeout default 18h — empirical pace ~7K bars/h, large-bar sym BTC/ETH ~10-13h margin x1.5; small-bar Grupo 2 sym (ONDO ~8K + RENDER ~14K + POL ~12K + SEI ~22K + TAO unknown) ~2-6h margin x3-x9.

## CLI launch

```powershell
python automation_orchestrator.py --mode production --grupo 2 --stage RECICLAJE `
    --chunk-size 1000000 --poll-interval 120 --timeout-per-sym 64800 `
    --log-dir .
```

## Cross-references

- D.5.2 precedent: `analysis_scripts/fase_d_5_2_cross_class_hookup_complete_20260512_080000.md`
- D.6 ANALYSIS: `analysis_scripts/fase_d_6_analysis_complete_20260512_082500.md`
- Caveat #14: §13.2 sequential strict mandatory
- Caveat #15: §13.2 verificación primary source mandatory items
- TDR 0x116 fix: `project_crash_0x116_tdr_596_02_fix.md`
