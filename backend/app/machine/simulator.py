import asyncio
import logging
from typing import Dict, Any, Optional
from app.machine.controller import MachineController
from app.websocket.manager import ws_manager

logger = logging.getLogger("textile_machine.simulator")


class SimulatorMachineController(MachineController):
    """
    High-fidelity machine simulator for 3D CNC Textile Thread/Needle Insertion.
    Simulates stepper movements, limit homing, needle strokes, and safety interlocks.
    """

    def __init__(self):
        self.is_connected: bool = True
        self.is_homed: bool = True
        self.is_busy: bool = False
        self.is_paused: bool = False
        self.is_emergency_stopped: bool = False
        
        # Coordinates in mm
        self.current_x: float = 0.0
        self.current_y: float = 0.0
        self.current_z: float = 25.0  # Safe home Z height
        
        # Machine Limits (mm)
        self.max_x: float = 500.0
        self.max_y: float = 500.0
        self.max_z: float = 100.0
        self.safe_z: float = 25.0
        self.insert_z: float = 5.0

        # State tracking
        self.operation: str = "IDLE"  # IDLE, MOVING, HOMING, INSERTING, PAUSED, STOPPED
        self.current_hole_label: Optional[str] = None
        
        # Simulation parameters
        self.simulated_speed_factor: float = 1.0  # Speed multiplier for testing
        self.force_fail_labels: set = set()  # Hole labels configured to fail on first try for testing retry

    async def connect(self, port: Optional[str] = None, baudrate: int = 115200) -> bool:
        self.is_connected = True
        self.is_emergency_stopped = False
        self.operation = "READY"
        logger.info("Machine Simulator connected.")
        await ws_manager.broadcast("MACHINE_CONNECTED", {
            "mode": "SIMULATION",
            "status": "READY",
            "position": self.get_position()
        })
        return True

    async def disconnect(self) -> None:
        self.is_connected = False
        self.operation = "DISCONNECTED"
        logger.info("Machine Simulator disconnected.")
        await ws_manager.broadcast("MACHINE_DISCONNECTED", {
            "mode": "SIMULATION",
            "status": "DISCONNECTED"
        })

    async def home(self) -> bool:
        if not self.is_connected:
            raise RuntimeError("Machine not connected")

        self.is_busy = True
        self.operation = "HOMING"
        await ws_manager.broadcast("MACHINE_MOVING", {
            "operation": "HOMING",
            "target": {"x": 0.0, "y": 0.0, "z": self.safe_z}
        })

        # Simulate homing motion
        await asyncio.sleep(0.4 / self.simulated_speed_factor)
        self.current_x = 0.0
        self.current_y = 0.0
        self.current_z = self.safe_z
        self.is_homed = True
        self.is_busy = False
        self.operation = "READY"

        await ws_manager.broadcast("MACHINE_READY", {
            "status": "READY",
            "position": self.get_position()
        })
        return True

    async def move_to(self, x: float, y: float, z: Optional[float] = None, speed: Optional[float] = None) -> bool:
        if not self.is_connected:
            raise RuntimeError("Machine is not connected")
        if self.is_emergency_stopped:
            raise RuntimeError("Machine is in Emergency Stop state. Home or reset first.")

        target_z = z if z is not None else self.safe_z

        # Bounds check
        if not (0.0 <= x <= self.max_x and 0.0 <= y <= self.max_y and 0.0 <= target_z <= self.max_z):
            raise ValueError(f"Target coordinates ({x}, {y}, {target_z}) exceed machine limits")

        self.is_busy = True
        self.operation = "MOVING"

        # Intermediate step simulation for smooth UI telemetry
        steps = 4
        start_x, start_y, start_z = self.current_x, self.current_y, self.current_z

        for i in range(1, steps + 1):
            if self.is_emergency_stopped:
                break
            
            # Linear interpolation
            t = i / steps
            self.current_x = round(start_x + (x - start_x) * t, 2)
            self.current_y = round(start_y + (y - start_y) * t, 2)
            self.current_z = round(start_z + (target_z - start_z) * t, 2)

            await ws_manager.broadcast("MACHINE_POSITION", {
                "position": self.get_position(),
                "operation": "MOVING",
                "hole": self.current_hole_label
            })
            await asyncio.sleep(0.08 / self.simulated_speed_factor)

        self.current_x = round(x, 2)
        self.current_y = round(y, 2)
        self.current_z = round(target_z, 2)
        self.is_busy = False
        self.operation = "IN_POSITION"

        return True

    async def insert_thread(self) -> Dict[str, Any]:
        """Simulates lowering needle, inserting thread, and retracting to safe height."""
        if not self.is_connected:
            raise RuntimeError("Machine not connected")

        self.is_busy = True
        self.operation = "INSERTING"
        await ws_manager.broadcast("MACHINE_MOVING", {
            "operation": "INSERTING",
            "position": self.get_position(),
            "hole": self.current_hole_label
        })

        # 1. Lower to insert Z
        self.current_z = self.insert_z
        await asyncio.sleep(0.25 / self.simulated_speed_factor)

        # 2. Thread insertion actuation
        await asyncio.sleep(0.3 / self.simulated_speed_factor)

        # 3. Retract to safe Z
        self.current_z = self.safe_z
        await asyncio.sleep(0.2 / self.simulated_speed_factor)

        self.is_busy = False
        self.operation = "READY"

        return {
            "status": "INSERTION_COMPLETE",
            "position": self.get_position(),
            "hole": self.current_hole_label
        }

    async def stop(self) -> bool:
        self.is_emergency_stopped = True
        self.is_busy = False
        self.is_paused = False
        self.operation = "STOPPED"
        logger.warning("Software Emergency Stop triggered on Machine Simulator.")
        await ws_manager.broadcast("MACHINE_ERROR", {
            "status": "STOPPED",
            "message": "Software Emergency Stop triggered"
        })
        return True

    async def pause(self) -> bool:
        self.is_paused = True
        self.operation = "PAUSED"
        await ws_manager.broadcast("JOB_PAUSED", {
            "status": "PAUSED",
            "position": self.get_position()
        })
        return True

    async def resume(self) -> bool:
        self.is_paused = False
        self.operation = "READY"
        await ws_manager.broadcast("JOB_RESUMED", {
            "status": "READY",
            "position": self.get_position()
        })
        return True

    def get_position(self) -> Dict[str, float]:
        return {
            "x": round(self.current_x, 2),
            "y": round(self.current_y, 2),
            "z": round(self.current_z, 2)
        }

    def get_status(self) -> Dict[str, Any]:
        return {
            "is_connected": self.is_connected,
            "is_homed": self.is_homed,
            "is_busy": self.is_busy,
            "is_paused": self.is_paused,
            "is_emergency_stopped": self.is_emergency_stopped,
            "operation": self.operation,
            "current_hole": self.current_hole_label,
            "position": self.get_position(),
            "mode": "SIMULATION"
        }
