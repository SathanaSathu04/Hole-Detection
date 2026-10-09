import os
import uuid
import cv2
import numpy as np
import logging
from typing import List, Optional
from datetime import datetime
from sqlalchemy.orm import Session

from app.database.models.board import Board, BoardStatus

logger = logging.getLogger("textile_machine.board_service")

STORAGE_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "storage", "boards")
os.makedirs(STORAGE_DIR, exist_ok=True)


class BoardService:
    @staticmethod
    def create_board(db: Session, name: str, file_bytes: bytes, filename: str) -> Board:
        board_id = str(uuid.uuid4())
        safe_filename = f"{board_id}_{filename.replace(' ', '_')}"
        file_path = os.path.join(STORAGE_DIR, safe_filename)

        with open(file_path, "wb") as f:
            f.write(file_bytes)

        # Read dimensions
        np_arr = np.frombuffer(file_bytes, np.uint8)
        img = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
        height, width = (img.shape[0], img.shape[1]) if img is not None else (0, 0)

        board = Board(
            id=board_id,
            name=name if name else f"Board_{datetime.now().strftime('%Y%m%d_%H%M')}",
            image_path=file_path,
            image_width=width,
            image_height=height,
            total_holes=0,
            status=BoardStatus.UPLOADED,
        )
        db.add(board)
        db.commit()
        db.refresh(board)
        logger.info(f"Created board {board.id} with image {width}x{height}px")
        return board

    @staticmethod
    def get_board(db: Session, board_id: str) -> Optional[Board]:
        return db.query(Board).filter(Board.id == board_id).first()

    @staticmethod
    def list_boards(db: Session) -> List[Board]:
        return db.query(Board).order_by(Board.created_at.desc()).all()

    @staticmethod
    def delete_board(db: Session, board_id: str) -> bool:
        board = db.query(Board).filter(Board.id == board_id).first()
        if not board:
            return False
        if os.path.exists(board.image_path):
            try:
                os.remove(board.image_path)
            except Exception as e:
                logger.warning(f"Failed to delete board image file: {e}")
        db.delete(board)
        db.commit()
        return True


board_service = BoardService()
