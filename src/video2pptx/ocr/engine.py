from __future__ import annotations

import os
import re


def contains_rtl(text):
    return any("\u0590" <= ch <= "\u08ff" for ch in text)


def extract_numeric_tokens(text):
    return re.findall(r"(?<!\w)[+-]?(?:\d+(?:[/:-]\d+)+|\d[\d,]*(?:\.\d+)?%?)(?!\w)", text)


class OCREngine:
    def __init__(self, languages=("eng",), min_confidence=55):
        self.languages = tuple(languages)
        self.min_confidence = min_confidence

    def available(self):
        try:
            import pytesseract
            if os.getenv("TESSERACT_CMD"):
                pytesseract.pytesseract.tesseract_cmd = os.environ["TESSERACT_CMD"]
            pytesseract.get_tesseract_version()
            return True
        except Exception:
            return False

    def extract(self, image_path):
        if not self.available():
            return [], ["OCR unavailable: install Tesseract and pytesseract; slide remains an image."]
        import pytesseract
        from PIL import Image
        data = pytesseract.image_to_data(Image.open(image_path), lang="+".join(self.languages),
                                         config="--psm 11", output_type=pytesseract.Output.DICT)
        words = []
        for i, raw in enumerate(data["text"]):
            text = raw.strip()
            try:
                confidence = float(data["conf"][i])
            except (TypeError, ValueError):
                confidence = -1
            if not text or confidence < 0:
                continue
            words.append({"text": text, "confidence": confidence / 100,
                          "bbox": (data["left"][i], data["top"][i], data["width"][i], data["height"][i]),
                          "block": data["block_num"][i], "paragraph": data["par_num"][i],
                          "line": data["line_num"][i]})
        lines = {}
        for word in words:
            key = (word["block"], word["paragraph"], word["line"])
            lines.setdefault(key, []).append(word)
        elements, warnings = [], []
        for order, line_words in enumerate(lines.values()):
            x = min(w["bbox"][0] for w in line_words); y = min(w["bbox"][1] for w in line_words)
            right = max(w["bbox"][0] + w["bbox"][2] for w in line_words)
            bottom = max(w["bbox"][1] + w["bbox"][3] for w in line_words)
            text = " ".join(w["text"] for w in line_words)
            confidence = sum(w["confidence"] for w in line_words) / len(line_words)
            uncertain = confidence * 100 < self.min_confidence
            if uncertain:
                warnings.append(f"Low-confidence OCR ({confidence:.0%}): {text!r}")
            elements.append({"kind": "text", "bbox": (x, y, right - x, bottom - y), "text": text,
                             "confidence": confidence, "language": "mixed", "role": "body",
                             "editable": not uncertain, "reading_order": order, "rtl": contains_rtl(text),
                             "warnings": ["Manual review required"] if uncertain else []})
        return elements, warnings
