"""Optional Windows-only enhancement. The portable fallback records events in notes/model JSON."""
from pathlib import Path
import platform


def powerpoint_available():
    if platform.system() != "Windows":
        return False
    try:
        import win32com.client
        return True
    except ImportError:
        return False


def apply_supported_animations(pptx_path, model):
    """Add conservative appear effects to editable shapes for detected entrance events.

    COM constants are used directly to avoid an Office type-library dependency. A copy is
    saved in place. Unsupported motion/exit events stay in the JSON timeline.
    """
    if not powerpoint_available():
        return ["PowerPoint COM automation is unavailable; animation timeline kept as metadata."]
    import win32com.client
    app = win32com.client.DispatchEx("PowerPoint.Application")
    app.Visible = False
    warnings = []
    try:
        presentation = app.Presentations.Open(str(Path(pptx_path).resolve()), WithWindow=False)
        for i, source in enumerate(model.slides, 1):
            if not source.animations:
                continue
            slide = presentation.Slides(i)
            # msoAnimEffectAppear=1, msoAnimTriggerAfterPrevious=3
            candidates = [s for s in slide.Shapes if getattr(s, "HasTextFrame", False)]
            for shape, event in zip(candidates, source.animations):
                slide.TimeLine.MainSequence.AddEffect(shape, 1, 0, 3)
            if len(source.animations) > len(candidates):
                warnings.append(f"Slide {i}: some detected events had no safe editable target.")
        presentation.Save(); presentation.Close()
    finally:
        app.Quit()
    return warnings

