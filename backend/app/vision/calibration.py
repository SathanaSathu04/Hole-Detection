import json
import cv2
import numpy as np
from typing import List, Dict, Any, Tuple, Optional
from pydantic import BaseModel, Field


class CalibrationPoint(BaseModel):
    image_x: float
    image_y: float
    machine_x: float
    machine_y: float
    board_x: Optional[float] = None
    board_y: Optional[float] = None


class CalibrationRequest(BaseModel):
    board_id: Optional[str] = None
    name: str = "Standard Calibration"
    reference_points: List[CalibrationPoint]
    machine_origin: Optional[List[float]] = [0.0, 0.0, 0.0]
    board_dimensions: Optional[Dict[str, float]] = None


class CalibrationResult(BaseModel):
    is_valid: bool
    reprojection_error: float
    transformation_matrix: List[List[float]]
    inverse_matrix: List[List[float]]
    reference_points_error: List[Dict[str, Any]]
    message: str


def compute_calibration_homography(
    points: List[CalibrationPoint]
) -> Tuple[bool, Optional[np.ndarray], float, List[Dict[str, Any]], str]:
    """
    Computes 3x3 planar homography matrix from image coordinates to machine coordinates.
    Requires at least 4 non-collinear reference points.
    """
    if len(points) < 4:
        return False, None, 0.0, [], f"At least 4 reference points required, got {len(points)}"

    src_pts = np.array([[p.image_x, p.image_y] for p in points], dtype=np.float32)
    dst_pts = np.array([[p.machine_x, p.machine_y] for p in points], dtype=np.float32)

    # Compute homography with RANSAC
    H, mask = cv2.findHomography(src_pts, dst_pts, cv2.RANSAC, 5.0)

    if H is None or np.isnan(H).any() or np.isinf(H).any():
        # Fallback to least squares
        H, _ = cv2.findHomography(src_pts, dst_pts, 0)

    if H is None:
        return False, None, 0.0, [], "Failed to compute homography matrix from points"

    # Calculate reprojection errors
    src_homo = np.hstack([src_pts, np.ones((len(src_pts), 1), dtype=np.float32)])
    projected = (H @ src_homo.T).T
    projected_xy = projected[:, :2] / (projected[:, 2:3] + 1e-12)

    errors = np.linalg.norm(projected_xy - dst_pts, axis=1)
    mean_error = float(np.mean(errors))

    point_errors = []
    for idx, p in enumerate(points):
        point_errors.append({
            "point_index": idx + 1,
            "image": [p.image_x, p.image_y],
            "machine_actual": [p.machine_x, p.machine_y],
            "machine_projected": [round(float(projected_xy[idx, 0]), 3), round(float(projected_xy[idx, 1]), 3)],
            "error_mm": round(float(errors[idx]), 4)
        })

    is_valid = mean_error < 5.0  # Acceptable threshold (mm)
    msg = f"Calibration successful. Mean reprojection error: {mean_error:.3f} mm" if is_valid else f"Mean error {mean_error:.3f} mm exceeds tolerance (5.0 mm)"

    return is_valid, H, round(mean_error, 4), point_errors, msg
