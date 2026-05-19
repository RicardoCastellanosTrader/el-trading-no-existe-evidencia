# FASE D.1 — Automation Orchestrator Design (Path C reformulado incremental rolling)

**Date**: 2026-05-11
**Scope**: Greenfield orchestrator stub for Path C reformulado per-grupo 5 sym cross-3-options PIPELINED.
**Non-goals (this stub)**: Real compute execution. The orchestrator must not import Numba/CUDA, must not modify `master.py` / `lab_cuda.py` / `regime_walk_forward.py` / `live/*`. Dry-run only — simulates flow + manages persistent state JSON.

---

## 1. State Machine (text/ASCII)

States are parameterized by `grupo_id` (1..9 for 9 grupos of 5 sym cross-cartera 45). Each grupo cycles through 5 sequential states plus the inter-grupo transition.

```
                                   +---------------------+
                                   |   IDLE (initial)    |
                                   +----------+----------+
                                              | start(grupo=N)
                                              v
                            +------------------------------------+
                            |  RECICLAJE_GRUPO_N                 |
                            |  - reciclaje 5 sym sequential      |
                            |  - watcher: regime_wf/{sym}_       |
                            |    specialist_configs.json (5/5)   |
                            |  - auto-cleanup _parts_{sym}       |
                            +-----------------+------------------+
                                              | all 5 sym DONE primary source verified
                                              v
                            +------------------------------------+
                            |  CROSS_CLASS_GRUPO_N               |
                            |  - 3 options sequential strict:    |
                            |    (a) BTC source × 4 sym          |
                            |    (b) ETH source × 4 sym          |
                            |    (c) per-sym GMM baseline (ref)  |
                            |  - Caveat #14 SEQUENTIAL STRICT    |
                            |  - watcher: ccv_phaseN_results/    |
                            +-----------------+------------------+
                                              | all 3 options DONE
                                              v
                            +------------------------------------+
                            |  ANALYSIS_GRUPO_N                  |
                            |  - cross-15-classifications        |
                            |    matrix + best source per-sym    |
                            |  - Gate B / stable+POS evaluation  |
                            |  - emit analysis report            |
                            +-----------------+------------------+
                                              | report emitted
                                              v
                            +------------------------------------+
                            |  DEPLOYMENT_READY_GRUPO_N          |
                            |  - tier3_gate_pending = True       |
                            |  - PAUSE + REPORT Tier 3 Ricardo   |
                            |  - awaits explicit authorization   |
                            +-----------------+------------------+
                                              | Ricardo authorizes (external)
                                              v
                            +------------------------------------+
                            |  DEPLOYED_GRUPO_N                  |
                            |  - bot v2.5.0 deployment hook      |
                            |    (force-flat + transition)       |
                            |  - watcher: deployment ack         |
                            +-----------------+------------------+
                                              | deployment ack received
                                              v
                            +------------------------------------+
                            |  NEXT_GRUPO                        |
                            |  - increment grupo_actual          |
                            |  - validate grupo N+1 exists       |
                            |  - if N == 9: TERMINAL_COMPLETE    |
                            +-----------------+------------------+
                                              | grupo_actual <- N+1
                                              v
                                         (loop back to RECICLAJE_GRUPO_(N+1))
```

**Notes**:
- PIPELINED at the user-decision boundary: while `DEPLOYED_GRUPO_N` operacional on bot, `RECICLAJE_GRUPO_(N+1)` may begin (Path C reformulado spec). The orchestrator advances `grupo_actual` only after Ricardo authorizes the NEXT_GRUPO transition — pipelining is empirical/operational, not concurrent within this orchestrator process.
- Failure mode `CRASH`: any state may be interrupted. On restart, the orchestrator reads `automation_state.json` and infers resume point from `crash_recovery_resume_point`.

---

## 2. Schema `automation_state.json`

```json
{
  "schema_version": 1,
  "created_at": "2026-05-11T00:00:00Z",
  "updated_at": "2026-05-11T00:00:00Z",
  "grupo_actual": 1,
  "fase_actual": "RECICLAJE_GRUPO_N",
  "grupos": {
    "1": {
      "symbols": ["BTCUSDT", "ETHUSDT", "BNBUSDT", "XRPUSDT", "TRXUSDT"],
      "sym_done_grupo_N": [],
      "sym_pending_grupo_N": ["BTCUSDT", "ETHUSDT", "BNBUSDT", "XRPUSDT", "TRXUSDT"],
      "cross_options_done": [],
      "cross_options_pending": ["BTC_SOURCE", "ETH_SOURCE", "PER_SYM_BASELINE"],
      "analysis_report_path": null,
      "deployment_ack": false,
      "tier3_gate_pending": false
    },
    "2": { "...": "..." }
  },
  "last_completed": {
    "state": "IDLE",
    "grupo_id": null,
    "timestamp": null
  },
  "crash_recovery_resume_point": {
    "state": "IDLE",
    "grupo_id": 1,
    "context": {}
  },
  "tier3_gate_pending": false,
  "history": [
    {"ts": "...", "from": "IDLE", "to": "RECICLAJE_GRUPO_N", "grupo_id": 1, "note": "..."}
  ]
}
```

**Field semantics**:
- `grupo_actual`: int, 1..9 (or null if TERMINAL_COMPLETE).
- `fase_actual`: enum of valid states.
- `grupos[N].symbols`: declared at grupo-start time, immutable after.
- `grupos[N].sym_done_grupo_N` / `sym_pending_grupo_N`: invariant `sorted(done ∪ pending) == sorted(symbols)`.
- `grupos[N].cross_options_done` / `cross_options_pending`: subset of `{BTC_SOURCE, ETH_SOURCE, PER_SYM_BASELINE}`.
- `tier3_gate_pending` (top-level): True ⇒ orchestrator paused awaiting Ricardo Tier 3 authorization.
- `crash_recovery_resume_point`: snapshot of last consistent state pre-transition; used by `load_state()` to determine where to resume.
- `history`: append-only audit trail of transitions.

---

## 3. Transition Rules

| From state | To state | Guard |
|---|---|---|
| IDLE | RECICLAJE_GRUPO_N | `grupo_actual` set, `symbols` declared, `sym_pending` == full list |
| RECICLAJE_GRUPO_N | CROSS_CLASS_GRUPO_N | `sym_done == symbols` AND primary-source verified (Caveat #15) for each sym (`regime_wf/{sym}_specialist_configs.json` exists) |
| CROSS_CLASS_GRUPO_N | ANALYSIS_GRUPO_N | `cross_options_done == {BTC_SOURCE, ETH_SOURCE, PER_SYM_BASELINE}` AND all paths in `ccv_phaseN_results/` populated |
| ANALYSIS_GRUPO_N | DEPLOYMENT_READY_GRUPO_N | `analysis_report_path` is not None AND file exists |
| DEPLOYMENT_READY_GRUPO_N | DEPLOYED_GRUPO_N | `tier3_gate_pending == False` (Ricardo authorized externally via CLI command) |
| DEPLOYED_GRUPO_N | NEXT_GRUPO | `deployment_ack == True` |
| NEXT_GRUPO | RECICLAJE_GRUPO_(N+1) | `grupo_actual+1 <= 9` AND grupo (N+1) declared OR auto-prepared from default plan |
| NEXT_GRUPO | TERMINAL_COMPLETE | `grupo_actual == 9` |
| any | CRASH (implicit) | unhandled exception during transition |

**Validation invariants** (enforced by `transition()`):
1. Target state must be in the explicit transition table above.
2. Guards must evaluate True before commit.
3. `history` appended atomically with `save_state()` (write to temp + rename).
4. Caveat #14 sequential strict — no concurrent state transitions inside one process. CLI commands are serialized.

---

## 4. Pause / Resume Mechanics

**Pause**: User invokes CLI `--pause` OR transition to `DEPLOYMENT_READY_GRUPO_N` auto-pauses (Tier 3). State persisted before pause.

**Resume**:
1. `load_state()` reads `automation_state.json`.
2. If file missing ⇒ initialize fresh state (IDLE).
3. If file present, inspect `crash_recovery_resume_point.state`:
   - For non-CRASH last state: resume by transitioning to `fase_actual` (idempotent — already there).
   - For CRASH: inspect `crash_recovery_resume_point.context` to determine partial work. For RECICLAJE: re-check `sym_done` by verifying primary-source files; for CROSS_CLASS: re-check `cross_options_done` by verifying output paths; for ANALYSIS: re-check `analysis_report_path` existence.
4. Pattern §12 L38 verificación primary source applied at each resume — files-existence is canonical truth, JSON state is hint.

**Crash recovery resume point** is updated at two moments:
- BEFORE any transition (snapshot pre-write).
- AFTER successful state save (snapshot of new state).

A crash between these two moments is detected by `updated_at` skew vs `crash_recovery_resume_point.timestamp` mismatch.

---

## 5. Tiered Reporting Integration

Mapping per CONTEXTO §13.2 tiered-reporting model:

| Phase / event | Tier | Behavior |
|---|---|---|
| Sym i done within RECICLAJE_GRUPO_N (i < 5) | Tier 1 | Silent — append to history, save state, continue. |
| RECICLAJE_GRUPO_N complete (all 5 sym DONE) | Tier 2 | Brief log line. Auto-transition to CROSS_CLASS_GRUPO_N. |
| Each cross-option DONE within CROSS_CLASS_GRUPO_N | Tier 1 | Silent. |
| CROSS_CLASS_GRUPO_N complete (3 options DONE) | Tier 2 | Brief log line. Auto-transition to ANALYSIS_GRUPO_N. |
| ANALYSIS_GRUPO_N report emitted | Tier 2 | Brief log line. Auto-transition to DEPLOYMENT_READY_GRUPO_N. |
| DEPLOYMENT_READY_GRUPO_N reached | **Tier 3** | **PAUSE + REPORT Ricardo**. `tier3_gate_pending = True`. Orchestrator awaits explicit `--authorize-deploy <grupo_id>` CLI invocation. |
| Deployment ack received | Tier 2 | Brief log. Auto-transition to NEXT_GRUPO. |
| Unexpected failure / Caveat #14 violation / primary-source mismatch (Caveat #15) | **Tier 3** | **PAUSE + REPORT** — write detailed diagnostic JSON to `automation_state_diagnostic_<ts>.json`. |
| TERMINAL_COMPLETE (grupo 9 deployed) | Tier 3 | Final report Ricardo (deployment cross-cartera 45 complete). |

**Tier 3 PAUSE behavior**: set `tier3_gate_pending = True`, persist state, emit human-readable summary on stdout, exit 0 (non-error). External (Ricardo) must inspect, then re-invoke orchestrator with explicit authorization to clear the gate.

---

## 6. CLI Surface (stub)

```
python automation_orchestrator.py --dry-run                          # advance state machine one step (idempotent)
python automation_orchestrator.py --dry-run --simulate-grupo 1       # full grupo flow simulation (no compute)
python automation_orchestrator.py --status                            # read-only print state summary
python automation_orchestrator.py --authorize-deploy <grupo_id>       # clear tier3_gate_pending
python automation_orchestrator.py --reset                             # erase state (interactive confirm)
```

This stub MANDATORILY requires `--dry-run` for any state-mutating operation other than `--authorize-deploy` and `--reset`. Real compute hookup is out of scope (Fase D.5+).

---

## 7. References

- CONTEXTO §13.2 Caveat #13 (auto-cleanup `_parts_*`), #14 (sequential strict), #15 (primary-source verification), #16 (caveat reformulation discipline).
- `project_path_c_reformulado_2026_05_10.md` (Path C reformulated incremental rolling).
- `live/portfolio_manager.py:654-741` (§13.3 L2188 P1 leverage map RESUELTO precedent — primary source verification pattern).
- HEAD `963431c feat(gpu-cleanup-v17)` as parent commit.
