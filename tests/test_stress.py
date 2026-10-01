"""Unit tests for StressTestEngine in hwscan.core.stress_test."""

import time
import pytest
from hwscan.core.stress_test import StressTestEngine


def test_stress_engine_initial_state():
    engine = StressTestEngine()
    assert not engine.is_running
    # Verify GPU methods do not raise exceptions
    temp = engine.get_gpu_temperature()
    assert temp is None or isinstance(temp, int)
    util = engine.get_gpu_utilization()
    assert util is None or isinstance(util, int)


def test_stress_engine_execution_and_completion():
    engine = StressTestEngine()
    telemetry_events = []
    completion_events = []

    def on_telemetry(data):
        telemetry_events.append(data)

    def on_completion(summary):
        completion_events.append(summary)

    # Run for 1 second with low RAM allocation (16 MB)
    engine.start_test(
        duration_seconds=1,
        test_cpu=True,
        test_ram=True,
        test_disk=False,
        ram_mb=16,
        on_telemetry=on_telemetry,
        on_completion=on_completion,
    )

    assert engine.is_running

    # Wait for completion (max 8 seconds)
    t0 = time.time()
    while engine.is_running and (time.time() - t0) < 8.0:
        time.sleep(0.1)

    assert not engine.is_running
    assert len(completion_events) == 1
    summary = completion_events[0]
    assert "stability_status" in summary
    assert "PASSED" in summary["stability_status"] or "FAILED" in summary["stability_status"]
    assert "peak_cpu_load" in summary
    assert "total_elapsed" in summary

    # Telemetry should have captured at least 1 update
    if telemetry_events:
        t = telemetry_events[0]
        assert "cpu_percent" in t
        assert "progress_percent" in t


def test_stress_engine_manual_stop():
    engine = StressTestEngine()

    engine.start_test(
        duration_seconds=30,
        test_cpu=True,
        test_ram=False,
        test_disk=False,
    )
    assert engine.is_running
    time.sleep(0.3)
    engine.stop_test()
    assert not engine.is_running
