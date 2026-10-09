import os
import cv2
import numpy as np


def generate_textile_board(
    rows: int = 15,
    cols: int = 20,
    hole_radius: int = 8,
    spacing_x: int = 35,
    spacing_y: int = 35,
    margin_x: int = 60,
    margin_y: int = 60,
    output_path: str = "sample_board.png",
    irregular_shape: bool = False
):
    width = margin_x * 2 + (cols - 1) * spacing_x
    height = margin_y * 2 + (rows - 1) * spacing_y

    # Board background: light cream/grey textile composite board
    board = np.full((height, width, 3), 235, dtype=np.uint8)

    # Subtle board texture and border
    cv2.rectangle(board, (15, 15), (width - 15, height - 15), (200, 200, 205), 3)

    # Calibration alignment fiducials at corners
    fiducials = [
        (35, 35),
        (width - 35, 35),
        (width - 35, height - 35),
        (35, height - 35),
    ]
    for fx, fy in fiducials:
        cv2.circle(board, (fx, fy), 12, (50, 50, 60), 2)
        cv2.drawMarker(board, (fx, fy), (50, 50, 60), cv2.MARKER_CROSS, 20, 2)

    total_holes = 0
    for r in range(rows):
        y = margin_y + r * spacing_y
        for c in range(cols):
            x = margin_x + c * spacing_x

            # If irregular shape is true, omit some corner/edge holes
            if irregular_shape:
                # Omit corners to create realistic non-rectangular board shape
                if (r < 3 and (c < 3 or c >= cols - 3)) or (r >= rows - 3 and (c < 3 or c >= cols - 3)):
                    continue

            # Draw crisp dark hole with subtle rim shadow
            cv2.circle(board, (x, y), hole_radius + 1, (100, 100, 105), 1)
            cv2.circle(board, (x, y), hole_radius, (25, 25, 30), -1)
            total_holes += 1

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    cv2.imwrite(output_path, board)
    print(f"Generated board: {output_path} with {total_holes} holes ({width}x{height}px)")
    return output_path, total_holes


if __name__ == "__main__":
    out_dir = os.path.join(os.path.dirname(__file__))
    
    # 1. Standard production board (300 holes)
    generate_textile_board(rows=15, cols=20, hole_radius=7, output_path=os.path.join(out_dir, "sample_board_300.png"), irregular_shape=True)
    
    # 2. Dense textile board (1,000 holes)
    generate_textile_board(rows=25, cols=40, hole_radius=6, spacing_x=25, spacing_y=25, output_path=os.path.join(out_dir, "sample_board_1000.png"), irregular_shape=True)
    
    # 3. High-density industrial board (5,000 holes)
    generate_textile_board(rows=50, cols=100, hole_radius=4, spacing_x=16, spacing_y=16, margin_x=40, margin_y=40, output_path=os.path.join(out_dir, "sample_board_5000.png"), irregular_shape=False)
