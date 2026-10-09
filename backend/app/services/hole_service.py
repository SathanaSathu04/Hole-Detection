import uuid
import logging
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session

from app.database.models.board import Board, BoardStatus
from app.database.models.hole import Hole, HoleStatus
from app.database.models.calibration import Calibration
from app.vision.board_processor import process_board_image_file
from app.vision.hole_detector import HoleDetectionConfig

logger = logging.getLogger("textile_machine.hole_service")


class HoleService:
    @staticmethod
    def detect_and_save_holes(
        db: Session,
        board_id: str,
        config: Optional[HoleDetectionConfig] = None
    ) -> Dict[str, Any]:
        board = db.query(Board).filter(Board.id == board_id).first()
        if not board:
            raise ValueError(f"Board with id {board_id} not found")

        board.status = BoardStatus.PROCESSING
        db.commit()

        # Check for active calibration matrix for this board if exists
        calib = db.query(Calibration).filter(Calibration.board_id == board_id, Calibration.is_valid == True).order_by(Calibration.created_at.desc()).first()
        calib_json = calib.transformation_matrix if calib else None

        try:
            detected_holes, metadata = process_board_image_file(
                image_path=board.image_path,
                config=config,
                calibration_matrix_json=calib_json
            )

            # Clear previous holes for this board
            db.query(Hole).filter(Hole.board_id == board_id).delete()

            # Fast bulk creation
            hole_entities = []
            for h in detected_holes:
                hole_id = str(uuid.uuid4())
                hole_obj = Hole(
                    id=hole_id,
                    board_id=board_id,
                    label=h["label"],
                    row_number=h["row_number"],
                    column_number=h["column_number"],
                    image_x=h["image_x"],
                    image_y=h["image_y"],
                    radius=h.get("radius", 5.0),
                    board_x=h.get("board_x", 0.0),
                    board_y=h.get("board_y", 0.0),
                    machine_x=h.get("machine_x", 0.0),
                    machine_y=h.get("machine_y", 0.0),
                    status=HoleStatus.PENDING,
                    attempt_count=0,
                )
                hole_entities.append(hole_obj)

            db.bulk_save_objects(hole_entities)
            
            board.total_holes = len(hole_entities)
            board.image_width = metadata["image_width"]
            board.image_height = metadata["image_height"]
            board.status = BoardStatus.READY
            db.commit()

            logger.info(f"Successfully processed {len(hole_entities)} holes for board {board_id}")
            return {
                "board_id": board_id,
                "total_holes": len(hole_entities),
                "metadata": metadata
            }

        except Exception as e:
            board.status = BoardStatus.ERROR
            db.commit()
            logger.error(f"Error detecting holes: {e}", exc_info=True)
            raise

    @staticmethod
    def get_holes_by_board(
        db: Session,
        board_id: str,
        status: Optional[str] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None
    ) -> List[Hole]:
        query = db.query(Hole).filter(Hole.board_id == board_id)
        if status:
            query = query.filter(Hole.status == status)
        query = query.order_by(Hole.row_number.asc(), Hole.column_number.asc())
        if offset is not None:
            query = query.offset(offset)
        if limit is not None:
            query = query.limit(limit)
        return query.all()

    @staticmethod
    def search_hole(db: Session, board_id: str, label: str) -> Optional[Hole]:
        return db.query(Hole).filter(
            Hole.board_id == board_id,
            Hole.label == label.strip().upper()
        ).first()

    @staticmethod
    def update_hole_status(db: Session, hole_id: str, status: HoleStatus, reason: Optional[str] = None) -> Optional[Hole]:
        hole = db.query(Hole).filter(Hole.id == hole_id).first()
        if hole:
            hole.status = status
            if reason:
                hole.failure_reason = reason
            db.commit()
            db.refresh(hole)
        return hole

    @staticmethod
    def add_manual_hole(db: Session, board_id: str, image_x: float, image_y: float, label: Optional[str] = None) -> Hole:
        board = db.query(Board).filter(Board.id == board_id).first()
        if not board:
            raise ValueError("Board not found")

        count = db.query(Hole).filter(Hole.board_id == board_id).count()
        new_label = label if label else f"M{count + 1}"
        hole = Hole(
            id=str(uuid.uuid4()),
            board_id=board_id,
            label=new_label,
            row_number=999,
            column_number=count + 1,
            image_x=image_x,
            image_y=image_y,
            machine_x=round(image_x * 0.2, 2),
            machine_y=round(image_y * 0.2, 2),
            board_x=round(image_x * 0.2, 2),
            board_y=round(image_y * 0.2, 2),
            status=HoleStatus.PENDING
        )
        db.add(hole)
        board.total_holes += 1
        db.commit()
        db.refresh(hole)
        return hole

    @staticmethod
    def delete_hole(db: Session, hole_id: str) -> bool:
        hole = db.query(Hole).filter(Hole.id == hole_id).first()
        if not hole:
            return False
        board = db.query(Board).filter(Board.id == hole.board_id).first()
        if board and board.total_holes > 0:
            board.total_holes -= 1
        db.delete(hole)
        db.commit()
        return True


hole_service = HoleService()
