import os
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel, ConfigDict
from datetime import datetime

from app.database.database import get_db
from app.services.board_service import board_service
from app.database.models.board import Board

router = APIRouter(prefix="/api/boards", tags=["Boards"])


class BoardResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    image_path: str
    image_width: Optional[int] = None
    image_height: Optional[int] = None
    total_holes: int = 0
    status: str
    created_at: datetime
    updated_at: Optional[datetime] = None


@router.post("/upload", response_model=BoardResponse)
async def upload_board(
    file: UploadFile = File(...),
    name: Optional[str] = Form(None),
    db: Session = Depends(get_db)
):
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file uploaded")

    allowed_exts = [".jpg", ".jpeg", ".png", ".bmp", ".tif", ".tiff", ".webp"]
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in allowed_exts:
        raise HTTPException(status_code=400, detail=f"Unsupported file format '{ext}'. Use PNG, JPG, or BMP.")

    try:
        content = await file.read()
        board = board_service.create_board(
            db=db,
            name=name if name else os.path.splitext(file.filename)[0],
            file_bytes=content,
            filename=file.filename
        )
        return board
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to process uploaded board: {str(e)}")


@router.get("", response_model=List[BoardResponse])
def get_boards(db: Session = Depends(get_db)):
    return board_service.list_boards(db)


@router.get("/{board_id}", response_model=BoardResponse)
def get_board_detail(board_id: str, db: Session = Depends(get_db)):
    board = board_service.get_board(db, board_id)
    if not board:
        raise HTTPException(status_code=404, detail="Board not found")
    return board


@router.get("/{board_id}/image")
def get_board_image(board_id: str, db: Session = Depends(get_db)):
    board = board_service.get_board(db, board_id)
    if not board or not os.path.exists(board.image_path):
        raise HTTPException(status_code=404, detail="Board image file not found")
    return FileResponse(board.image_path)


@router.delete("/{board_id}")
def delete_board(board_id: str, db: Session = Depends(get_db)):
    success = board_service.delete_board(db, board_id)
    if not success:
        raise HTTPException(status_code=404, detail="Board not found")
    return {"message": f"Board {board_id} deleted successfully"}
