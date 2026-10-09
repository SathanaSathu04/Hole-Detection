import cv2
import numpy as np
from typing import List, Dict, Any, Optional, Tuple
from pydantic import BaseModel, Field
from app.vision.hole_classifier import group_and_number_holes


class HoleDetectionConfig(BaseModel):
    min_radius: float = Field(default=3.0, description="Minimum hole radius in pixels")
    max_radius: float = Field(default=50.0, description="Maximum hole radius in pixels")
    min_circularity: float = Field(default=0.60, description="Circularity threshold (4*pi*Area / Perimeter^2)")
    min_distance: float = Field(default=6.0, description="Minimum Euclidean distance between hole centers")
    blur_ksize: int = Field(default=5, description="Gaussian blur kernel size (odd integer)")
    contrast_alpha: float = Field(default=1.2, description="Contrast adjustment factor")
    brightness_beta: int = Field(default=0, description="Brightness adjustment")
    threshold_method: str = Field(default="adaptive_gaussian", description="'adaptive_gaussian', 'otsu', or 'manual'")
    manual_threshold_value: int = Field(default=120, description="Threshold value if manual method used")
    dark_holes: bool = Field(default=True, description="True if holes are darker than background")
    row_tolerance_px: float = Field(default=15.0, description="Row grouping tolerance in pixels")


def detect_holes_in_image(
    image_bgr: np.ndarray,
    config: Optional[HoleDetectionConfig] = None
) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    """
    Complete computer vision pipeline for textile hole detection.
    Returns:
      - list of numbered hole dicts with label, row, col, image_x, image_y, radius
      - metadata dict with processing metrics
    """
    if config is None:
        config = HoleDetectionConfig()

    height, width = image_bgr.shape[:2]
    
    # 1. Grayscale
    gray = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2GRAY)

    # 2. Contrast/Brightness adjustment
    if config.contrast_alpha != 1.0 or config.brightness_beta != 0:
        adjusted = cv2.convertScaleAbs(gray, alpha=config.contrast_alpha, beta=config.brightness_beta)
    else:
        adjusted = gray

    # 3. Gaussian Blur for noise reduction
    ksize = config.blur_ksize if config.blur_ksize % 2 == 1 else config.blur_ksize + 1
    blurred = cv2.GaussianBlur(adjusted, (ksize, ksize), 0)

    # 4. Thresholding
    if config.threshold_method == "otsu":
        flag = cv2.THRESH_BINARY_INV if config.dark_holes else cv2.THRESH_BINARY
        _, thresh = cv2.threshold(blurred, 0, 255, flag + cv2.THRESH_OTSU)
    elif config.threshold_method == "manual":
        flag = cv2.THRESH_BINARY_INV if config.dark_holes else cv2.THRESH_BINARY
        _, thresh = cv2.threshold(blurred, config.manual_threshold_value, 255, flag)
    else:
        # Default: Adaptive Gaussian
        flag = cv2.THRESH_BINARY_INV if config.dark_holes else cv2.THRESH_BINARY
        thresh = cv2.adaptiveThreshold(
            blurred, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, flag, 21, 5
        )

    # 5. Morphological cleanup (open to remove small noise, close to solidify contours)
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
    cleaned = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, kernel, iterations=1)

    # 6. Find contours
    contours, _ = cv2.findContours(cleaned, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    candidates: List[Dict[str, Any]] = []
    min_area = np.pi * (config.min_radius ** 2) * 0.6
    max_area = np.pi * (config.max_radius ** 2) * 1.5

    for cnt in contours:
        area = cv2.contourArea(cnt)
        if area < min_area or area > max_area:
            continue

        perimeter = cv2.arcLength(cnt, True)
        if perimeter == 0:
            continue

        # Circularity measure: 4 * pi * Area / (Perimeter^2)
        circularity = 4 * np.pi * (area / (perimeter * perimeter))
        if circularity < config.min_circularity:
            continue

        # Fit minimum enclosing circle
        (cx, cy), radius = cv2.minEnclosingCircle(cnt)

        if radius < config.min_radius or radius > config.max_radius:
            continue

        # Moments for sub-pixel centroid accuracy
        M = cv2.moments(cnt)
        if M["m00"] != 0:
            centroid_x = float(M["m10"] / M["m00"])
            centroid_y = float(M["m01"] / M["m00"])
        else:
            centroid_x = float(cx)
            centroid_y = float(cy)

        candidates.append({
            "image_x": round(centroid_x, 2),
            "image_y": round(centroid_y, 2),
            "radius": round(float(radius), 2),
            "area": round(float(area), 2),
            "circularity": round(float(circularity), 3)
        })

    # 7. Deduplication (eliminate multiple hits within min_distance)
    deduped: List[Dict[str, Any]] = []
    min_dist_sq = config.min_distance ** 2

    # Sort candidates by area descending so best detections are retained
    candidates_sorted = sorted(candidates, key=lambda c: c["area"], reverse=True)
    for cand in candidates_sorted:
        x, y = cand["image_x"], cand["image_y"]
        is_duplicate = False
        for kept in deduped:
            dx = x - kept["image_x"]
            dy = y - kept["image_y"]
            if (dx * dx + dy * dy) < min_dist_sq:
                is_duplicate = True
                break
        if not is_duplicate:
            deduped.append(cand)

    # 8. Row grouping and Excel numbering
    numbered_holes = group_and_number_holes(deduped, row_tolerance_px=config.row_tolerance_px)

    metadata = {
        "image_width": width,
        "image_height": height,
        "raw_contours_found": len(contours),
        "candidates_passed_filter": len(candidates),
        "deduplicated_holes": len(deduped),
        "final_holes_count": len(numbered_holes),
        "total_rows": len(set(h["row_number"] for h in numbered_holes)) if numbered_holes else 0
    }

    return numbered_holes, metadata
