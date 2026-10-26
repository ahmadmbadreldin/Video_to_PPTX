from __future__ import annotations

from html import escape
from pathlib import Path


def find_overlaps(boxes, tolerance=0.02):
    from video2pptx.layout.geometry import rectangles_overlap
    found = []
    for i, a in enumerate(boxes):
        for j, b in enumerate(boxes[i + 1:], i + 1):
            if rectangles_overlap(a, b, -tolerance):
                found.append((i, j))
    return found


def write_accuracy_report(model, output, previews=()):
    slides = []
    for slide in model.slides:
        editable = sum(e.editable for e in slide.elements)
        confidence = sum((e.confidence for e in slide.elements), 0) / max(1, len(slide.elements))
        warnings = "".join(f"<li>{escape(w)}</li>" for w in slide.warnings)
        slides.append(f"""<section><h2>Slide {slide.index + 1}</h2>
        <p>Boundary confidence: {slide.boundary_confidence:.0%} · OCR confidence: {confidence:.0%} ·
        Editable elements: {editable}/{len(slide.elements)} · Animation events: {len(slide.animations)}</p>
        <ul>{warnings or '<li>No slide-specific warnings.</li>'}</ul></section>""")
    cards = "".join(f'<img src="{escape(Path(p).as_posix())}" alt="slide preview">' for p in previews)
    html = f"""<!doctype html><html><head><meta charset="utf-8"><title>Video2BrandedPPTX accuracy report</title>
    <style>body{{font:15px system-ui;margin:2rem;max-width:1100px;color:#1f2937}}header{{border-left:8px solid #2f75b5;padding-left:1rem}}section{{border-top:1px solid #ddd;padding:1rem 0}}img{{width:46%;margin:1%;border:1px solid #ccc}}.notice{{background:#fff7ed;padding:1rem}}</style></head>
    <body><header><h1>Reconstruction accuracy report</h1><p>{len(model.slides)} detected slides from {escape(model.source)}</p></header>
    <p class="notice"><strong>Important:</strong> This pipeline reconstructs from visual evidence. Image similarity is not proof of factual correctness. Low-confidence OCR, ambiguous transitions, charts, diagrams and animations require human review.</p>
    {''.join(slides)}<h2>Before/after previews</h2><div>{cards}</div>
    <h2>Known limits</h2><p>Video cannot reveal hidden source data, exact fonts, master layouts, speaker notes, hyperlinks, or unsupported animation parameters. Charts and complex diagrams remain raster assets unless their data can be recovered reliably.</p></body></html>"""
    Path(output).write_text(html, encoding="utf-8")
    return output
