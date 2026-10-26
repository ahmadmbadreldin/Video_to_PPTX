from video2pptx.scenes.detector import DetectionConfig, FrameState, classify_boundaries, detect_slides, group_animation_states


def state(t, fp, change, sharp=10):
    return FrameState(t, f"{t}.jpg", fp, 100, sharp, change, False)


def test_scene_boundary_detection():
    labels = classify_boundaries([(1, .01), (2, .08), (3, .4)], DetectionConfig())
    assert [x[1] for x in labels] == ["noise", "animation", "slide"]


def test_deduplication_of_repeated_boundary_state():
    states = [state(0, 0, 0), state(1, 0, .01), state(2, 0, .4), state(3, 0, .01)]
    slides = detect_slides(states, DetectionConfig(min_scene_seconds=.5))
    assert len(slides) == 1


def test_animation_grouping_does_not_make_slide_per_state():
    base = 0
    small = (1 << 4) - 1
    different = (1 << 40) - 1
    groups = group_animation_states([base, small, different], [0, 1, 2], scene_threshold=.4, animation_threshold=.03)
    assert len(groups) == 2
    assert len(groups[0]["events"]) == 1


def test_black_frames_ignored():
    black = state(0, 0, 0); black.is_black = True
    assert len(detect_slides([black, state(1, 1, 0)])) == 1

