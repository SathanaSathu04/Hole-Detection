import logging
from typing import Dict, Any, Optional
from app.machine.controller import MachineController
from app.machine.simulator import SimulatorMachineController
from app.machine.real_controller import RealMachineController

logger = logging.getLogger("textile_machine.machine_service")


class MachineService:
    def __init__(self):
        self.mode: str = "SIMULATION"
        self.controller: MachineController = SimulatorMachineController()

    async def set_mode(self, mode: str, port: Optional[str] = None, baudrate: int = 115200) -> bool:
        mode_upper = mode.upper()
        if mode_upper == "REAL":
            self.mode = "REAL"
            self.controller = RealMachineController(port=port or "COM3", baudrate=baudrate)
        else:
            self.mode = "SIMULATION"
            self.controller = SimulatorMachineController()
        return await self.controller.connect()

    async def connect(self, port: Optional[str] = None, baudrate: int = 115200) -> bool:
        return await self.controller.connect(port=port, baudrate=baudrate)

    async def disconnect(self) -> None:
        await self.controller.disconnect()

    async def home(self) -> bool:
        return await self.controller.home()

    async def move_to(self, x: float, y: float, z: Optional[float] = None, speed: Optional[float] = None) -> bool:
        return await self.controller.move_to(x, y, z, speed)

    async def stop(self) -> bool:
        return await self.controller.stop()

    async def pause(self) -> bool:
        return await self.controller.pause()

    async def resume(self) -> bool:
        return await self.controller.resume()

    def get_position(self) -> Dict[str, float]:
        return self.controller.get_position()

    def get_status(self) -> Dict[str, Any]:
        status = self.controller.get_status()
        status["mode"] = self.mode
        return status


machine_service = MachineService()
