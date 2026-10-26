from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class DetectionConfig:
    scene_threshold: float = 0.22
    animation_threshold: float = 0.035
    black_threshold: float = 12
    min_scene_seconds: float = 0.8
    preserve_revisits: bool = False


@dataclass
class FrameState:
    timestamp: float
    path: str
    fingerprint: int
    mean: float
    sharpness: float
    change: float = 0.0
    is_black: bool = False


@dataclass
class DetectedSlide:
    start: float
    end: float
    representative: FrameState
    states: list[FrameState] = field(default_factory=list)
    boundary_confidence: float = 0.0
    animation_events: list[dict] = field(default_factory=list)


def dhash(frame, size=8):
    import cv2
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY) if frame.ndim == 3 else frame
    small = cv2.resize(gray, (size + 1, size), interpolation=cv2.INTER_AREA)
    bits = small[:, 1:] > small[:, :-1]
    value = 0
    for bit in bits.flatten():
        value = (value << 1) | int(bit)
    return value


def hamming_distance(a, b, bits=64):
    return (int(a) ^ int(b)).bit_count() / bits


def frame_change(previous, current):
    """Robust normalized difference, downweighted for cursor-sized changes."""
    import cv2
    import numpy as np
    a = cv2.resize(previous, (160, 90), interpolation=cv2.INTER_AREA)
    b = cv2.resize(current, (160, 90), interpolation=cv2.INTER_AREA)
    delta = cv2.absdiff(a, b)
    gray = cv2.cvtColor(delta, cv2.COLOR_BGR2GRAY)
    changed = float(np.mean(gray > 18))
    magnitude = float(np.mean(gray)) / 255.0
    # Presentation changes are spatially sparse compared with natural video. Scale the
    # combined signal so a full background/title replacement crosses the default scene
    # threshold while a new bullet normally remains an animation-sized event.
    return min(1.0, (0.72 * changed + 0.28 * magnitude) * 10.0)


def classify_boundaries(changes, config=None):
    """Classify a sequence of (timestamp, change) into slide vs animation events."""
    config = config or DetectionConfig()
    result = []
    for timestamp, change in changes:
        if change >= config.scene_threshold:
            kind = "slide"
        elif change >= config.animation_threshold:
            kind = "animation"
        else:
            kind = "noise"
        result.append((timestamp, kind, min(1.0, change / max(config.scene_threshold, 1e-9))))
    return result


def detect_slides(states, config=None):
    config = config or DetectionConfig()
    usable = [s for s in states if not s.is_black]
    if not usable:
        return []
    slides, current = [], [usable[0]]
    events = []
    for state in usable[1:]:
        if state.change >= config.scene_threshold and state.timestamp - current[0].timestamp >= config.min_scene_seconds:
            best = max(current[-min(3, len(current)):], key=lambda s: s.sharpness)
            slides.append(DetectedSlide(current[0].timestamp, current[-1].timestamp, best, current, state.change, events))
            current, events = [state], []
        else:
            if state.change >= config.animation_threshold:
                events.append({"time": state.timestamp, "event": "visual-change", "confidence": min(1.0, state.change / config.scene_threshold)})
            current.append(state)
    best = max(current[-min(3, len(current)):], key=lambda s: s.sharpness)
    slides.append(DetectedSlide(current[0].timestamp, current[-1].timestamp, best, current, 0.7, events))
    if not config.preserve_revisits:
        deduped = []
        for slide in slides:
            previous = deduped[-1].representative if deduped else None
            # dHash alone intentionally ignores color and can collapse two slides with
            # the same template but different words. Require luminance agreement too.
            if (previous and hamming_distance(previous.fingerprint, slide.representative.fingerprint) < 0.045
                    and abs(previous.mean - slide.representative.mean) < 2.0):
                deduped[-1].end = slide.end
                deduped[-1].states.extend(slide.states)
                deduped[-1].animation_events.extend(slide.animation_events)
            else:
                deduped.append(slide)
        slides = deduped
    return slides


def group_animation_states(fingerprints, times, scene_threshold=0.22, animation_threshold=0.035):
    """Pure grouping helper used by tests and advanced adapters."""
    if not fingerprints:
        return []
    groups = [{"start": times[0], "states": [0], "events": []}]
    for i in range(1, len(fingerprints)):
        change = hamming_distance(fingerprints[i - 1], fingerprints[i])
        if change >= scene_threshold:
            groups.append({"start": times[i], "states": [i], "events": []})
        else:
            groups[-1]["states"].append(i)
            if change >= animation_threshold:
                groups[-1]["events"].append({"time": times[i], "event": "visual-change", "confidence": change / scene_threshold})
    return groups

