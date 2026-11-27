import importlib.util
from pathlib import Path

spec = importlib.util.spec_from_file_location(
    "sim_plc", Path(__file__).resolve().parents[1] / "plc-simulator" / "sim_plc.py"
)
sim_plc = importlib.util.module_from_spec(spec)
spec.loader.exec_module(sim_plc)


def test_simulator_start_run_and_sort():
    sim = sim_plc.SortingLineSimulator()
    assert sim.system_state == 0

    # Start line
    out = sim.step(cmd_start=True, cmd_stop=False, cmd_reset=False, sim_fault=False)
    assert out["nSystemState"] == 10
    assert out["bConveyorMain"] is True

    # Two more ticks complete a 3-tick sorting cycle (1 item sorted)
    sim.step(False, False, False, False)
    out = sim.step(False, False, False, False)
    assert out["nTotalCount"] == 1
    assert out["nSortedACount"] + out["nSortedBCount"] == 1


def test_simulator_fault_and_reset_interlock():
    sim = sim_plc.SortingLineSimulator()
    sim.step(cmd_start=True, cmd_stop=False, cmd_reset=False, sim_fault=False)

    # Trigger fault
    out = sim.step(cmd_start=False, cmd_stop=False, cmd_reset=False, sim_fault=True)
    assert out["nSystemState"] == 99
    assert out["bConveyorMain"] is False

    # Start command must be ignored while in FAULT
    out = sim.step(cmd_start=True, cmd_stop=False, cmd_reset=False, sim_fault=False)
    assert out["nSystemState"] == 99

    # Reset returns to IDLE (0)
    out = sim.step(cmd_start=False, cmd_stop=False, cmd_reset=True, sim_fault=False)
    assert out["nSystemState"] == 0