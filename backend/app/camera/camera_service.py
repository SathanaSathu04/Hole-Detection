import time
import cv2
import numpy as np
import logging
from typing import Dict, Any, Optional
from datetime import datetime
from app.websocket.manager import ws_manager

logger = logging.getLogger("textile_machine.camera")


class CameraService:
    """
    Industrial Camera Interface supporting USB OpenCV video capture
    with automatic synthetic frame generation fallback when hardware camera is unavailable.
    """

    def __init__(self, device_index: int = 0):
        self.device_index: int = device_index
        self.cap: Optional[cv2.VideoCapture] = None
        self.is_connected: bool = False
        self.is_streaming: bool = False
        self.use_synthetic: bool = False
        
        # Camera properties
        self.width: int = 640
        self.height: int = 480
        self.fps: int = 30
        
        # State for synthetic inspection visualization
        self.active_hole_label: str = "A1"
        self.active_state: str = "IDLE"  # IDLE, INSERTING, VERIFYING, SUCCESS, FAILED
        self.last_frame: Optional[np.ndarray] = None
        self.last_frame_timestamp: float = 0.0

    async def connect(self, device_index: Optional[int] = None) -> bool:
        if device_index is not None:
            self.device_index = device_index

        try:
            # Try connecting to physical USB camera
            self.cap = cv2.VideoCapture(self.device_index, cv2.CAP_DSHOW)
            if self.cap.isOpened():
                self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
                self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)
                self.is_connected = True
                self.use_synthetic = False
                logger.info(f"Connected to physical camera device #{self.device_index}")
            else:
                # Fallback to high-definition synthetic inspection feed
                self.is_connected = True
                self.use_synthetic = True
                logger.info("Physical camera not detected. Enabled synthetic industrial camera simulation feed.")
        except Exception as e:
            self.is_connected = True
            self.use_synthetic = True
            logger.warning(f"Error accessing physical camera: {e}. Using synthetic feed.")

        await ws_manager.broadcast("CAMERA_CONNECTED", {
            "device_index": self.device_index,
            "synthetic_mode": self.use_synthetic,
            "status": "CONNECTED"
        })
        return True

    async def disconnect(self) -> None:
        if self.cap is not None:
            try:
                self.cap.release()
            except Exception:
                pass
            self.cap = None

        self.is_connected = False
        self.is_streaming = False
        logger.info("Camera disconnected.")
        await ws_manager.broadcast("CAMERA_DISCONNECTED", {"status": "DISCONNECTED"})

    def capture_frame(self) -> np.ndarray:
        """Captures a single BGR frame from physical camera or synthetic generator."""
        if not self.is_connected:
            self.last_frame = self._generate_error_frame("CAMERA DISCONNECTED")
            return self.last_frame

        if not self.use_synthetic and self.cap is not None and self.cap.isOpened():
            ret, frame = self.cap.read()
            if ret and frame is not None:
                self.last_frame = frame
                self.last_frame_timestamp = time.time()
                return frame

        # Synthetic camera frame generation
        frame = self._generate_synthetic_frame()
        self.last_frame = frame
        self.last_frame_timestamp = time.time()
        return frame

    def _generate_synthetic_frame(self) -> np.ndarray:
        """Generates realistic live inspection feed with textile board view, crosshair, and thread."""
        img = np.zeros((self.height, self.width, 3), dtype=np.uint8)
        
        # Background: Textured textile fabric look (slate/dark grey pattern)
        img[:] = (35, 38, 42)
        
        # Draw grid lines for textile weave
        for y in range(0, self.height, 20):
            cv2.line(img, (0, y), (self.width, y), (42, 45, 50), 1)
        for x in range(0, self.width, 20):
            cv2.line(img, (x, 0), (x, self.height), (42, 45, 50), 1)

        cx, cy = self.width // 2, self.height // 2
        hole_radius = 45

        # Draw physical hole on board
        cv2.circle(img, (cx, cy), hole_radius + 4, (20, 20, 22), -1)
        cv2.circle(img, (cx, cy), hole_radius, (10, 10, 12), -1)
        cv2.circle(img, (cx, cy), hole_radius, (90, 95, 105), 2)

        # Draw inspection state elements
        if self.active_state in ["INSERTING", "VERIFYING", "SUCCESS"]:
            # Draw needle/thread entering hole
            thread_color = (0, 220, 100) if self.active_state == "SUCCESS" else (40, 180, 240)
            cv2.line(img, (cx, 0), (cx, cy), thread_color, 4)
            cv2.circle(img, (cx, cy), 8, thread_color, -1)
            # Add fibrous texture lines
            cv2.line(img, (cx - 4, cy - 10), (cx + 6, cy + 12), (255, 255, 255), 1)
            cv2.line(img, (cx + 5, cy - 8), (cx - 5, cy + 8), (255, 255, 255), 1)
        elif self.active_state == "FAILED":
            # Red warning outline around hole
            cv2.circle(img, (cx, cy), hole_radius + 8, (0, 0, 220), 3)

        # Draw precision alignment crosshair
        cv2.line(img, (cx - 20, cy), (cx + 20, cy), (0, 255, 200), 1)
        cv2.line(img, (cx, cy - 20), (cx, cy + 20), (0, 255, 200), 1)
        cv2.circle(img, (cx, cy), 15, (0, 255, 200), 1)

        # Draw live HUD overlay
        timestamp_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
        cv2.putText(img, f"LIVE CAM #{self.device_index} [SIM]", (15, 25), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 150), 1)
        cv2.putText(img, f"TIME: {timestamp_str}", (15, 45), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (200, 200, 200), 1)
        cv2.putText(img, f"TARGET HOLE: {self.active_hole_label}", (15, self.height - 35), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (255, 255, 255), 1)
        
        status_color = (0, 255, 0) if self.active_state == "SUCCESS" else ((0, 0, 255) if self.active_state == "FAILED" else (0, 200, 255))
        cv2.putText(img, f"STATUS: {self.active_state}", (15, self.height - 15), cv2.FONT_HERSHEY_SIMPLEX, 0.55, status_color, 2)

        return img

    def _generate_error_frame(self, message: str) -> np.ndarray:
        img = np.zeros((self.height, self.width, 3), dtype=np.uint8)
        img[:] = (20, 20, 25)
        cv2.putText(img, message, (self.width // 2 - 120, self.height // 2), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
        return img

    def get_status(self) -> Dict[str, Any]:
        return {
            "is_connected": self.is_connected,
            "device_index": self.device_index,
            "synthetic_mode": self.use_synthetic,
            "resolution": f"{self.width}x{self.height}",
            "fps": self.fps,
            "active_hole": self.active_hole_label,
            "active_state": self.active_state
        }


camera_service = CameraService()
