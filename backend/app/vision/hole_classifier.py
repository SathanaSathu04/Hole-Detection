import numpy as np
from typing import List, Dict, Any, Tuple


def index_to_excel_row_name(index: int) -> str:
    """
    Convert 0-based integer index to Excel-style row name.
    0 -> A, 1 -> B, ..., 25 -> Z, 26 -> AA, 27 -> AB, ..., 51 -> AZ, 52 -> BA, etc.
    Supports practically unlimited rows (thousands/millions).
    """
    if index < 0:
        raise ValueError("Index must be non-negative")
    
    result = []
    index += 1  # Convert to 1-based for conversion algorithm
    while index > 0:
        index, remainder = divmod(index - 1, 26)
        result.append(chr(65 + remainder))
    return "".join(reversed(result))


def excel_row_name_to_index(name: str) -> int:
    """
    Convert Excel-style row name (e.g., 'A', 'Z', 'AA', 'AB') back to 0-based integer index.
    """
    name = name.upper().strip()
    result = 0
    for char in name:
        if not ('A' <= char <= 'Z'):
            raise ValueError(f"Invalid character '{char}' in Excel row name")
        result = result * 26 + (ord(char) - ord('A') + 1)
    return result - 1


def group_and_number_holes(
    hole_candidates: List[Dict[str, Any]],
    row_tolerance_px: float = 15.0
) -> List[Dict[str, Any]]:
    """
    Takes a list of detected hole dictionaries with 'image_x', 'image_y', 'radius'
    1. Clusters/groups holes into distinct horizontal rows based on Y coordinate.
    2. Sorts each row from top-to-bottom.
    3. Sorts holes inside each row from left-to-right (X coordinate).
    4. Generates Excel-style row names (A, B, ..., Z, AA, AB, ...) and 1-based column numbers.
    5. Returns structured list with label (e.g. 'A1', 'A2', 'B1'), row_number, column_number.
    """
    if not hole_candidates:
        return []

    # Sort all candidates by Y coordinate first
    sorted_by_y = sorted(hole_candidates, key=lambda h: h["image_y"])

    rows: List[List[Dict[str, Any]]] = []
    current_row: List[Dict[str, Any]] = []
    current_row_y_mean = 0.0

    for hole in sorted_by_y:
        y = hole["image_y"]
        if not current_row:
            current_row = [hole]
            current_row_y_mean = y
        else:
            # Check if hole belongs to the current row within tolerance
            if abs(y - current_row_y_mean) <= row_tolerance_px:
                current_row.append(hole)
                # Update running mean of Y for this row
                current_row_y_mean = sum(h["image_y"] for h in current_row) / len(current_row)
            else:
                # Start a new row
                rows.append(current_row)
                current_row = [hole]
                current_row_y_mean = y

    if current_row:
        rows.append(current_row)

    # Now sort rows by their mean Y to guarantee strictly increasing order
    rows.sort(key=lambda r: sum(h["image_y"] for h in r) / len(r))

    final_holes: List[Dict[str, Any]] = []

    for row_idx, row in enumerate(rows):
        row_name = index_to_excel_row_name(row_idx)
        # Sort holes inside this row by X (left to right)
        sorted_row = sorted(row, key=lambda h: h["image_x"])
        
        for col_idx, hole in enumerate(sorted_row):
            col_num = col_idx + 1
            label = f"{row_name}{col_num}"
            
            hole_data = {
                **hole,
                "label": label,
                "row_name": row_name,
                "row_number": row_idx + 1,  # 1-based row number
                "column_number": col_num,   # 1-based column number restarting per row
            }
            final_holes.append(hole_data)

    return final_holes
