import os
import cv2
import pytest
import numpy as np
from app.vision.hole_detector import detect_holes_in_image, HoleDetectionConfig
from app.vision.coordinate_mapper import CoordinateMapper
from app.vision.calibration import compute_calibration_homography, CalibrationPoint
from app.vision.verification import verify_insertion


def test_hole_detection_pipeline():
    # Create simple synthetic test image with 6 dark circles on light background
    img = np.full((300, 400, 3), 240, dtype=np.uint8)
    centers = [(100, 100), (200, 100), (300, 100), (100, 200), (200, 200), (300, 200)]
    for cx, cy in centers:
        cv2.circle(img, (cx, cy), 10, (30, 30, 30), -1)

    config = HoleDetectionConfig(min_radius=5.0, max_radius=20.0, dark_holes=True)
    holes, metadata = detect_holes_in_image(img, config)

    assert len(holes) == 6
    assert metadata["final_holes_count"] == 6
    assert metadata["total_rows"] == 2

    # Check labels: A1, A2, A3 and B1, B2, B3
    labels = [h["label"] for h in holes]
    assert labels == ["A1", "A2", "A3", "B1", "B2", "B3"]


def test_calibration_and_coordinate_mapper():
    # 4 reference points mapping image (0..500) to machine mm (0..100)
    pts = [
        CalibrationPoint(image_x=100.0, image_y=100.0, machine_x=0.0, machine_y=0.0),
        CalibrationPoint(image_x=900.0, image_y=100.0, machine_x=200.0, machine_y=0.0),
        CalibrationPoint(image_x=900.0, image_y=900.0, machine_x=200.0, machine_y=200.0),
        CalibrationPoint(image_x=100.0, image_y=900.0, machine_x=0.0, machine_y=200.0),
    ]

    is_valid, H, mean_err, pt_errors, msg = compute_calibration_homography(pts)

    assert is_valid is True
    assert H is not None
    assert mean_err < 1.0

    mapper = CoordinateMapper(homography_matrix=H)
    mx, my = mapper.image_to_machine(500.0, 500.0)
    # Center of image should map to center of machine (100, 100)
    assert abs(mx - 100.0) < 1.0
    assert abs(my - 100.0) < 1.0


def test_verification_module():
    # Frame with texture/lines indicating inserted thread
    frame = np.full((480, 640, 3), 40, dtype=np.uint8)
    cv2.circle(frame, (320, 240), 30, (10, 10, 10), -1)
    # Draw clear bright thread lines
    cv2.line(frame, (320, 0), (320, 240), (0, 255, 100), 5)
    cv2.circle(frame, (320, 240), 10, (0, 255, 100), -1)
    for i in range(-15, 16, 5):
        cv2.line(frame, (320 + i, 220), (320 - i, 260), (255, 255, 255), 2)

    expected = {"camera_x": 320, "camera_y": 240}
    res = verify_insertion(frame, expected, min_confidence_threshold=0.5)

    assert res["success"] is True
    assert res["reason"] == "THREAD_DETECTED"
    assert res["confidence"] >= 0.5
