import uuid
import asyncio
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session

from app.database.database import SessionLocal
from app.database.models.board import Board, BoardStatus
from app.database.models.hole import Hole, HoleStatus
from app.database.models.job import Job, JobHole, JobStatus
from app.database.models.calibration import Calibration
from app.services.machine_service import machine_service
from app.camera.camera_service import camera_service
from app.vision.verification import verify_insertion
from app.websocket.manager import ws_manager

logger = logging.getLogger("textile_machine.job_service")


class JobService:
    def __init__(self):
        self.active_tasks: Dict[str, asyncio.Task] = {}
        self.pause_events: Dict[str, asyncio.Event] = {}
        self.stop_flags: Dict[str, bool] = {}

    def create_job(
        self,
        db: Session,
        board_id: str,
        hole_ids: List[str],
        name: Optional[str] = None
    ) -> Job:
        board = db.query(Board).filter(Board.id == board_id).first()
        if not board:
            raise ValueError("Board not found")

        if not hole_ids:
            # If no specific holes passed, take all holes ordered by row and column
            all_holes = db.query(Hole).filter(Hole.board_id == board_id).order_by(Hole.row_number.asc(), Hole.column_number.asc()).all()
            hole_ids = [h.id for h in all_holes]

        if not hole_ids:
            raise ValueError("No holes available on this board to create a job")

        job_id = str(uuid.uuid4())
        job = Job(
            id=job_id,
            board_id=board_id,
            name=name if name else f"Job_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            status=JobStatus.READY,
            total_holes=len(hole_ids),
            processed_holes=0,
            successful_holes=0,
            failed_holes=0,
            skipped_holes=0,
        )
        db.add(job)

        # Create JobHole sequence records
        job_holes = []
        for seq, h_id in enumerate(hole_ids, start=1):
            hole = db.query(Hole).filter(Hole.id == h_id).first()
            if hole:
                jh = JobHole(
                    id=str(uuid.uuid4()),
                    job_id=job_id,
                    hole_id=h_id,
                    sequence=seq,
                    status="PENDING",
                    target_machine_x=hole.machine_x,
                    target_machine_y=hole.machine_y,
                )
                job_holes.append(jh)
                hole.status = HoleStatus.SELECTED

        db.bulk_save_objects(job_holes)
        db.commit()
        db.refresh(job)

        logger.info(f"Created Job {job.id} with {len(job_holes)} holes")
        asyncio.create_task(ws_manager.broadcast("JOB_CREATED", {
            "job_id": job.id,
            "name": job.name,
            "total_holes": job.total_holes
        }))
        return job

    def get_job(self, db: Session, job_id: str) -> Optional[Job]:
        return db.query(Job).filter(Job.id == job_id).first()

    def list_jobs(self, db: Session, board_id: Optional[str] = None) -> List[Job]:
        query = db.query(Job)
        if board_id:
            query = query.filter(Job.board_id == board_id)
        return query.order_by(Job.created_at.desc()).all()

    async def start_job(self, db: Session, job_id: str) -> Job:
        job = db.query(Job).filter(Job.id == job_id).first()
        if not job:
            raise ValueError("Job not found")

        # SAFETY CHECKS
        machine_status = machine_service.get_status()
        if not machine_status.get("is_connected", False):
            raise RuntimeError("Machine is not connected. Connect machine before starting job.")

        if job.status == JobStatus.RUNNING:
            return job

        job.status = JobStatus.RUNNING
        job.started_at = datetime.utcnow()
        db.commit()

        self.stop_flags[job_id] = False
        pause_event = asyncio.Event()
        pause_event.set()
        self.pause_events[job_id] = pause_event

        # Spawn asynchronous job execution worker
        task = asyncio.create_task(self._run_job_execution(job_id))
        self.active_tasks[job_id] = task

        await ws_manager.broadcast("JOB_STARTED", {
            "job_id": job.id,
            "total_holes": job.total_holes
        })
        return job

    async def pause_job(self, db: Session, job_id: str) -> Job:
        job = db.query(Job).filter(Job.id == job_id).first()
        if not job:
            raise ValueError("Job not found")

        if job_id in self.pause_events:
            self.pause_events[job_id].clear()

        job.status = JobStatus.PAUSED
        db.commit()
        await machine_service.pause()
        await ws_manager.broadcast("JOB_PAUSED", {"job_id": job_id})
        return job

    async def resume_job(self, db: Session, job_id: str) -> Job:
        job = db.query(Job).filter(Job.id == job_id).first()
        if not job:
            raise ValueError("Job not found")

        if job_id in self.pause_events:
            self.pause_events[job_id].set()

        job.status = JobStatus.RUNNING
        db.commit()
        await machine_service.resume()
        await ws_manager.broadcast("JOB_RESUMED", {"job_id": job_id})
        return job

    async def stop_job(self, db: Session, job_id: str) -> Job:
        job = db.query(Job).filter(Job.id == job_id).first()
        if not job:
            raise ValueError("Job not found")

        self.stop_flags[job_id] = True
        if job_id in self.pause_events:
            self.pause_events[job_id].set()

        if job_id in self.active_tasks:
            self.active_tasks[job_id].cancel()

        job.status = JobStatus.STOPPED
        job.completed_at = datetime.utcnow()
        db.commit()
        await machine_service.stop()
        await ws_manager.broadcast("JOB_STOPPED", {"job_id": job_id})
        return job

    async def retry_hole(self, db: Session, job_id: str, hole_id: str) -> Dict[str, Any]:
        job_hole = db.query(JobHole).filter(JobHole.job_id == job_id, JobHole.hole_id == hole_id).first()
        hole = db.query(Hole).filter(Hole.id == hole_id).first()
        if not job_hole or not hole:
            raise ValueError("Hole or Job entry not found")

        # Execute single hole insertion
        result = await self._process_single_hole(job_id, job_hole, hole, is_retry=True)
        return result

    async def _run_job_execution(self, job_id: str):
        """Asynchronous worker executing all job holes sequentially."""
        logger.info(f"Starting execution loop for job {job_id}")

        while True:
            # Check pause / stop conditions
            if self.stop_flags.get(job_id, False):
                break

            pause_event = self.pause_events.get(job_id)
            if pause_event:
                await pause_event.wait()

            # Create fresh DB session for isolation
            with SessionLocal() as db:
                job = db.query(Job).filter(Job.id == job_id).first()
                if not job or job.status != JobStatus.RUNNING:
                    break

                # Get next pending job hole
                next_jh = db.query(JobHole).filter(
                    JobHole.job_id == job_id,
                    JobHole.status == "PENDING"
                ).order_by(JobHole.sequence.asc()).first()

                if not next_jh:
                    # All holes processed
                    job.status = JobStatus.COMPLETED
                    job.completed_at = datetime.utcnow()
                    db.commit()
                    await ws_manager.broadcast("JOB_COMPLETED", {
                        "job_id": job_id,
                        "successful": job.successful_holes,
                        "failed": job.failed_holes
                    })
                    break

                hole = db.query(Hole).filter(Hole.id == next_jh.hole_id).first()
                job.current_hole_id = hole.id if hole else None
                db.commit()

            # Process this hole
            await self._process_single_hole(job_id, next_jh, hole)

        logger.info(f"Job execution loop finished for job {job_id}")

    async def _process_single_hole(self, job_id: str, job_hole: JobHole, hole: Hole, is_retry: bool = False) -> Dict[str, Any]:
        """Runs the complete movement, insertion, and camera verification cycle for a hole."""
        with SessionLocal() as db:
            jh = db.query(JobHole).filter(JobHole.id == job_hole.id).first()
            h = db.query(Hole).filter(Hole.id == hole.id).first()
            job = db.query(Job).filter(Job.id == job_id).first()

            jh.status = "PROCESSING"
            jh.started_at = datetime.utcnow()
            jh.attempt_count += 1
            h.status = HoleStatus.PROCESSING
            h.attempt_count += 1
            db.commit()

            label = h.label
            target_x = h.machine_x or (h.image_x * 0.2)
            target_y = h.machine_y or (h.image_y * 0.2)

        # Broadcast state
        await ws_manager.broadcast("HOLE_PROCESSING", {
            "job_id": job_id,
            "hole_id": hole.id,
            "label": label,
            "attempt": hole.attempt_count,
            "is_retry": is_retry,
            "machine_x": target_x,
            "machine_y": target_y
        })

        # Update simulator/camera targets
        if hasattr(machine_service.controller, "current_hole_label"):
            machine_service.controller.current_hole_label = label
        camera_service.active_hole_label = label
        camera_service.active_state = "MOVING"

        # 1. MOVE TO HOLE
        try:
            await machine_service.move_to(target_x, target_y)
        except Exception as e:
            logger.error(f"Motion error: {e}")

        # 2. INSERT THREAD
        camera_service.active_state = "INSERTING"
        await machine_service.controller.insert_thread()

        # 3. CAMERA VERIFICATION
        camera_service.active_state = "VERIFYING"
        await ws_manager.broadcast("CAMERA_VERIFICATION", {
            "hole": label,
            "status": "VERIFYING"
        })

        # Capture frame
        frame = camera_service.capture_frame()
        expected_info = {"image_x": hole.image_x, "image_y": hole.image_y, "camera_x": 320, "camera_y": 240}
        
        # In simulator mode, let retry succeed or determine verification
        verification = verify_insertion(frame, expected_info)
        
        # Optional failure demo check: if hole label is configured to fail on attempt 1
        force_fails = getattr(machine_service.controller, "force_fail_labels", set())
        if label in force_fails and hole.attempt_count == 1:
            verification = {
                "success": False,
                "confidence": 0.2,
                "reason": "THREAD_NOT_DETECTED",
                "details": "Simulated thread insertion failure for test verification"
            }

        is_success = verification.get("success", True)
        reason = verification.get("reason", "THREAD_DETECTED" if is_success else "THREAD_NOT_DETECTED")
        confidence = verification.get("confidence", 0.95)

        # 4. PERSIST RESULT
        with SessionLocal() as db:
            jh = db.query(JobHole).filter(JobHole.id == job_hole.id).first()
            h = db.query(Hole).filter(Hole.id == hole.id).first()
            job = db.query(Job).filter(Job.id == job_id).first()

            jh.completed_at = datetime.utcnow()
            jh.failure_reason = reason if not is_success else None

            if is_success:
                jh.status = "SUCCESS"
                h.status = HoleStatus.SUCCESS
                camera_service.active_state = "SUCCESS"
                job.successful_holes += 1
                event_type = "HOLE_SUCCESS"
            else:
                jh.status = "FAILED"
                h.status = HoleStatus.FAILED
                h.failure_reason = reason
                camera_service.active_state = "FAILED"
                job.failed_holes += 1
                event_type = "HOLE_FAILED"

            job.processed_holes += 1
            db.commit()

        # Broadcast update
        await ws_manager.broadcast(event_type, {
            "job_id": job_id,
            "hole_id": hole.id,
            "label": label,
            "status": "SUCCESS" if is_success else "FAILED",
            "reason": reason,
            "confidence": confidence,
            "attempt": hole.attempt_count,
            "processed": job.processed_holes,
            "total": job.total_holes
        })

        return {
            "success": is_success,
            "hole": label,
            "reason": reason,
            "confidence": confidence
        }


job_service = JobService()
