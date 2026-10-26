from dataclasses import dataclass


def pixel_bbox_to_inches(bbox, image_size, slide_size):
    x, y, w, h = bbox
    iw, ih = image_size
    sw, sh = slide_size
    if iw <= 0 or ih <= 0:
        raise ValueError("Image dimensions must be positive")
    return x / iw * sw, y / ih * sh, w / iw * sw, h / ih * sh


def rectangles_overlap(a, b, padding=0.0):
    ax, ay, aw, ah = a
    bx, by, bw, bh = b
    return not (ax + aw + padding <= bx or bx + bw + padding <= ax or
                ay + ah + padding <= by or by + bh + padding <= ay)


@dataclass(frozen=True)
class LogoPlacement:
    x: float
    y: float
    width: float
    height: float
    sidebar: str | None = None


def place_logo(position, slide_size, logo_aspect, scale=0.11, margin=0.25,
               sidebar_width=0.75, occupied=()):
    sw, sh = slide_size
    width = max(0.15, min(sw * scale, sw * 0.4))
    height = width / max(logo_aspect, 0.01)
    if height > sh * 0.22:
        height = sh * 0.22
        width = height * logo_aspect
    candidates = {
        "top-right": (sw - width - margin, margin),
        "top-left": (margin, margin),
        "bottom-right": (sw - width - margin, sh - height - margin),
        "bottom-left": (margin, sh - height - margin),
    }
    if position == "right-sidebar":
        if width > sidebar_width - 2 * min(margin, sidebar_width * 0.2):
            width = max(0.12, sidebar_width - 2 * min(margin, sidebar_width * 0.2))
            height = width / max(logo_aspect, 0.01)
        x = sw - sidebar_width + (sidebar_width - width) / 2
        return LogoPlacement(max(0, x), margin, width, height, "right")
    if position == "left-sidebar":
        if width > sidebar_width - 2 * min(margin, sidebar_width * 0.2):
            width = max(0.12, sidebar_width - 2 * min(margin, sidebar_width * 0.2))
            height = width / max(logo_aspect, 0.01)
        x = (sidebar_width - width) / 2
        return LogoPlacement(max(0, x), margin, width, height, "left")
    if position == "auto":
        for name in ("top-right", "bottom-right", "top-left", "bottom-left"):
            box = (*candidates[name], width, height)
            if not any(rectangles_overlap(box, item, 0.08) for item in occupied):
                return LogoPlacement(*candidates[name], width, height)
        return LogoPlacement(sw - sidebar_width + (sidebar_width - width) / 2,
                             margin, width, height, "right")
    if position not in candidates:
        raise ValueError(f"Unsupported logo position: {position}")
    return LogoPlacement(*candidates[position], width, height)

