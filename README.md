# Video2BrandedPPTX

[![Python 3.11+](https://img.shields.io/badge/python-3.11%2B-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

Video2BrandedPPTX is an offline-first Python application that reconstructs presentation screen recordings as branded PowerPoint files. It detects likely slide boundaries and progressive build states, preserves clean reference frames, extracts editable text when OCR is available, and applies a consistent presentation design and company logo.

> [!IMPORTANT]
> Reconstruction from video cannot be perfect. A recording does not contain the original PowerPoint objects, chart data, master layouts, fonts, hyperlinks, speaker notes, or exact animation settings. Always review the generated accuracy report and compare important facts and numbers with the reference deck.

## Features

- Reads MP4, MOV, MKV, and WEBM recordings.
- Samples by timestamp instead of blindly extracting one frame per second.
- Detects black frames, slide changes, and smaller animation-like changes.
- Groups progressive builds under their parent slide.
- Selects a clean, stable reference frame for each detected slide.
- Supports optional multilingual OCR, including English, Arabic, and Chinese.
- Preserves OCR bounding boxes, confidence, reading order, and RTL alignment.
- Generates editable text boxes when OCR confidence is sufficient.
- Keeps complex charts, photographs, and diagrams as image assets when reliable native reconstruction is impossible.
- Supports automatic, corner, and reserved-sidebar logo placement.
- Includes Corporate, Modern Minimal, Premium Dark, Original, and Custom Brand themes.
- Preserves the source aspect ratio, including 16:9 and 4:3.
- Provides a Streamlit interface and command-line interface.
- Uses deterministic project IDs, cached frames, and checkpoint/resume support.
- Produces structured JSON, previews, extracted assets, and an HTML accuracy report.
- Can optionally add conservative PowerPoint animations through COM automation on Windows.

## Requirements

- Python 3.11 or newer
- Windows or Linux
- Optional: [Tesseract OCR](https://github.com/tesseract-ocr/tesseract) executable and required language packs
- Optional: FFmpeg installed on the system for broader codec support
- Optional: Microsoft PowerPoint and `pywin32` for Windows COM animation enhancement
- Optional: LibreOffice or Microsoft PowerPoint for external slide rendering

The basic image-preserving conversion works without Microsoft PowerPoint, paid APIs, or an OCR executable.

## Installation and running

Download or clone the repository, open a terminal in its root directory, and
follow the instructions for your operating system.

### Windows PowerShell

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m pip install -e . --no-deps
```

Start the Streamlit interface after installation:

```powershell
python -m streamlit run src/video2pptx/app.py
```

If PowerShell blocks activation, run the environment's Python directly:

```powershell
.\.venv\Scripts\python.exe -m streamlit run src/video2pptx/app.py
```

Windows users can also double-click `run_app.cmd`. The launcher resolves all
paths relative to its own location and does not contain machine-specific paths.

### Linux

```bash
python3.11 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m pip install -e . --no-deps
```

Start the Streamlit interface after installation:

```bash
python -m streamlit run src/video2pptx/app.py
```

For development and tests, the equivalent project-extra installation is:

```bash
python -m pip install -e ".[all,test]"
```

## Streamlit interface

Start the application from the repository root:

```powershell
python -m streamlit run src/video2pptx/app.py
```

The interface lets you:

1. Upload a presentation recording and optional PNG or SVG logo.
2. Select a conversion mode and visual theme.
3. Configure logo placement, size, brand colors, font, footer, and slide numbers.
4. Choose OCR languages and processing accuracy.
5. Preview detected source slides and branded results.
6. Review low-confidence OCR text.
7. Download the generated presentations, model, and report.

Uploaded files are processed in an isolated temporary directory. The core pipeline does not call external APIs.

## Command-line interface

```powershell
python -m video2pptx convert `
  --input input.mp4 `
  --logo assets/logo.png `
  --theme corporate `
  --mode hybrid `
  --redesign moderate `
  --ocr-languages eng,ara,chi_sim `
  --output output
```

For image-only processing without an OCR executable:

```powershell
python -m video2pptx convert --input input.mp4 --output output --no-ocr
```

Useful options:

| Option | Description |
| --- | --- |
| `--outputs` | Comma-separated artifacts: `reference,branded,hybrid,model,report,previews` |
| `--sample-interval` | Timestamp sampling interval in seconds |
| `--scene-threshold` | Sensitivity for separating slides |
| `--animation-threshold` | Sensitivity for recording smaller visual changes |
| `--preserve-revisits` | Keep repeated visits to the same slide |
| `--no-resume` | Ignore an existing cached checkpoint |
| `--native-animations` | Attempt conservative PowerPoint COM animations on Windows |

Lower the scene threshold when distinct slides are being grouped. Raise it when animation builds are incorrectly becoming separate slides.

## OCR configuration

The Python package `pytesseract` is a wrapper and does not include the Tesseract engine. Install Tesseract separately and ensure the executable is available on `PATH`, or set its full location. For example, when it is installed under the standard Windows Program Files directory:

```powershell
$env:TESSERACT_CMD = Join-Path $env:ProgramFiles "Tesseract-OCR\tesseract.exe"
```

Language codes are passed as comma-separated Tesseract codes, for example:

```text
eng,ara,chi_sim
```

If Tesseract is unavailable, conversion continues using slide images and records an OCR warning instead of inventing text.

## Branding configuration

Copy [config/brand_config.example.json](config/brand_config.example.json) and customize the company name, colors, fonts, logo position, sidebar width, footer, and slide-number settings.

```powershell
python -m video2pptx convert `
  --input input.mp4 `
  --brand-config config/my_brand.json `
  --theme custom-brand `
  --output output
```

The validation schema is available at [schemas/brand_config.schema.json](schemas/brand_config.schema.json).

## Generated outputs

| Path | Purpose |
| --- | --- |
| `presentation_branded.pptx` | Branded redesign with editable OCR text where reliable |
| `presentation_reference.pptx` | Clean source-reference frames |
| `presentation_hybrid.pptx` | Visual-fidelity fallback with branding |
| `presentation_model.json` | Structured slide, element, confidence, warning, and animation metadata |
| `accuracy_report.html` | Human-review report with grounded confidence metrics and limitations |
| `extracted_assets/` | Selected slide frames and reusable visual assets |
| `preview/` | Before/after previews and contact sheets |
| `manifest.json` | Machine-readable output paths |

## Project structure

```text
src/video2pptx/
|-- ingestion/       Video validation and timestamp-based frame extraction
|-- scenes/          Slide boundaries, animation states, and deduplication
|-- ocr/             Multilingual OCR adapter and confidence handling
|-- layout/          Coordinate conversion, overlap, and logo placement
|-- reconstruction/  PPTX generation and editable elements
|-- animations/      Animation metadata and optional PowerPoint COM adapter
|-- branding/        Brand configuration and validation
|-- rendering/       Preview and contact-sheet generation
|-- validation/      Accuracy and warning reports
|-- models/          Structured intermediate presentation model
|-- pipeline.py      End-to-end orchestration and checkpoints
|-- cli.py           Command-line interface
`-- app.py           Streamlit interface
```

## Tests and reproducible sample

Install the test extra and run:

```powershell
python -m pip install -e ".[test]"
python -m pytest
```

Create and convert the deterministic sample video:

```powershell
python examples/create_sample_video.py
python -m video2pptx convert `
  --input examples/sample_presentation.mp4 `
  --output sample_output `
  --no-ocr
```

The test suite covers scene boundaries, deduplication, animation grouping, coordinate conversion, logo placement, RTL detection, aspect ratios, brand validation, overlap detection, numeric token preservation, PPTX validity, editable text, SVG fallback behavior, and an end-to-end synthetic video conversion.

## Review checklist

1. Confirm slide boundaries in `preview/before_contact_sheet.jpg`.
2. Review warnings and low-confidence OCR in `accuracy_report.html` and `presentation_model.json`.
3. Compare names, dates, numbers, symbols, and chart labels with `presentation_reference.pptx`.
4. Open the branded presentation in PowerPoint or LibreOffice and check font substitution and overflow.
5. Enable native animation reconstruction only after reviewing the content.

## Known limitations

- OCR quality depends on video resolution, compression, language packs, and text size.
- Low-confidence text is flagged and retained visually rather than fabricated.
- Complex charts and diagrams remain raster assets when their underlying data cannot be recovered.
- Cursor movement, compression noise, and fades can resemble animation events.
- `python-pptx` cannot author the full PowerPoint animation model. Portable outputs store the timeline in JSON and slide notes.
- The Windows COM adapter supports only conservative effects and requires Microsoft PowerPoint.
- Built-in previews are grounded composites, not exact Office-rendered slide images.
- SVG logo support requires the optional CairoSVG package and its native Cairo dependency. PNG is the most portable format.
- Hidden objects, hyperlinks, source chart workbooks, exact fonts, notes, and unsupported transitions cannot be recovered from pixels.

## Contributing

Issues and pull requests are welcome. Please include a reproducible sample, avoid uploading confidential recordings, and run the test suite before submitting changes.

## Author and contact

**Ahmad Badr Eldin**

| Channel | Contact |
| --- | --- |
| LinkedIn | [linkedin.com/in/ahmadbadreldin](https://www.linkedin.com/in/ahmadbadreldin) |
| Email | [ahmadmbadreldin@gmail.com](mailto:ahmadmbadreldin@gmail.com) |
| Phone | [(+20) 01030744844](tel:+201030744844) |

## License

Copyright © 2026 Ahmad Badr Eldin. Released under the [MIT License](LICENSE).
