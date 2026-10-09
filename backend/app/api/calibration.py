import json
import uuid
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.database.database import get_db
from app.database.models.calibration import Calibration
from app.vision.calibration import compute_calibration_homography, CalibrationRequest, CalibrationPoint
from app.vision.coordinate_mapper import CoordinateMapper

router = APIRouter(prefix="/api/calibration", tags=["Calibration"])


class CalibrationResponse(BaseModel):
    id: str
    board_id: Optional[str]
    name: str
    is_valid: bool
    reprojection_error: float
    reference_points: List[Dict[str, Any]]
    transformation_matrix: List[List[float]]
    point_errors: List[Dict[str, Any]]
    message: str


class TestCoordRequest(BaseModel):
    image_x: float
    image_y: float
    calibration_id: Optional[str] = None


@router.post("", response_model=CalibrationResponse)
def create_calibration(req: CalibrationRequest, db: Session = Depends(get_db)):
    is_valid, H, mean_err, pt_errors, msg = compute_calibration_homography(req.reference_points)

    if H is None:
        raise HTTPException(status_code=422, detail=f"Calibration calculation failed: {msg}")

    calib_id = str(uuid.uuid4())
    matrix_list = H.tolist()
    points_dict = [p.dict() for p in req.reference_points]

    calib = Calibration(
        id=calib_id,
        board_id=req.board_id,
        name=req.name,
        reference_points=json.dumps(points_dict),
        transformation_matrix=json.dumps(matrix_list),
        machine_origin=json.dumps(req.machine_origin),
        board_dimensions=json.dumps(req.board_dimensions) if req.board_dimensions else None,
        reprojection_error=mean_err,
        is_valid=is_valid
    )
    db.add(calib)
    db.commit()

    return CalibrationResponse(
        id=calib_id,
        board_id=req.board_id,
        name=req.name,
        is_valid=is_valid,
        reprojection_error=mean_err,
        reference_points=points_dict,
        transformation_matrix=matrix_list,
        point_errors=pt_errors,
        message=msg
    )


@router.get("", response_model=List[CalibrationResponse])
def get_calibrations(board_id: Optional[str] = Query(None), db: Session = Depends(get_db)):
    query = db.query(Calibration)
    if board_id:
        query = query.filter(Calibration.board_id == board_id)
    calibs = query.order_by(Calibration.created_at.desc()).all()

    results = []
    for c in calibs:
        results.append(CalibrationResponse(
            id=c.id,
            board_id=c.board_id,
            name=c.name,
            is_valid=c.is_valid,
            reprojection_error=c.reprojection_error,
            reference_points=c.get_reference_points_list(),
            transformation_matrix=c.get_matrix_array(),
            point_errors=[],
            message="Valid calibration" if c.is_valid else "Invalid calibration"
        ))
    return results


@router.post("/test")
def test_coordinate_transformation(req: TestCoordRequest, db: Session = Depends(get_db)):
    calib = None
    if req.calibration_id:
        calib = db.query(Calibration).filter(Calibration.id == req.calibration_id).first()
    else:
        calib = db.query(Calibration).filter(Calibration.is_valid == True).order_by(Calibration.created_at.desc()).first()

    mapper = CoordinateMapper.from_json(calib.transformation_matrix) if calib else CoordinateMapper()
    mach_x, mach_y = mapper.image_to_machine(req.image_x, req.image_y)
    board_x, board_y = mapper.image_to_board(req.image_x, req.image_y)

    return {
        "image": {"x": req.image_x, "y": req.image_y},
        "board_mm": {"x": board_x, "y": board_y},
        "machine_mm": {"x": mach_x, "y": mach_y},
        "is_calibrated": calib is not None and calib.is_valid
    }
