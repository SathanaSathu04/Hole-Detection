import enum
from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, Enum
from sqlalchemy.orm import relationship
from app.database.database import Base


class BoardStatus(str, enum.Enum):
    UPLOADED = "UPLOADED"
    PROCESSING = "PROCESSING"
    READY = "READY"
    ERROR = "ERROR"


class Board(Base):
    __tablename__ = "boards"

    id = Column(String(36), primary_key=True, index=True)
    name = Column(String(255), nullable=False, default="Untitled Board")
    image_path = Column(String(500), nullable=False)
    image_width = Column(Integer, nullable=True)
    image_height = Column(Integer, nullable=True)
    total_holes = Column(Integer, default=0)
    status = Column(Enum(BoardStatus), default=BoardStatus.UPLOADED, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    holes = relationship("Hole", back_populates="board", cascade="all, delete-orphan")
    calibrations = relationship("Calibration", back_populates="board", cascade="all, delete-orphan")
    jobs = relationship("Job", back_populates="board", cascade="all, delete-orphan")
