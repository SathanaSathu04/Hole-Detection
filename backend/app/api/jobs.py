from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel, ConfigDict
from datetime import datetime

from app.database.database import get_db
from app.services.job_service import job_service
from app.database.models.job import Job, JobHole
from app.database.models.hole import Hole

router = APIRouter(prefix="/api/jobs", tags=["Jobs"])


class CreateJobRequest(BaseModel):
    board_id: str
    hole_ids: Optional[List[str]] = []
    name: Optional[str] = None


class JobHoleDetail(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    hole_id: str
    sequence: int
    status: str
    attempt_count: int
    failure_reason: Optional[str] = None
    target_machine_x: Optional[float] = None
    target_machine_y: Optional[float] = None
    label: Optional[str] = None
    image_x: Optional[float] = None
    image_y: Optional[float] = None


class JobDetailResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    board_id: str
    name: str
    status: str
    total_holes: int
    processed_holes: int
    successful_holes: int
    failed_holes: int
    skipped_holes: int
    current_hole_id: Optional[str] = None
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    job_holes: Optional[List[JobHoleDetail]] = []


@router.post("", response_model=JobDetailResponse)
def create_job(req: CreateJobRequest, db: Session = Depends(get_db)):
    try:
        job = job_service.create_job(db, req.board_id, req.hole_ids, req.name)
        return job
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create job: {str(e)}")


@router.get("", response_model=List[JobDetailResponse])
def list_jobs(board_id: Optional[str] = Query(None), db: Session = Depends(get_db)):
    return job_service.list_jobs(db, board_id=board_id)


@router.get("/{job_id}", response_model=JobDetailResponse)
def get_job_detail(job_id: str, db: Session = Depends(get_db)):
    job = job_service.get_job(db, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    job_hole_details = []
    for jh in job.job_holes:
        hole = db.query(Hole).filter(Hole.id == jh.hole_id).first()
        job_hole_details.append(JobHoleDetail(
            id=jh.id,
            hole_id=jh.hole_id,
            sequence=jh.sequence,
            status=jh.status,
            attempt_count=jh.attempt_count,
            failure_reason=jh.failure_reason,
            target_machine_x=jh.target_machine_x,
            target_machine_y=jh.target_machine_y,
            label=hole.label if hole else "UNKNOWN",
            image_x=hole.image_x if hole else None,
            image_y=hole.image_y if hole else None,
        ))

    response_data = JobDetailResponse.model_validate(job)
    response_data.job_holes = job_hole_details
    return response_data


@router.post("/{job_id}/start")
async def start_job(job_id: str, db: Session = Depends(get_db)):
    try:
        job = await job_service.start_job(db, job_id)
        return {"status": "SUCCESS", "message": f"Job {job.id} started", "job_status": job.status}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{job_id}/pause")
async def pause_job(job_id: str, db: Session = Depends(get_db)):
    try:
        job = await job_service.pause_job(db, job_id)
        return {"status": "SUCCESS", "message": f"Job {job.id} paused"}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/{job_id}/resume")
async def resume_job(job_id: str, db: Session = Depends(get_db)):
    try:
        job = await job_service.resume_job(db, job_id)
        return {"status": "SUCCESS", "message": f"Job {job.id} resumed"}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/{job_id}/stop")
async def stop_job(job_id: str, db: Session = Depends(get_db)):
    try:
        job = await job_service.stop_job(db, job_id)
        return {"status": "SUCCESS", "message": f"Job {job.id} stopped"}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/{job_id}/retry/{hole_id}")
async def retry_hole(job_id: str, hole_id: str, db: Session = Depends(get_db)):
    try:
        result = await job_service.retry_hole(db, job_id, hole_id)
        return {"status": "SUCCESS", "result": result}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
