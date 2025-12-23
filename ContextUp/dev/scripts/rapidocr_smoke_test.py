"""
RapidOCR Smoke Test
Usage:
  python dev/scripts/rapidocr_smoke_test.py <image_path> [--out output.txt] [--min-conf 0.5] [--cpu]
"""
from __future__ import annotations

import argparse
import inspect
from pathlib import Path

import cv2

try:
    from rapidocr_onnxruntime import RapidOCR
except ImportError as exc:
    raise SystemExit(f"rapidocr-onnxruntime is not installed: {exc}") from exc


def build_engine(use_gpu: bool, lang: str | None) -> RapidOCR:
    kwargs = {}
    params = inspect.signature(RapidOCR).parameters
    if lang and "lang" in params:
        kwargs["lang"] = lang
    if "use_gpu" in params:
        kwargs["use_gpu"] = use_gpu
    elif "use_cuda" in params:
        kwargs["use_cuda"] = use_gpu
    elif "providers" in params and not use_gpu:
        kwargs["providers"] = ["CPUExecutionProvider"]
    try:
        return RapidOCR(**kwargs)
    except TypeError:
        return RapidOCR()


def extract_lines(result, min_conf: float) -> list[str]:
    lines = []
    if not result:
        return lines
    for item in result:
        if not item:
            continue
        text = None
        conf = None
        if isinstance(item, (list, tuple)):
            if len(item) >= 2 and isinstance(item[1], str):
                text = item[1]
            elif len(item) >= 2 and isinstance(item[1], (list, tuple)) and item[1]:
                text = item[1][0]
            if len(item) >= 3 and isinstance(item[2], (int, float)):
                conf = float(item[2])
            elif isinstance(item[-1], (int, float)):
                conf = float(item[-1])
        if text and (conf is None or conf >= min_conf):
            if conf is None:
                lines.append(text)
            else:
                lines.append(f"{text} ({conf:.2f})")
    return lines


def main() -> int:
    parser = argparse.ArgumentParser(description="RapidOCR smoke test (image only).")
    parser.add_argument("image", help="Path to image file")
    parser.add_argument("--out", help="Optional output text file", default="")
    parser.add_argument("--min-conf", type=float, default=0.5, help="Minimum confidence (default: 0.5)")
    parser.add_argument("--cpu", action="store_true", help="Force CPU provider")
    parser.add_argument("--lang", default="", help="Language code if supported by RapidOCR")
    args = parser.parse_args()

    img_path = Path(args.image)
    if not img_path.exists():
        print(f"[ERROR] File not found: {img_path}")
        return 1

    image = cv2.imread(str(img_path))
    if image is None:
        print(f"[ERROR] Failed to read image: {img_path}")
        return 1

    ocr = build_engine(use_gpu=not args.cpu, lang=args.lang or None)
    result = ocr(image)
    if isinstance(result, tuple):
        result = result[0]

    lines = extract_lines(result, args.min_conf)
    if not lines:
        print("[INFO] No text detected.")
    else:
        print("[INFO] Detected text:")
        for line in lines:
            print(f"  {line}")

    if args.out:
        out_path = Path(args.out)
        out_path.write_text("\n".join(lines), encoding="utf-8")
        print(f"[INFO] Saved: {out_path}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
