from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, Text
from app.database.database import Base


class MachineConfiguration(Base):
    __tablename__ = "machine_configurations"

    id = Column(String(36), primary_key=True, index=True)
    name = Column(String(255), default="Default Machine Config")
    mode = Column(String(50), default="SIMULATION")  # SIMULATION or REAL
    
    # Motion limits (in mm)
    max_x = Column(Float, default=500.0)
    max_y = Column(Float, default=500.0)
    max_z = Column(Float, default=100.0)
    safe_z = Column(Float, default=25.0)
    insert_z = Column(Float, default=5.0)
    
    # Speeds
    travel_speed = Column(Float, default=100.0)  # mm/s
    insertion_speed = Column(Float, default=20.0)  # mm/s
    
    # Real Hardware connection details (placeholders for real controller)
    port = Column(String(50), default="COM3")
    baudrate = Column(Integer, default=115200)
    protocol = Column(String(50), default="GCODE_GENERIC")
    
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class CameraConfiguration(Base):
    __tablename__ = "camera_configurations"

    id = Column(String(36), primary_key=True, index=True)
    name = Column(String(255), default="Inspection Camera")
    device_index = Column(Integer, default=0)
    resolution_width = Column(Integer, default=1920)
    resolution_height = Column(Integer, default=1080)
    fps = Column(Integer, default=30)
    exposure = Column(Float, nullable=True)
    brightness = Column(Float, nullable=True)
    focus = Column(Float, nullable=True)
    
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
