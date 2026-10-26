from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
import json
import re

POSITIONS = {"auto", "top-right", "top-left", "right-sidebar", "left-sidebar", "bottom-right", "bottom-left"}


@dataclass
class BrandConfig:
    company_name: str = ""
    primary_color: str = "17365D"
    accent_color: str = "2F75B5"
    background_color: str = "FFFFFF"
    text_color: str = "1F2937"
    font_family: str = "Aptos"
    title_font_family: str = "Aptos Display"
    logo_position: str = "auto"
    logo_scale: float = 0.11
    logo_margin_inches: float = 0.25
    sidebar_width_inches: float = 0.75
    logo_opacity: float = 1.0
    footer_text: str = ""
    show_slide_numbers: bool = True
    exclude_title_slide: bool = False
    exclude_closing_slide: bool = False

    def __post_init__(self):
        for name in ("primary_color", "accent_color", "background_color", "text_color"):
            value = getattr(self, name).lstrip("#")
            if not re.fullmatch(r"[0-9A-Fa-f]{6}", value):
                raise ValueError(f"{name} must be a six-digit hex color")
            setattr(self, name, value.upper())
        if self.logo_position not in POSITIONS:
            raise ValueError(f"logo_position must be one of {sorted(POSITIONS)}")
        if not 0.02 <= self.logo_scale <= 0.4:
            raise ValueError("logo_scale must be between 0.02 and 0.4")
        if not 0 <= self.logo_opacity <= 1:
            raise ValueError("logo_opacity must be between 0 and 1")
        if not 0.35 <= self.sidebar_width_inches <= 3:
            raise ValueError("sidebar_width_inches must be between 0.35 and 3")

    @classmethod
    def load(cls, path=None):
        if not path:
            return cls()
        raw = json.loads(Path(path).read_text(encoding="utf-8"))
        raw.pop("$schema", None)
        known = set(cls.__dataclass_fields__)
        extra = set(raw) - known
        if extra:
            raise ValueError(f"Unknown brand configuration fields: {sorted(extra)}")
        return cls(**raw)

    def to_dict(self):
        return asdict(self)
