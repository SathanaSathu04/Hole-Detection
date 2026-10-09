import pytest
from app.vision.hole_classifier import index_to_excel_row_name, excel_row_name_to_index, group_and_number_holes


def test_excel_row_naming():
    assert index_to_excel_row_name(0) == "A"
    assert index_to_excel_row_name(1) == "B"
    assert index_to_excel_row_name(25) == "Z"
    assert index_to_excel_row_name(26) == "AA"
    assert index_to_excel_row_name(27) == "AB"
    assert index_to_excel_row_name(51) == "AZ"
    assert index_to_excel_row_name(52) == "BA"
    assert index_to_excel_row_name(701) == "ZZ"
    assert index_to_excel_row_name(702) == "AAA"


def test_excel_row_index_reversal():
    for i in [0, 1, 25, 26, 27, 51, 52, 100, 701, 702, 5000]:
        name = index_to_excel_row_name(i)
        assert excel_row_name_to_index(name) == i


def test_group_and_number_holes():
    # Synthetic hole points in 2 rows
    raw_holes = [
        {"image_x": 100.0, "image_y": 50.0, "radius": 5.0},
        {"image_x": 50.0, "image_y": 52.0, "radius": 5.0},
        {"image_x": 150.0, "image_y": 49.0, "radius": 5.0},
        {"image_x": 60.0, "image_y": 120.0, "radius": 5.0},
        {"image_x": 120.0, "image_y": 119.0, "radius": 5.0},
    ]

    numbered = group_and_number_holes(raw_holes, row_tolerance_px=10.0)

    assert len(numbered) == 5
    # Row A should have 3 holes sorted by X: 50 -> 100 -> 150
    assert numbered[0]["label"] == "A1"
    assert numbered[0]["image_x"] == 50.0
    assert numbered[1]["label"] == "A2"
    assert numbered[1]["image_x"] == 100.0
    assert numbered[2]["label"] == "A3"
    assert numbered[2]["image_x"] == 150.0

    # Row B should have 2 holes sorted by X: 60 -> 120
    assert numbered[3]["label"] == "B1"
    assert numbered[3]["image_x"] == 60.0
    assert numbered[4]["label"] == "B2"
    assert numbered[4]["image_x"] == 120.0
