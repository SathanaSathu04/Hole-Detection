import os
import cv2
import numpy as np
from typing import List, Dict, Any, Tuple, Optional
from app.vision.hole_detector import detect_holes_in_image, HoleDetectionConfig
from app.vision.coordinate_mapper import CoordinateMapper


def process_board_image_file(
    image_path: str,
    config: Optional[HoleDetectionConfig] = None,
    calibration_matrix_json: Optional[str] = None
) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    """
    Loads an image file, runs hole detection, maps coordinates to board and machine mm,
    and returns holes list and metadata.
    """
    if not os.path.exists(image_path):
        raise FileNotFoundError(f"Image file not found at: {image_path}")

    # Use cv2.imdecode to support Unicode / Windows file paths reliably
    with open(image_path, "rb") as f:
        file_bytes = np.frombuffer(f.read(), np.uint8)
        image_bgr = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)

    if image_bgr is None:
        raise ValueError(f"Could not decode valid image from {image_path}")

    holes, metadata = detect_holes_in_image(image_bgr, config)

    # Initialize CoordinateMapper
    mapper = CoordinateMapper.from_json(calibration_matrix_json) if calibration_matrix_json else CoordinateMapper()

    # Apply coordinate transformations
    if holes:
        coords_img = np.array([[h["image_x"], h["image_y"]] for h in holes], dtype=np.float64)
        mach_coords = mapper.batch_image_to_machine(coords_img)

        for i, h in enumerate(holes):
            mx, my = round(float(mach_coords[i, 0]), 2), round(float(mach_coords[i, 1]), 2)
            h["machine_x"] = mx
            h["machine_y"] = my
            h["board_x"] = mx  # In default setup, board coordinates align with machine frame
            h["board_y"] = my

    return holes, metadata
