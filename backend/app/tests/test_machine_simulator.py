import pytest
from app.machine.simulator import SimulatorMachineController


@pytest.mark.asyncio
async def test_machine_simulator_lifecycle():
    sim = SimulatorMachineController()
    sim.simulated_speed_factor = 20.0  # Fast testing

    assert sim.is_connected is True
    assert sim.is_homed is True

    # Test move
    moved = await sim.move_to(150.0, 220.0, 25.0)
    assert moved is True
    pos = sim.get_position()
    assert pos["x"] == 150.0
    assert pos["y"] == 220.0
    assert pos["z"] == 25.0

    # Test insertion stroke
    insert_res = await sim.insert_thread()
    assert insert_res["status"] == "INSERTION_COMPLETE"
    assert sim.get_position()["z"] == sim.safe_z

    # Test stop / pause / resume
    await sim.stop()
    assert sim.is_emergency_stopped is True
    assert sim.operation == "STOPPED"

    # Reset
    await sim.connect()
    assert sim.is_emergency_stopped is False
