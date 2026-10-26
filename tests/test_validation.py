from video2pptx.validation.report import find_overlaps


def test_overlapping_objects_reported():
    assert find_overlaps([(0, 0, 2, 2), (1, 1, 1, 1), (5, 5, 1, 1)]) == [(0, 1)]

