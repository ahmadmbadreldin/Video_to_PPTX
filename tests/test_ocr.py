from video2pptx.ocr.engine import contains_rtl, extract_numeric_tokens


def test_rtl_detection():
    assert contains_rtl("مرحبا بالعالم")
    assert not contains_rtl("Hello world")


def test_numeric_text_extraction_preserves_values():
    text = "Revenue +12.5%, total 1,234.50 and ratio 3:2 on 2026-10-26"
    values = extract_numeric_tokens(text)
    assert "+12.5%" in values
    assert "1,234.50" in values
    assert "3:2" in values

