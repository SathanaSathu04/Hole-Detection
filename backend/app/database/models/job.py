import enum
from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, Enum, ForeignKey, Index
from sqlalchemy.orm import relationship
from app.database.database import Base


class JobStatus(str, enum.Enum):
    DRAFT = "DRAFT"
    READY = "READY"
    RUNNING = "RUNNING"
    PAUSED = "PAUSED"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    STOPPED = "STOPPED"


class Job(Base):
    __tablename__ = "jobs"

    id = Column(String(36), primary_key=True, index=True)
    board_id = Column(String(36), ForeignKey("boards.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(255), default="Textile Insertion Job")
    status = Column(Enum(JobStatus), default=JobStatus.DRAFT, index=True)
    
    total_holes = Column(Integer, default=0)
    processed_holes = Column(Integer, default=0)
    successful_holes = Column(Integer, default=0)
    failed_holes = Column(Integer, default=0)
    skipped_holes = Column(Integer, default=0)
    
    current_hole_id = Column(String(36), nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)

    # Relationships
    board = relationship("Board", back_populates="jobs")
    job_holes = relationship("JobHole", back_populates="job", cascade="all, delete-orphan", order_by="JobHole.sequence")


class JobHole(Base):
    __tablename__ = "job_holes"

    id = Column(String(36), primary_key=True, index=True)
    job_id = Column(String(36), ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False, index=True)
    hole_id = Column(String(36), ForeignKey("holes.id", ondelete="CASCADE"), nullable=False, index=True)
    
    sequence = Column(Integer, nullable=False, index=True)  # 1, 2, 3... execution order
    status = Column(String(50), default="PENDING", index=True)
    attempt_count = Column(Integer, default=0)
    failure_reason = Column(String(255), nullable=True)
    
    target_machine_x = Column(Float, nullable=True)
    target_machine_y = Column(Float, nullable=True)
    
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)

    # Relationships
    job = relationship("Job", back_populates="job_holes")
    hole = relationship("Hole", back_populates="job_entries")

    __table_args__ = (
        Index("ix_job_holes_job_seq", "job_id", "sequence"),
        Index("ix_job_holes_job_status", "job_id", "status"),
    )
