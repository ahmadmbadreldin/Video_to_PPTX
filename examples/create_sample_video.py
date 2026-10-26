"""Create a small deterministic screen-recording-like MP4 for a local smoke test."""
from pathlib import Path
import cv2
import numpy as np

target = Path(__file__).with_name("sample_presentation.mp4")
writer = cv2.VideoWriter(str(target), cv2.VideoWriter_fourcc(*"mp4v"), 6, (1280, 720))
if not writer.isOpened():
    raise SystemExit("This OpenCV build cannot encode MP4")
for title, bullet, color in [("Quarterly Results", "Revenue grew 12.5%", (250, 250, 250)),
                             ("Product Roadmap", "Launch: January 2027", (235, 245, 255))]:
    for frame_no in range(24):
        frame = np.full((720, 1280, 3), color, np.uint8)
        cv2.rectangle(frame, (0, 0), (1280, 24), (180, 90, 30), -1)
        cv2.putText(frame, title, (90, 150), cv2.FONT_HERSHEY_SIMPLEX, 2, (30, 40, 60), 4)
        if frame_no >= 8:
            cv2.putText(frame, bullet, (120, 360), cv2.FONT_HERSHEY_SIMPLEX, 1.2, (40, 80, 130), 3)
        writer.write(frame)
writer.release()
print(target)
