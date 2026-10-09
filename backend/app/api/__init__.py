from app.api.boards import router as boards_router
from app.api.holes import router as holes_router
from app.api.calibration import router as calibration_router
from app.api.jobs import router as jobs_router
from app.api.machine import router as machine_router
from app.api.camera import router as camera_router
from app.api.system import router as system_router

__all__ = [
    "boards_router",
    "holes_router",
    "calibration_router",
    "jobs_router",
    "machine_router",
    "camera_router",
    "system_router",
]
