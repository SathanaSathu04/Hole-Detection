import cv2
import numpy as np
from typing import Dict, Any, Optional, Tuple


def verify_insertion(
    camera_frame: Optional[np.ndarray],
    expected_hole_info: Dict[str, Any],
    reference_frame: Optional[np.ndarray] = None,
    roi_radius_px: int = 40,
    min_confidence_threshold: float = 0.65
) -> Dict[str, Any]:
    """
    OpenCV-based thread/needle insertion verification at the expected hole position.
    
    Checks:
    1. Valid frame presence.
    2. Region of Interest (ROI) around hole center.
    3. Texture, edge density, and color changes indicative of inserted thread fibers.
    4. Differential comparison if reference frame before insertion is available.
    """
    if camera_frame is None or not isinstance(camera_frame, np.ndarray) or camera_frame.size == 0:
        return {
            "success": False,
            "confidence": 0.0,
            "reason": "CAMERA_ERROR",
            "details": "No valid frame received from camera"
        }

    frame_h, frame_w = camera_frame.shape[:2]
    
    # Target center in camera frame
    center_x = int(expected_hole_info.get("camera_x", expected_hole_info.get("image_x", frame_w // 2)))
    center_y = int(expected_hole_info.get("camera_y", expected_hole_info.get("image_y", frame_h // 2)))

    # Bound ROI inside frame
    x1 = max(0, center_x - roi_radius_px)
    y1 = max(0, center_y - roi_radius_px)
    x2 = min(frame_w, center_x + roi_radius_px)
    y2 = min(frame_h, center_y + roi_radius_px)

    if (x2 - x1) < 10 or (y2 - y1) < 10:
        return {
            "success": False,
            "confidence": 0.1,
            "reason": "WRONG_POSITION",
            "details": f"Target hole position ({center_x}, {center_y}) outside camera field of view"
        }

    roi = camera_frame[y1:y2, x1:x2]
    roi_gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)

    # 1. Edge and fiber density analysis using Canny and Sobel
    edges = cv2.Canny(roi_gray, 50, 150)
    edge_density = np.sum(edges > 0) / (edges.size + 1e-9)

    # 2. Local variance / contrast of hole center (presence of thread changes smooth hole into textured thread)
    local_std = float(np.std(roi_gray))

    # 3. Reference frame difference if available
    diff_score = 0.0
    if reference_frame is not None and reference_frame.shape == camera_frame.shape:
        ref_roi = reference_frame[y1:y2, x1:x2]
        ref_gray = cv2.cvtColor(ref_roi, cv2.COLOR_BGR2GRAY)
        diff = cv2.absdiff(roi_gray, ref_gray)
        diff_score = float(np.mean(diff) / 255.0)

    # Combined heuristic score
    # Edge density typically > 0.08 when thread is inserted, std > 25
    edge_factor = min(1.0, edge_density / 0.15)
    std_factor = min(1.0, local_std / 45.0)
    
    if reference_frame is not None:
        confidence = 0.4 * edge_factor + 0.3 * std_factor + 0.3 * min(1.0, diff_score * 3.0)
    else:
        confidence = 0.55 * edge_factor + 0.45 * std_factor

    confidence = round(float(np.clip(confidence, 0.05, 0.99)), 3)

    if confidence >= min_confidence_threshold:
        return {
            "success": True,
            "confidence": confidence,
            "reason": "THREAD_DETECTED",
            "details": f"Thread detected with {confidence*100:.1f}% confidence"
        }
    elif confidence < 0.35:
        return {
            "success": False,
            "confidence": confidence,
            "reason": "THREAD_NOT_DETECTED",
            "details": "No thread fibers or significant texture found in hole"
        }
    else:
        return {
            "success": False,
            "confidence": confidence,
            "reason": "LOW_CONFIDENCE",
            "details": f"Detection confidence {confidence:.2f} below required threshold {min_confidence_threshold:.2f}"
        }
