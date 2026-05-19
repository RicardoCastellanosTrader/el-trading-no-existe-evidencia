"""Tests compute_runner module (Fase D.5.2 subprocess wrapper).

Mock pid_alive + bugcheck_count + subprocess to avoid spawning real subprocesses.

Coverage:
- CR.1: launch_subprocess returns RunHandle with correct fields.
- CR.2: launch_cross_classification builds correct cmd args.
- CR.3: poll_completion RUNNING when pid alive.
- CR.4: poll_completion DONE_SUCCESS when pid dead + outputs present.
- CR.5: poll_completion DONE_PARTIAL when pid dead + outputs partial.
- CR.6: poll_completion CRASHED when pid dead + no outputs.
- CR.7: poll_completion BUGCHECK on increased Event Log count.
- CR.8: wait_for_completion returns success on first DONE_SUCCESS poll.
- CR.9: wait_for_completion returns TIMEOUT when poll_interval > timeout.
- CR.10: verify_outputs returns correct present list.
- CR.11: launch_reciclaje builds master.py command correctly.
"""
from __future__ import annotations

import time
from pathlib import Path

import pytest

import compute_runner as cr


# -----------------------------------------------------------------------------
# CR.1: launch_subprocess returns RunHandle with correct fields
# -----------------------------------------------------------------------------

def test_cr_1_launch_subprocess_returns_handle(tmp_path, monkeypatch):
    captured = {}

    class _StubPopen:
        def __init__(self, cmd, stdout, stderr, cwd=None, creationflags=0):
            captured["cmd"] = list(cmd)
            captured["cwd"] = cwd
            self.pid = 99999

    monkeypatch.setattr("subprocess.Popen", _StubPopen)
    monkeypatch.setattr(cr, "bugcheck_count", lambda h=2: 5)

    handle = cr.launch_subprocess(
        cmd=["python", "script.py", "--arg", "1"],
        log_path=str(tmp_path / "out.log"),
        err_path=str(tmp_path / "err.log"),
        expected_outputs=[str(tmp_path / "out.json")],
        label="test_label",
    )

    assert handle.pid == 99999
    assert handle.cmd == ["python", "script.py", "--arg", "1"]
    assert handle.log_path == tmp_path / "out.log"
    assert handle.err_path == tmp_path / "err.log"
    assert handle.expected_outputs == [tmp_path / "out.json"]
    assert handle.label == "test_label"
    assert handle.initial_bugcheck_count == 5
    assert captured["cmd"] == ["python", "script.py", "--arg", "1"]


# -----------------------------------------------------------------------------
# CR.2: launch_cross_classification builds correct command
# -----------------------------------------------------------------------------

def test_cr_2_launch_cross_classification_cmd(tmp_path, monkeypatch):
    captured = {}

    class _StubPopen:
        def __init__(self, cmd, stdout, stderr, cwd=None, creationflags=0):
            captured["cmd"] = list(cmd)
            self.pid = 12345

    monkeypatch.setattr("subprocess.Popen", _StubPopen)
    monkeypatch.setattr(cr, "bugcheck_count", lambda h=2: 0)

    handle = cr.launch_cross_classification(
        source="BTC",
        target="ETH",
        output_root=str(tmp_path / "ccv_btc" / "ETHUSDT_btc_classified"),
        log_path=str(tmp_path / "log"),
        err_path=str(tmp_path / "err"),
        python_exe="python_test",
        script_path="analysis_scripts/sub_frame_3a1_gmm_n_pthreshold_grid.py",
    )

    cmd = captured["cmd"]
    assert cmd[0] == "python_test"
    assert "sub_frame_3a1_gmm_n_pthreshold_grid.py" in cmd[1]
    assert "--cross-classify-source" in cmd
    assert "BTC" in cmd
    assert "--symbols" in cmd
    # Single target (per-target launch CCV precedent)
    sym_idx = cmd.index("--symbols")
    assert cmd[sym_idx + 1] == "ETH"
    assert "--output-root" in cmd
    # --cells filter MANDATORY to prevent 31-cell default catastrophic compute
    assert "--cells" in cmd
    cells_idx = cmd.index("--cells")
    assert cmd[cells_idx + 1] == "baseline"
    # Expected outputs: summary JSON at output_root root + specialist_configs
    # in cell_baseline/{target}USDT/ subdir (empirically confirmed by smoke 2026-05-13)
    assert len(handle.expected_outputs) == 2
    expected_names = [p.name for p in handle.expected_outputs]
    assert "sub_frame_3a1_summary.json" in expected_names
    assert "ETHUSDT_specialist_configs.json" in expected_names


# -----------------------------------------------------------------------------
# CR.3-CR.6: poll_completion variants
# -----------------------------------------------------------------------------

def _make_handle(tmp_path, expected_outputs=None, pid=1234):
    return cr.RunHandle(
        pid=pid,
        cmd=["python"],
        log_path=tmp_path / "log",
        err_path=tmp_path / "err",
        expected_outputs=expected_outputs or [],
        start_time=time.time(),
        initial_bugcheck_count=0,
    )


def test_cr_3_poll_completion_running(tmp_path, monkeypatch):
    monkeypatch.setattr(cr, "pid_alive", lambda pid: True)
    monkeypatch.setattr(cr, "bugcheck_count", lambda h=2: 0)
    handle = _make_handle(tmp_path)
    assert cr.poll_completion(handle) == cr.CompletionStatus.RUNNING


def test_cr_4_poll_completion_done_success(tmp_path, monkeypatch):
    out = tmp_path / "result.json"
    out.write_text("{}")
    monkeypatch.setattr(cr, "pid_alive", lambda pid: False)
    monkeypatch.setattr(cr, "bugcheck_count", lambda h=2: 0)
    handle = _make_handle(tmp_path, expected_outputs=[out])
    assert cr.poll_completion(handle) == cr.CompletionStatus.DONE_SUCCESS


def test_cr_5_poll_completion_done_partial(tmp_path, monkeypatch):
    out1 = tmp_path / "result_1.json"
    out1.write_text("{}")
    out2 = tmp_path / "result_2.json"  # not created
    monkeypatch.setattr(cr, "pid_alive", lambda pid: False)
    monkeypatch.setattr(cr, "bugcheck_count", lambda h=2: 0)
    handle = _make_handle(tmp_path, expected_outputs=[out1, out2])
    assert cr.poll_completion(handle) == cr.CompletionStatus.DONE_PARTIAL


def test_cr_6_poll_completion_crashed(tmp_path, monkeypatch):
    out = tmp_path / "result.json"  # not created
    monkeypatch.setattr(cr, "pid_alive", lambda pid: False)
    monkeypatch.setattr(cr, "bugcheck_count", lambda h=2: 0)
    handle = _make_handle(tmp_path, expected_outputs=[out])
    assert cr.poll_completion(handle) == cr.CompletionStatus.CRASHED


def test_cr_7_poll_completion_bugcheck(tmp_path, monkeypatch):
    monkeypatch.setattr(cr, "pid_alive", lambda pid: True)
    monkeypatch.setattr(cr, "bugcheck_count", lambda h=2: 5)
    handle = _make_handle(tmp_path)
    handle.initial_bugcheck_count = 4
    # bugcheck check happens first, so BUGCHECK wins over RUNNING
    assert cr.poll_completion(handle) == cr.CompletionStatus.BUGCHECK


# -----------------------------------------------------------------------------
# CR.8-CR.9: wait_for_completion
# -----------------------------------------------------------------------------

def test_cr_8_wait_for_completion_immediate_success(tmp_path, monkeypatch):
    out = tmp_path / "result.json"
    out.write_text("{}")
    monkeypatch.setattr(cr, "pid_alive", lambda pid: False)
    monkeypatch.setattr(cr, "bugcheck_count", lambda h=2: 0)
    # Avoid actual sleep
    monkeypatch.setattr(cr.time, "sleep", lambda s: None)
    handle = _make_handle(tmp_path, expected_outputs=[out])
    status = cr.wait_for_completion(handle, poll_interval=1, timeout=10)
    assert status == cr.CompletionStatus.DONE_SUCCESS


def test_cr_9_wait_for_completion_timeout(tmp_path, monkeypatch):
    # PID always alive, no outputs, no bugcheck -> stays RUNNING until timeout
    monkeypatch.setattr(cr, "pid_alive", lambda pid: True)
    monkeypatch.setattr(cr, "bugcheck_count", lambda h=2: 0)
    # Fast time progression: each sleep advances time by 10s
    fake_clock = [time.time()]
    monkeypatch.setattr(cr.time, "time", lambda: fake_clock[0])
    def _fake_sleep(s):
        fake_clock[0] += s + 1  # advance > poll_interval
    monkeypatch.setattr(cr.time, "sleep", _fake_sleep)

    handle = _make_handle(tmp_path, expected_outputs=[])
    handle.start_time = fake_clock[0]
    status = cr.wait_for_completion(handle, poll_interval=10, timeout=20)
    assert status == cr.CompletionStatus.TIMEOUT


# -----------------------------------------------------------------------------
# CR.10: verify_outputs
# -----------------------------------------------------------------------------

def test_cr_10_verify_outputs(tmp_path):
    a = tmp_path / "a.json"
    b = tmp_path / "b.json"
    c = tmp_path / "c.json"
    a.write_text("{}")
    c.write_text("{}")
    handle = _make_handle(tmp_path, expected_outputs=[a, b, c])
    all_present, present = cr.verify_outputs(handle)
    assert all_present is False
    assert set(present) == {a, c}


# -----------------------------------------------------------------------------
# CR.11: launch_reciclaje builds master.py command
# -----------------------------------------------------------------------------

def test_cr_11_launch_reciclaje_per_sym_cmd(tmp_path, monkeypatch):
    """H_B fix 2026-05-19: launch_reciclaje (multi-sym) replaced by launch_reciclaje_per_sym
    (single sym) for 2-phase isolation pattern. Test verifies per-sym cmd build with --recycle
    default + --chunk-size + optional --from-step/--to-step."""
    captured = {}

    class _StubPopen:
        def __init__(self, cmd, stdout, stderr, cwd=None, creationflags=0):
            captured["cmd"] = list(cmd)
            self.pid = 22222

    monkeypatch.setattr("subprocess.Popen", _StubPopen)
    monkeypatch.setattr(cr, "bugcheck_count", lambda h=2: 0)

    # Phase 2 pattern: from_step="regime-wf" + recycle=False (sub-test bit-exact)
    handle = cr.launch_reciclaje_per_sym(
        symbol="XRP/USDT",
        chunk_size=1_000_000,
        log_path=str(tmp_path / "log"),
        err_path=str(tmp_path / "err"),
        master_path="master.py",
        python_exe="python_test",
        from_step="regime-wf",
        recycle=False,
    )

    cmd = captured["cmd"]
    assert cmd[0] == "python_test"
    assert "master.py" in cmd
    assert "--from-step" in cmd
    assert "regime-wf" in cmd
    assert "--recycle" not in cmd  # recycle=False
    sym_idx = cmd.index("--symbols")
    assert cmd[sym_idx + 1] == "XRP/USDT"
    assert "--chunk-size" in cmd
    assert "1000000" in cmd
    # Phase 2 expected output = specialist_configs JSON
    expected_names = {p.name for p in handle.expected_outputs}
    assert "XRPUSDT_specialist_configs.json" in expected_names

    # Phase 1 pattern: to_step="lite" + recycle=True default
    captured.clear()
    handle2 = cr.launch_reciclaje_per_sym(
        symbol="ONDO/USDT",
        chunk_size=1_000_000,
        log_path=str(tmp_path / "log2"),
        err_path=str(tmp_path / "err2"),
        master_path="master.py",
        python_exe="python_test",
        to_step="lite",
    )
    cmd2 = captured["cmd"]
    assert "--to-step" in cmd2 and "lite" in cmd2
    assert "--recycle" in cmd2  # recycle=True default
    # Phase 1 expected output = presets CSV (NOT regime_wf JSON since step 4 skipped)
    expected_names2 = {p.name for p in handle2.expected_outputs}
    assert "presets_ONDOUSDT.csv" in expected_names2
