from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
import hashlib
import json
import logging
import shutil

from video2pptx.branding import BrandConfig
from video2pptx.ingestion.video import VideoReader, is_black_frame
from video2pptx.models import AnimationEvent, Element, PresentationModel, Slide
from video2pptx.ocr import OCREngine
from video2pptx.reconstruction import build_presentation
from video2pptx.rendering import create_contact_sheet, create_redesign_preview
from video2pptx.scenes.detector import DetectionConfig, FrameState, detect_slides, dhash, frame_change
from video2pptx.validation import write_accuracy_report

LOG = logging.getLogger("video2pptx")


@dataclass
class ConversionOptions:
    output_dir: Path
    logo: Path | None = None
    theme: str = "corporate"
    mode: str = "hybrid"
    redesign: str = "moderate"
    brand_config: Path | None = None
    ocr_languages: tuple[str, ...] = ("eng",)
    ocr_enabled: bool = True
    min_ocr_confidence: int = 55
    sample_interval: float = 0.5
    scene_threshold: float = 0.22
    animation_threshold: float = 0.035
    preserve_revisits: bool = False
    preserve_animation_stages: bool = True
    native_animations: bool = False
    outputs: set[str] = field(default_factory=lambda: {"reference", "branded", "hybrid", "model", "report", "previews"})
    resume: bool = True


def project_id(path):
    path = Path(path)
    stat = path.stat()
    value = f"{path.resolve()}:{stat.st_size}:{stat.st_mtime_ns}".encode()
    return hashlib.sha256(value).hexdigest()[:16]


def _save_frame(frame, path):
    import cv2
    path.parent.mkdir(parents=True, exist_ok=True)
    if not cv2.imwrite(str(path), frame, [cv2.IMWRITE_JPEG_QUALITY, 94]):
        raise OSError(f"Could not write extracted frame: {path}")


def analyze_video(video, options, progress=None):
    reader = VideoReader(video)
    pid = project_id(video)
    out = options.output_dir.resolve(); cache = out / ".cache" / pid
    checkpoint = cache / "presentation_model.json"
    if options.resume and checkpoint.exists():
        LOG.info("Resuming from %s", checkpoint)
        return PresentationModel.load(checkpoint)
    assets = out / "extracted_assets"; cache.mkdir(parents=True, exist_ok=True); assets.mkdir(parents=True, exist_ok=True)
    states, previous = [], None
    for i, (timestamp, frame) in enumerate(reader.sample(options.sample_interval)):
        path = cache / f"frame_{i:06d}.jpg"; _save_frame(frame, path)
        import cv2
        import numpy as np
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        change = frame_change(previous, frame) if previous is not None else 0.0
        states.append(FrameState(timestamp, str(path), dhash(frame), float(np.mean(gray)),
                                 float(cv2.Laplacian(gray, cv2.CV_64F).var()), change,
                                 is_black_frame(frame)))
        previous = frame
        if progress:
            progress(min(0.45, (timestamp / max(reader.metadata.duration, 0.01)) * 0.45), f"Sampling video at {timestamp:.1f}s")
    detected = detect_slides(states, DetectionConfig(options.scene_threshold, options.animation_threshold,
                                                      preserve_revisits=options.preserve_revisits))
    if not detected:
        raise ValueError("No stable non-black presentation frames were detected")
    ocr = OCREngine(options.ocr_languages, options.min_ocr_confidence)
    slides = []
    for i, found in enumerate(detected):
        reference = assets / f"slide_{i + 1:03d}.jpg"
        shutil.copy2(found.representative.path, reference)
        elements, warnings = ocr.extract(reference) if options.ocr_enabled else ([], ["OCR disabled; content retained as image."])
        converted = []
        for raw in elements:
            if raw["bbox"][1] < reader.metadata.height * 0.22:
                raw["role"] = "title"
            converted.append(Element(**raw))
        animations = [AnimationEvent(**event) for event in found.animation_events]
        state_frames = []
        if options.preserve_animation_stages:
            for j, state in enumerate(found.states):
                if j == 0 or state.change >= options.animation_threshold:
                    state_frames.append(state.path)
        slides.append(Slide(i, found.start, found.end, str(reference), reader.metadata.width,
                            reader.metadata.height, found.boundary_confidence, "title" if i == 0 else "content",
                            converted, animations, state_frames, warnings))
        if progress:
            progress(0.45 + (i + 1) / len(detected) * 0.25, f"Extracting slide {i + 1}/{len(detected)}")
    model = PresentationModel(str(Path(video).resolve()), pid, reader.metadata.width, reader.metadata.height,
                              reader.metadata.fps, reader.metadata.duration, slides)
    if not ocr.available() and options.ocr_enabled:
        model.warnings.append("OCR was requested but Tesseract is unavailable. Outputs preserve slide imagery.")
    model.save(checkpoint)
    return model


def convert(video, options: ConversionOptions, progress=None):
    out = options.output_dir.resolve(); out.mkdir(parents=True, exist_ok=True)
    brand = BrandConfig.load(options.brand_config)
    model = analyze_video(video, options, progress)
    results = {}
    if "model" in options.outputs:
        model_path = out / "presentation_model.json"; model.save(model_path); results["model"] = model_path
    specs = {"reference": ("presentation_reference.pptx", "original"),
             "branded": ("presentation_branded.pptx", options.theme),
             "hybrid": ("presentation_hybrid.pptx", "hybrid")}
    for idx, (kind, (filename, theme)) in enumerate(specs.items()):
        if kind in options.outputs:
            results[kind] = build_presentation(model, out / filename, kind, brand, options.logo,
                                               theme, options.preserve_animation_stages)
        if progress:
            progress(0.72 + (idx + 1) * 0.06, f"Building {kind} presentation")
    preview_paths = []
    if "previews" in options.outputs or "report" in options.outputs:
        preview_dir = out / "preview"; preview_dir.mkdir(exist_ok=True)
        for slide in model.slides:
            target = preview_dir / f"slide_{slide.index + 1:03d}_after.jpg"
            create_redesign_preview(slide.reference_frame, target, brand)
            preview_paths.extend([Path(slide.reference_frame), target])
        create_contact_sheet([s.reference_frame for s in model.slides], preview_dir / "before_contact_sheet.jpg")
        create_contact_sheet([preview_dir / f"slide_{s.index + 1:03d}_after.jpg" for s in model.slides],
                             preview_dir / "after_contact_sheet.jpg")
        results["previews"] = preview_dir
    if "report" in options.outputs:
        report = out / "accuracy_report.html"
        rel = [Path("preview") / p.name for p in preview_paths if "preview" in p.parts]
        write_accuracy_report(model, report, rel); results["report"] = report
    if options.native_animations and "branded" in results:
        from video2pptx.animations import apply_supported_animations
        model.warnings.extend(apply_supported_animations(results["branded"], model))
        if "model" in options.outputs:
            model.save(results["model"])
    manifest = {key: str(value) for key, value in results.items()}
    (out / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    if progress:
        progress(1.0, "Conversion complete")
    return results

