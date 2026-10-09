from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel, ConfigDict
from datetime import datetime

from app.database.database import get_db
from app.services.hole_service import hole_service
from app.vision.hole_detector import HoleDetectionConfig
from app.database.models.hole import Hole

router = APIRouter(prefix="/api/boards/{board_id}/holes", tags=["Holes"])


class HoleResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    board_id: str
    label: str
    row_number: int
    column_number: int
    image_x: float
    image_y: float
    radius: float
    board_x: Optional[float] = None
    board_y: Optional[float] = None
    machine_x: Optional[float] = None
    machine_y: Optional[float] = None
    status: str
    failure_reason: Optional[str] = None
    attempt_count: int = 0


class ManualHoleRequest(BaseModel):
    image_x: float
    image_y: float
    label: Optional[str] = None


@router.post("/detect", response_model=Dict[str, Any])
def trigger_hole_detection(
    board_id: str,
    config: Optional[HoleDetectionConfig] = None,
    db: Session = Depends(get_db)
):
    try:
        result = hole_service.detect_and_save_holes(db, board_id, config)
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Hole detection failed: {str(e)}")


@router.get("", response_model=List[HoleResponse])
def get_board_holes(
    board_id: str,
    status: Optional[str] = Query(None, description="Filter by status (PENDING, SUCCESS, FAILED, etc.)"),
    limit: Optional[int] = Query(None, description="Max holes to return"),
    offset: Optional[int] = Query(None, description="Offset for pagination"),
    db: Session = Depends(get_db)
):
    holes = hole_service.get_holes_by_board(db, board_id, status=status, limit=limit, offset=offset)
    return holes


@router.get("/search", response_model=HoleResponse)
def search_hole(
    board_id: str,
    label: str = Query(..., description="Hole label, e.g. A102 or B5"),
    db: Session = Depends(get_db)
):
    hole = hole_service.search_hole(db, board_id, label)
    if not hole:
        raise HTTPException(status_code=404, detail=f"Hole '{label}' not found on board")
    return hole


@router.get("/{hole_id}", response_model=HoleResponse)
def get_hole_by_id(board_id: str, hole_id: str, db: Session = Depends(get_db)):
    hole = db.query(Hole).filter(Hole.id == hole_id, Hole.board_id == board_id).first()
    if not hole:
        raise HTTPException(status_code=404, detail="Hole not found")
    return hole


@router.post("/manual", response_model=HoleResponse)
def add_manual_hole(
    board_id: str,
    req: ManualHoleRequest,
    db: Session = Depends(get_db)
):
    try:
        hole = hole_service.add_manual_hole(db, board_id, req.image_x, req.image_y, req.label)
        return hole
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{hole_id}")
def delete_hole(board_id: str, hole_id: str, db: Session = Depends(get_db)):
    success = hole_service.delete_hole(db, hole_id)
    if not success:
        raise HTTPException(status_code=404, detail="Hole not found")
    return {"message": f"Hole {hole_id} removed"}
