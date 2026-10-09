import json
import numpy as np
from typing import List, Dict, Any, Tuple, Optional


class CoordinateMapper:
    """
    Transforms coordinates across three coordinate systems:
    1. Image Pixels (image_x, image_y)
    2. Board Millimeters (board_x, board_y)
    3. Machine Coordinates (machine_x, machine_y)
    """

    def __init__(self, homography_matrix: Optional[np.ndarray] = None, mm_per_pixel: float = 0.2):
        self.H = homography_matrix
        self.H_inv = None
        self.mm_per_pixel = mm_per_pixel
        if self.H is not None:
            try:
                self.H_inv = np.linalg.inv(self.H)
            except Exception:
                self.H_inv = None

    @classmethod
    def from_matrix_list(cls, matrix_list: List[List[float]]):
        if not matrix_list or len(matrix_list) != 3:
            return cls(None)
        H = np.array(matrix_list, dtype=np.float64)
        return cls(H)

    @classmethod
    def from_json(cls, json_str: str):
        if not json_str:
            return cls(None)
        try:
            mat = json.loads(json_str)
            return cls.from_matrix_list(mat)
        except Exception:
            return cls(None)

    def image_to_machine(self, image_x: float, image_y: float) -> Tuple[float, float]:
        """Convert single image pixel coordinate to machine mm coordinate."""
        if self.H is not None:
            vec = np.array([image_x, image_y, 1.0], dtype=np.float64)
            res = self.H @ vec
            denom = res[2] if abs(res[2]) > 1e-9 else 1.0
            return round(float(res[0] / denom), 3), round(float(res[1] / denom), 3)
        else:
            # Fallback linear approximation if not yet calibrated
            return round(image_x * self.mm_per_pixel, 3), round(image_y * self.mm_per_pixel, 3)

    def machine_to_image(self, machine_x: float, machine_y: float) -> Tuple[float, float]:
        """Convert machine mm coordinate back to image pixel coordinate."""
        if self.H_inv is not None:
            vec = np.array([machine_x, machine_y, 1.0], dtype=np.float64)
            res = self.H_inv @ vec
            denom = res[2] if abs(res[2]) > 1e-9 else 1.0
            return round(float(res[0] / denom), 2), round(float(res[1] / denom), 2)
        else:
            scale = self.mm_per_pixel if self.mm_per_pixel != 0 else 1.0
            return round(machine_x / scale, 2), round(machine_y / scale, 2)

    def batch_image_to_machine(self, coords: np.ndarray) -> np.ndarray:
        """
        Fast vectorized transformation for 10,000+ points simultaneously.
        coords shape: (N, 2) where col 0 is image_x, col 1 is image_y.
        Returns: (N, 2) array of (machine_x, machine_y).
        """
        N = coords.shape[0]
        if N == 0:
            return np.empty((0, 2), dtype=np.float64)

        if self.H is not None:
            ones = np.ones((N, 1), dtype=np.float64)
            homo = np.hstack([coords, ones])  # (N, 3)
            proj = (self.H @ homo.T).T       # (N, 3)
            z = proj[:, 2:3]
            z[np.abs(z) < 1e-9] = 1.0
            return proj[:, :2] / z
        else:
            return coords * self.mm_per_pixel

    def image_to_board(self, image_x: float, image_y: float, origin_offset: Tuple[float, float] = (0.0, 0.0)) -> Tuple[float, float]:
        """
        Calculate local board mm coordinates (relative to board top-left / origin).
        """
        raw_x, raw_y = self.image_to_machine(image_x, image_y)
        return round(raw_x - origin_offset[0], 3), round(raw_y - origin_offset[1], 3)
