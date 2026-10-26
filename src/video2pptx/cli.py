from __future__ import annotations

import argparse
import logging
from pathlib import Path
import sys

from video2pptx.pipeline import ConversionOptions, convert


def parser():
    root = argparse.ArgumentParser(prog="video2pptx", description="Reconstruct and brand presentations from screen recordings")
    root.add_argument("--version", action="version", version="Video2BrandedPPTX 0.1.0")
    sub = root.add_subparsers(dest="command", required=True)
    command = sub.add_parser("convert", help="convert a presentation recording")
    command.add_argument("--input", required=True, type=Path)
    command.add_argument("--output", required=True, type=Path)
    command.add_argument("--logo", type=Path)
    command.add_argument("--brand-config", type=Path)
    command.add_argument("--theme", choices=["original", "corporate", "modern-minimal", "premium-dark", "custom-brand"], default="corporate")
    command.add_argument("--mode", choices=["fidelity", "branded", "hybrid"], default="hybrid")
    command.add_argument("--redesign", choices=["minimal", "moderate", "extensive"], default="moderate")
    command.add_argument("--ocr-languages", default="eng", help="comma-separated Tesseract codes, e.g. eng,ara,chi_sim")
    command.add_argument("--no-ocr", action="store_true")
    command.add_argument("--sample-interval", type=float, default=0.5)
    command.add_argument("--scene-threshold", type=float, default=0.22)
    command.add_argument("--animation-threshold", type=float, default=0.035)
    command.add_argument("--preserve-revisits", action="store_true")
    command.add_argument("--native-animations", action="store_true")
    command.add_argument("--no-resume", action="store_true")
    command.add_argument("--outputs", default="reference,branded,hybrid,model,report,previews")
    command.add_argument("--verbose", action="store_true")
    return root


def main(argv=None):
    args = parser().parse_args(argv)
    logging.basicConfig(level=logging.DEBUG if args.verbose else logging.INFO,
                        format="%(asctime)s %(levelname)s %(message)s")
    try:
        options = ConversionOptions(output_dir=args.output, logo=args.logo, theme=args.theme, mode=args.mode,
                                    redesign=args.redesign, brand_config=args.brand_config,
                                    ocr_languages=tuple(x.strip() for x in args.ocr_languages.split(",") if x.strip()),
                                    ocr_enabled=not args.no_ocr, sample_interval=args.sample_interval,
                                    scene_threshold=args.scene_threshold, animation_threshold=args.animation_threshold,
                                    preserve_revisits=args.preserve_revisits, native_animations=args.native_animations,
                                    outputs=set(x.strip() for x in args.outputs.split(",") if x.strip()),
                                    resume=not args.no_resume)
        results = convert(args.input, options, lambda p, m: print(f"[{p:>6.1%}] {m}", file=sys.stderr))
        for name, path in results.items():
            print(f"{name}: {path}")
    except (ValueError, FileNotFoundError, RuntimeError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        raise SystemExit(2)


if __name__ == "__main__":
    main()

