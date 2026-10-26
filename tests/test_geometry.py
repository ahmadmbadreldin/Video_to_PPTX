import pytest

from video2pptx.layout.geometry import pixel_bbox_to_inches, place_logo, rectangles_overlap


def test_coordinate_conversion():
    assert pixel_bbox_to_inches((960, 540, 480, 270), (1920, 1080), (13.333, 7.5)) == pytest.approx((6.6665, 3.75, 3.33325, 1.875))


def test_aspect_ratio_logo_preserved():
    placement = place_logo("top-right", (13.333, 7.5), 2.0, scale=0.1)
    assert placement.width / placement.height == pytest.approx(2.0)
    assert placement.x + placement.width <= 13.333


def test_sidebar_is_reserved():
    placement = place_logo("right-sidebar", (13.333, 7.5), 1.0, sidebar_width=1.0)
    assert placement.sidebar == "right"
    assert placement.x >= 12.333


def test_auto_avoids_occupied_corner():
    result = place_logo("auto", (10, 7.5), 1.0, occupied=[(8.5, 0, 1.5, 2)])
    assert result.y > 5


def test_overlap_detection():
    assert rectangles_overlap((0, 0, 2, 2), (1, 1, 2, 2))
    assert not rectangles_overlap((0, 0, 1, 1), (1, 0, 1, 1))

