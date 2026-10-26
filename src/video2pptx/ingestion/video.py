from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterator
import math

SUPPORTED_EXTENSIONS = {".mp4", ".mov", ".mkv", ".webm"}


def _cv2():
    try:
        import cv2
        return cv2
    except ImportError as exc:
        raise RuntimeError("OpenCV is required for video processing. Install the package with: pip install -e .") from exc


@dataclass(frozen=True)
class VideoMetadata:
    width: int
    height: int
    fps: float
    duration: float
    frame_count: int
    aspect_ratio: float
    orientation: str


def validate_video(path: str | Path) -> Path:
    path = Path(path).expanduser().resolve()
    if not path.is_file():
        raise FileNotFoundError(f"Video not found: {path}")
    if path.suffix.lower() not in SUPPORTED_EXTENSIONS:
        raise ValueError(f"Unsupported video format {path.suffix!r}; expected MP4, MOV, MKV, or WEBM")
    if path.stat().st_size == 0:
        raise ValueError("Input video is empty")
    return path


class VideoReader:
    def __init__(self, path, crop=None):
        self.path = validate_video(path)
        self.crop = crop
        cv2 = _cv2()
        cap = cv2.VideoCapture(str(self.path))
        if not cap.isOpened():
            raise ValueError(f"OpenCV could not open video: {self.path}")
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        fps = float(cap.get(cv2.CAP_PROP_FPS) or 0)
        count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
        duration = count / fps if fps > 0 and count > 0 else float(cap.get(cv2.CAP_PROP_POS_MSEC) or 0) / 1000
        cap.release()
        if width <= 0 or height <= 0:
            raise ValueError("Video has invalid dimensions")
        self.metadata = VideoMetadata(width, height, fps, duration, count, width / height,
                                      "landscape" if width >= height else "portrait")

    def frames_at_timestamps(self, timestamps) -> Iterator[tuple[float, object]]:
        """Decode only requested timestamps. Timestamps, not frame numbers, support VFR input."""
        cv2 = _cv2()
        cap = cv2.VideoCapture(str(self.path))
        try:
            for requested in timestamps:
                if requested < 0 or (self.metadata.duration and requested > self.metadata.duration + 0.01):
                    continue
                cap.set(cv2.CAP_PROP_POS_MSEC, requested * 1000.0)
                ok, frame = cap.read()
                if not ok:
                    continue
                actual = float(cap.get(cv2.CAP_PROP_POS_MSEC) or requested * 1000) / 1000
                if self.crop:
                    x, y, w, h = self.crop
                    frame = frame[y:y + h, x:x + w]
                yield actual, frame
        finally:
            cap.release()

    def sample(self, interval=0.5):
        if interval <= 0:
            raise ValueError("Sampling interval must be positive")
        duration = self.metadata.duration
        if duration <= 0:
            raise ValueError("Video duration is unavailable")
        timestamps = (min(i * interval, duration) for i in range(int(math.ceil(duration / interval)) + 1))
        yield from self.frames_at_timestamps(timestamps)


def is_black_frame(frame, threshold=12):
    import numpy as np
    return float(np.mean(frame)) <= threshold

