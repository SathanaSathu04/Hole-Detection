from typing import Optional, Dict, Any
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.services.machine_service import machine_service

router = APIRouter(prefix="/api/machine", tags=["Machine"])


class ConnectRequest(BaseModel):
    mode: Optional[str] = "SIMULATION"  # SIMULATION or REAL
    port: Optional[str] = "COM3"
    baudrate: Optional[int] = 115200


class MoveRequest(BaseModel):
    x: float
    y: float
    z: Optional[float] = None
    speed: Optional[float] = None


@router.post("/connect")
async def connect_machine(req: ConnectRequest):
    try:
        await machine_service.set_mode(req.mode, req.port, req.baudrate)
        return {"status": "SUCCESS", "message": f"Machine connected in {req.mode} mode", "machine_status": machine_service.get_status()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/disconnect")
async def disconnect_machine():
    await machine_service.disconnect()
    return {"status": "SUCCESS", "message": "Machine disconnected"}


@router.post("/home")
async def home_machine():
    try:
        await machine_service.home()
        return {"status": "SUCCESS", "message": "Machine homed successfully", "position": machine_service.get_position()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/move")
async def move_machine(req: MoveRequest):
    try:
        await machine_service.move_to(req.x, req.y, req.z, req.speed)
        return {"status": "SUCCESS", "position": machine_service.get_position()}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/stop")
async def stop_machine():
    await machine_service.stop()
    return {"status": "SUCCESS", "message": "Machine emergency stop engaged"}


@router.get("/status")
def get_machine_status():
    return machine_service.get_status()


@router.get("/position")
def get_machine_position():
    return machine_service.get_position()
