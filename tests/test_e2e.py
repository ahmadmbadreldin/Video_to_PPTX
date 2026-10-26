from pathlib import Path

import cv2
import numpy as np

from video2pptx.pipeline import ConversionOptions, convert


def make_video(path):
    writer = cv2.VideoWriter(str(path), cv2.VideoWriter_fourcc(*"mp4v"), 4, (640, 360))
    if not writer.isOpened():
        raise RuntimeError("Test OpenCV build cannot encode mp4v")
    for page, color in [("Q3 RESULTS", (245, 245, 245)), ("ROADMAP 2027", (220, 240, 255))]:
        for frame_no in range(12):
            frame = np.full((360, 640, 3), color, np.uint8)
            cv2.putText(frame, page, (60, 100), cv2.FONT_HERSHEY_SIMPLEX, 1.4, (20, 30, 50), 3)
            if frame_no >= 4:
                cv2.putText(frame, "Revenue 12.5%", (80, 210), cv2.FONT_HERSHEY_SIMPLEX, .8, (30, 80, 120), 2)
            writer.write(frame)
    writer.release()


def test_reproducible_end_to_end_sample(tmp_path):
    video = tmp_path / "sample.mp4"; make_video(video)
    out = tmp_path / "out"
    options = ConversionOptions(out, ocr_enabled=False, sample_interval=.5, scene_threshold=.18,
                                animation_threshold=.01)
    results = convert(video, options)
    for key in ("reference", "branded", "hybrid", "model", "report", "previews"):
        assert Path(results[key]).exists()
    assert (out / "manifest.json").exists()

