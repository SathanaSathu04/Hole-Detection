import json
from datetime import datetime
from sqlalchemy import Column, String, Float, DateTime, Boolean, ForeignKey, Text
from sqlalchemy.orm import relationship
from app.database.database import Base


class Calibration(Base):
    __tablename__ = "calibrations"

    id = Column(String(36), primary_key=True, index=True)
    board_id = Column(String(36), ForeignKey("boards.id", ondelete="CASCADE"), nullable=True, index=True)
    name = Column(String(255), default="Standard Calibration")
    
    # Stored as JSON strings
    reference_points = Column(Text, nullable=False)  # List of {image: [x,y], machine: [x,y]}
    transformation_matrix = Column(Text, nullable=False)  # 3x3 Homography Matrix serialized to JSON
    machine_origin = Column(Text, nullable=True)  # [x, y, z] in mm
    board_dimensions = Column(Text, nullable=True)  # {width_mm: 300, height_mm: 200}
    
    reprojection_error = Column(Float, default=0.0)
    is_valid = Column(Boolean, default=False)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    board = relationship("Board", back_populates="calibrations")

    def get_reference_points_list(self):
        try:
            return json.loads(self.reference_points) if self.reference_points else []
        except Exception:
            return []

    def get_matrix_array(self):
        try:
            return json.loads(self.transformation_matrix) if self.transformation_matrix else []
        except Exception:
            return []
