import os
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.database.database import init_db, SessionLocal
from app.database.models.board import Board
from app.services.board_service import board_service
from app.services.hole_service import hole_service
from app.websocket.manager import ws_manager
from app.services.machine_service import machine_service
from app.camera.camera_service import camera_service
from app.api import (
    boards_router,
    holes_router,
    calibration_router,
    jobs_router,
    machine_router,
    camera_router,
    system_router,
)

# Configure structured logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] [%(name)s] %(message)s",
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger("textile_machine.main")


def auto_seed_sample_board():
    """Automatically loads and analyzes sample_board_300.png if database is empty."""
    with SessionLocal() as db:
        existing = db.query(Board).first()
        if not existing:
            sample_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "sample-data", "sample_board_300.png")
            if os.path.exists(sample_path):
                logger.info(f"Auto-seeding sample textile board from {sample_path}...")
                with open(sample_path, "rb") as f:
                    file_bytes = f.read()
                board = board_service.create_board(
                    db=db,
                    name="Production Textile Board (Sample 300)",
                    file_bytes=file_bytes,
                    filename="sample_board_300.png"
                )
                hole_service.detect_and_save_holes(db, board.id)
                logger.info(f"Auto-seeded board {board.id} with {board.total_holes} detected holes.")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: initialize database tables and hardware services
    logger.info("Initializing Textile Machine Control System database...")
    init_db()
    
    # Auto seed initial sample board so UI is instantly ready
    try:
        auto_seed_sample_board()
    except Exception as e:
        logger.warning(f"Auto-seeding failed: {e}")

    logger.info("Connecting machine controller in SIMULATION mode...")
    await machine_service.connect()
    
    logger.info("Connecting vision camera subsystem...")
    await camera_service.connect()
    
    logger.info("Textile Thread/Needle Insertion System backend ready.")
    yield
    # Shutdown
    logger.info("Shutting down machine controllers and camera feeds...")
    await machine_service.disconnect()
    await camera_service.disconnect()


app = FastAPI(
    title="Automated Textile Thread/Needle Insertion Control API",
    description="Production-oriented industrial control backend for textile hole detection, 3D CNC kinematics, live camera verification, and job management.",
    version="1.0.0",
    lifespan=lifespan
)

# Enable CORS for Angular frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API Routers
app.include_router(system_router)
app.include_router(boards_router)
app.include_router(holes_router)
app.include_router(calibration_router)
app.include_router(jobs_router)
app.include_router(machine_router)
app.include_router(camera_router)


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await ws_manager.connect(websocket)
    try:
        # Send initial status packet immediately
        initial_status = {
            "machine": machine_service.get_status(),
            "camera": camera_service.get_status(),
        }
        await websocket.send_json({
            "event": "INITIAL_STATE",
            "data": initial_status
        })

        while True:
            # Keep receiving client pings or control messages
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)
    except Exception as e:
        logger.warning(f"WebSocket connection exception: {e}")
        ws_manager.disconnect(websocket)
