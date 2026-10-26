from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory
import json


def main():
    try:
        import streamlit as st
    except ImportError as exc:
        raise RuntimeError("Install the UI dependencies with: pip install -e '.[ui]'") from exc
    from video2pptx.pipeline import ConversionOptions, convert
    st.set_page_config(page_title="Video2BrandedPPTX", page_icon="🎞️", layout="wide")
    st.title("Video2BrandedPPTX")
    st.caption("Reconstruct, review, and professionally brand presentation screen recordings.")
    with st.sidebar:
        st.header("About")
        st.markdown("**Created by Ahmad Badr Eldin**")
        st.markdown("[LinkedIn](https://www.linkedin.com/in/ahmadbadreldin)")
        st.markdown("[Email](mailto:ahmadmbadreldin@gmail.com)")
        st.markdown("Phone: [(+20) 01030744844](tel:+201030744844)")
        st.caption("Offline-first presentation reconstruction and branding.")
    video = st.file_uploader("Presentation recording", type=["mp4", "mov", "mkv", "webm"])
    logo = st.file_uploader("Company logo (optional)", type=["png", "svg"])
    left, middle, right = st.columns(3)
    theme = left.selectbox("Theme", ["corporate", "modern-minimal", "premium-dark", "custom-brand", "original"])
    mode = middle.selectbox("Conversion mode", ["hybrid", "branded", "fidelity"])
    redesign = right.select_slider("Redesign intensity", ["minimal", "moderate", "extensive"], value="moderate")
    with st.expander("Brand and layout", expanded=True):
        c1, c2, c3 = st.columns(3)
        position = c1.selectbox("Logo position", ["auto", "right-sidebar", "left-sidebar", "top-right", "top-left", "bottom-right", "bottom-left"])
        logo_scale = c2.slider("Logo size", 0.02, 0.30, 0.11, 0.01)
        font = c3.text_input("Font family", "Aptos")
        c4, c5, c6 = st.columns(3)
        primary = c4.color_picker("Brand color", "#17365D")
        accent = c5.color_picker("Accent color", "#2F75B5")
        footer = c6.text_input("Footer text", "")
    langs = st.text_input("OCR languages (Tesseract codes)", "eng", help="Examples: eng, ara, chi_sim")
    c1, c2, c3 = st.columns(3)
    preserve = c1.checkbox("Preserve animation stages", True)
    slide_numbers = c2.checkbox("Slide numbers", True)
    accuracy = c3.selectbox("Accuracy level", ["Balanced", "High", "Fast"])
    output_names = st.multiselect("Outputs", ["reference", "branded", "hybrid", "model", "report", "previews"],
                                  default=["reference", "branded", "hybrid", "model", "report", "previews"])
    run = st.button("Convert presentation", type="primary", disabled=video is None)
    if run and video:
        with TemporaryDirectory(prefix="video2pptx_") as temp:
            temp = Path(temp); video_path = temp / video.name; video_path.write_bytes(video.getbuffer())
            logo_path = None
            if logo:
                logo_path = temp / logo.name; logo_path.write_bytes(logo.getbuffer())
            brand_path = temp / "brand_config.json"
            brand_path.write_text(json.dumps({"primary_color": primary, "accent_color": accent,
                                               "font_family": font, "title_font_family": font,
                                               "logo_position": position, "logo_scale": logo_scale,
                                               "footer_text": footer, "show_slide_numbers": slide_numbers}),
                                  encoding="utf-8")
            output = temp / "output"; bar = st.progress(0.0, "Starting")
            intervals = {"High": 0.25, "Balanced": 0.5, "Fast": 1.0}
            options = ConversionOptions(output, logo_path, theme, mode, redesign,
                                        brand_config=brand_path,
                                        ocr_languages=tuple(x.strip() for x in langs.split(",") if x.strip()),
                                        sample_interval=intervals[accuracy],
                                        preserve_animation_stages=preserve, outputs=set(output_names))
            try:
                results = convert(video_path, options, lambda p, m: bar.progress(p, m))
            except Exception as exc:
                st.exception(exc); return
            st.success("Conversion complete. Review warnings in the accuracy report before use.")
            preview_dir = results.get("previews")
            if preview_dir:
                before = output / "preview" / "before_contact_sheet.jpg"
                after = output / "preview" / "after_contact_sheet.jpg"
                a, b = st.columns(2)
                if before.exists(): a.image(str(before), caption="Detected source slides")
                if after.exists(): b.image(str(after), caption="Branded redesign preview")
            model_path = results.get("model")
            if model_path:
                data = json.loads(Path(model_path).read_text(encoding="utf-8"))
                uncertain = [{"slide": s["index"] + 1, "text": e.get("text"),
                              "confidence": round(e.get("confidence", 0), 3),
                              "warning": "; ".join(e.get("warnings", []))}
                             for s in data["slides"] for e in s.get("elements", [])
                             if e.get("confidence", 1) < 0.75 or e.get("warnings")]
                st.subheader("Low-confidence text review")
                if uncertain: st.dataframe(uncertain, use_container_width=True)
                else: st.info("No low-confidence OCR regions were recorded.")
            for name, path in results.items():
                path = Path(path)
                if path.is_file():
                    st.download_button(f"Download {name}", path.read_bytes(), file_name=path.name)


if __name__ == "__main__":
    main()
