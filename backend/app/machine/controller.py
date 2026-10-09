from abc import ABC, abstractmethod
from typing import Dict, Any, Optional


class MachineController(ABC):
    """
    Abstract hardware interface for 3D Textile Thread/Needle Insertion Machine.
    Decouples application logic from physical motor drivers, CNC controllers, or simulators.
    """

    @abstractmethod
    async def connect(self, port: Optional[str] = None, baudrate: int = 115200) -> bool:
        """Establish connection with the controller."""
        pass

    @abstractmethod
    async def disconnect(self) -> None:
        """Safely disconnect from the controller."""
        pass

    @abstractmethod
    async def home(self) -> bool:
        """Drive all axes (X, Y, Z) to home limit switches."""
        pass

    @abstractmethod
    async def move_to(self, x: float, y: float, z: Optional[float] = None, speed: Optional[float] = None) -> bool:
        """Move needle carriage to target XYZ coordinate in mm."""
        pass

    @abstractmethod
    async def insert_thread(self) -> Dict[str, Any]:
        """Trigger physical needle insertion down-stroke and thread feed cycle."""
        pass

    @abstractmethod
    async def stop(self) -> bool:
        """Software emergency stop. Halts motion immediately."""
        pass

    @abstractmethod
    async def pause(self) -> bool:
        """Pause current motion or job sequence."""
        pass

    @abstractmethod
    async def resume(self) -> bool:
        """Resume paused motion or job sequence."""
        pass

    @abstractmethod
    def get_position(self) -> Dict[str, float]:
        """Return current XYZ coordinates in mm: {'x': float, 'y': float, 'z': float}."""
        pass

    @abstractmethod
    def get_status(self) -> Dict[str, Any]:
        """Return comprehensive machine status dictionary."""
        pass
