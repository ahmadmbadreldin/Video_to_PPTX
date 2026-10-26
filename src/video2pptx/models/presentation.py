from __future__ import annotations

from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any
import json


@dataclass
class Element:
    kind: str
    bbox: tuple[float, float, float, float]
    text: str | None = None
    confidence: float = 1.0
    language: str | None = None
    role: str = "body"
    editable: bool = False
    asset_path: str | None = None
    reading_order: int = 0
    rtl: bool = False
    style: dict[str, Any] = field(default_factory=dict)
    warnings: list[str] = field(default_factory=list)


@dataclass
class AnimationEvent:
    time: float
    event: str
    region: tuple[float, float, float, float] | None = None
    confidence: float = 0.0
    description: str = ""


@dataclass
class Slide:
    index: int
    start: float
    end: float
    reference_frame: str
    width_px: int
    height_px: int
    boundary_confidence: float = 0.0
    semantic_type: str = "content"
    elements: list[Element] = field(default_factory=list)
    animations: list[AnimationEvent] = field(default_factory=list)
    state_frames: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


@dataclass
class PresentationModel:
    source: str
    project_id: str
    width_px: int
    height_px: int
    fps: float
    duration: float
    slides: list[Slide] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    version: str = "1.0"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def save(self, path: str | Path) -> None:
        Path(path).write_text(json.dumps(self.to_dict(), ensure_ascii=False, indent=2), encoding="utf-8")

    @classmethod
    def load(cls, path: str | Path) -> "PresentationModel":
        raw = json.loads(Path(path).read_text(encoding="utf-8"))
        raw["slides"] = [Slide(**{**s, "elements": [Element(**e) for e in s.get("elements", [])],
                                  "animations": [AnimationEvent(**a) for a in s.get("animations", [])]})
                         for s in raw.get("slides", [])]
        return cls(**raw)

