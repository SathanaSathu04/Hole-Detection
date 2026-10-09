import time
import cv2
import asyncio
from datetime import datetime
from typing import Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Response
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.database.database import get_db
from app.camera.camera_service import camera_service
from app.services.board_service import board_service
from app.services.hole_service import hole_service
from app.api.boards import BoardResponse

router = APIRouter(prefix="/api/camera", tags=["Camera"])


class CameraConnectRequest(BaseModel):
    device_index: Optional[int] = 0


class CaptureBoardRequest(BaseModel):
    name: Optional[str] = None


@router.post("/connect")
async def connect_camera(req: CameraConnectRequest):
    await camera_service.connect(device_index=req.device_index)
    return {"status": "SUCCESS", "camera_status": camera_service.get_status()}


@router.post("/disconnect")
async def disconnect_camera():
    await camera_service.disconnect()
    return {"status": "SUCCESS", "message": "Camera disconnected"}


@router.get("/status")
def get_camera_status():
    return camera_service.get_status()


@router.get("/frame")
def get_camera_frame():
    frame = camera_service.capture_frame()
    if frame is None:
        raise HTTPException(status_code=500, detail="Failed to capture frame")
    _, buffer = cv2.imencode(".jpg", frame, [int(cv2.IMWRITE_JPEG_QUALITY), 80])
    return Response(content=buffer.tobytes(), media_type="image/jpeg")


@router.post("/capture-board")
def capture_board_from_camera(
    req: Optional[CaptureBoardRequest] = None,
    db: Session = Depends(get_db)
):
    """
    Captures live frame from camera, registers it as a new board,
    executes OpenCV hole detection, numbers holes with Excel labels, and returns board details.
    """
    frame = camera_service.capture_frame()
    if frame is None:
        raise HTTPException(status_code=500, detail="Failed to capture frame from camera")

    success, buffer = cv2.imencode(".png", frame)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to encode captured camera frame")

    board_name = (req.name if req and req.name else None) or f"Camera_Scan_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    file_bytes = buffer.tobytes()

    try:
        board = board_service.create_board(
            db=db,
            name=board_name,
            file_bytes=file_bytes,
            filename=f"{board_name}.png"
        )
        detection_result = hole_service.detect_and_save_holes(db, board.id)
        
        # Reload board with updated total_holes
        db.refresh(board)
        return {
            "status": "SUCCESS",
            "board": BoardResponse.model_validate(board),
            "detection": detection_result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to process captured board: {str(e)}")


async def generate_mjpeg_stream():
    """Generates continuous MJPEG multipart stream for live HTML5 video player."""
    while True:
        frame = camera_service.capture_frame()
        if frame is not None:
            _, buffer = cv2.imencode(".jpg", frame, [int(cv2.IMWRITE_JPEG_QUALITY), 75])
            frame_bytes = buffer.tobytes()
            yield (b"--frame\r\n"
                   b"Content-Type: image/jpeg\r\n\r\n" + frame_bytes + b"\r\n")
        await asyncio.sleep(0.04)  # ~25 FPS


@router.get("/stream")
def stream_camera_feed():
    return StreamingResponse(
        generate_mjpeg_stream(),
        media_type="multipart/x-mixed-replace; boundary=frame"
    )
