import enum
from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, Enum, ForeignKey, Index
from sqlalchemy.orm import relationship
from app.database.database import Base


class HoleStatus(str, enum.Enum):
    PENDING = "PENDING"
    SELECTED = "SELECTED"
    PROCESSING = "PROCESSING"
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
    SKIPPED = "SKIPPED"


class Hole(Base):
    __tablename__ = "holes"

    id = Column(String(36), primary_key=True, index=True)
    board_id = Column(String(36), ForeignKey("boards.id", ondelete="CASCADE"), nullable=False, index=True)
    label = Column(String(50), nullable=False, index=True)  # e.g., A1, A102, AA15
    row_number = Column(Integer, nullable=False, index=True)  # 1-based index of row
    column_number = Column(Integer, nullable=False, index=True)  # 1-based index within row
    
    # Coordinates across coordinate frames
    image_x = Column(Float, nullable=False)
    image_y = Column(Float, nullable=False)
    radius = Column(Float, default=5.0)  # pixel radius
    
    board_x = Column(Float, nullable=True)  # mm on physical board
    board_y = Column(Float, nullable=True)  # mm on physical board
    
    machine_x = Column(Float, nullable=True)  # mm in machine coordinates
    machine_y = Column(Float, nullable=True)  # mm in machine coordinates
    
    status = Column(Enum(HoleStatus), default=HoleStatus.PENDING, index=True)
    failure_reason = Column(String(255), nullable=True)
    attempt_count = Column(Integer, default=0)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    board = relationship("Board", back_populates="holes")
    job_entries = relationship("JobHole", back_populates="hole", cascade="all, delete-orphan")

    __table_args__ = (
        Index("ix_holes_board_label", "board_id", "label"),
        Index("ix_holes_board_status", "board_id", "status"),
        Index("ix_holes_board_row_col", "board_id", "row_number", "column_number"),
    )
