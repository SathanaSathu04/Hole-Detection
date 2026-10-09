import os
import platform
from datetime import datetime
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database.database import get_db
from app.database.models.board import Board
from app.database.models.hole import Hole
from app.database.models.job import Job
from app.services.machine_service import machine_service
from app.camera.camera_service import camera_service

router = APIRouter(prefix="/api", tags=["System"])


@router.get("/health")
def health_check():
    return {
        "status": "HEALTHY",
        "service": "Textile Thread Insertion System",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "version": "1.0.0"
    }


@router.get("/system/status")
def get_system_status(db: Session = Depends(get_db)):
    board_count = db.query(Board).count()
    hole_count = db.query(Hole).count()
    job_count = db.query(Job).count()

    return {
        "system": {
            "os": platform.system(),
            "release": platform.release(),
            "python_version": platform.python_version(),
            "timestamp": datetime.utcnow().isoformat() + "Z"
        },
        "database": {
            "status": "CONNECTED",
            "total_boards": board_count,
            "total_holes": hole_count,
            "total_jobs": job_count
        },
        "machine": machine_service.get_status(),
        "camera": camera_service.get_status()
    }
