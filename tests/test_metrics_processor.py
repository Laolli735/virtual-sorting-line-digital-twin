import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "edge-gateway"))

from metrics_processor import validate_and_normalize


def test_valid_run_telemetry():
    raw = {
        "system_state": 10,
        "total_count": 150,
        "sorted_a": 90,
        "sorted_b": 60,
        "oee_availability": 94.567,
    }
    result = validate_and_normalize(raw)
    assert result.state_label == "RUN"
    assert result.total_count == 150
    assert result.oee_availability == 94.57

def test_total_count_reconciled_when_lower_than_branches():
    raw = {
        "system_state": 10,
        "total_count": 0,
        "sorted_a": 120,
        "sorted_b": 30,
        "oee_availability": 80.0,
    }
    result = validate_and_normalize(raw)
    assert result.total_count == 150

def test_oee_clamped_to_valid_percentage_range():
    high = validate_and_normalize({"oee_availability": 125.4})
    low = validate_and_normalize({"oee_availability": -12.0})
    assert high.oee_availability == 100.0
    assert low.oee_availability == 0.0

def test_unknown_and_fault_states():
    fault = validate_and_normalize({"system_state": 99})
    unknown = validate_and_normalize({"system_state": 777})
    assert fault.state_label == "FAULT"
    assert unknown.state_label == "UNKNOWN"
