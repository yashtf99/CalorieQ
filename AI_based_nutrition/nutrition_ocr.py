"""
nutrition_ocr.py

Pipeline for converting a raw photo of a nutrition label into
ordered raw text using OCR (no label/value parsing).

Pipeline stages:
    1. preprocess_image   -> normalize size, deskew, denoise, binarize
    2. ocr_extract_lines  -> run Tesseract, reconstruct reading order as lines

Dependencies:
    pip install opencv-python-headless pytesseract numpy pillow
    + Tesseract OCR binary must be installed on the system
      (e.g. `apt install tesseract-ocr` or `brew install tesseract`)

Usage:
    python nutrition_ocr.py path/to/label.jpg
"""

import re
from dataclasses import dataclass, field
from typing import Optional

import cv2
import numpy as np
import pytesseract
from pytesseract import Output


# --------------------------------------------------------------------------
# Stage 1: Preprocessing
# --------------------------------------------------------------------------

TARGET_MIN_WIDTH = 1200   # Tesseract does best around 300 "DPI"-equivalent;
                          # for phone photos this roughly means upscaling
                          # small images and downscaling huge ones.
TARGET_MAX_WIDTH = 2200


def _resize_for_ocr(gray: np.ndarray) -> np.ndarray:
    h, w = gray.shape[:2]
    if w < TARGET_MIN_WIDTH:
        scale = TARGET_MIN_WIDTH / w
    elif w > TARGET_MAX_WIDTH:
        scale = TARGET_MAX_WIDTH / w
    else:
        scale = 1.0
    if scale != 1.0:
        interp = cv2.INTER_CUBIC if scale > 1.0 else cv2.INTER_AREA
        gray = cv2.resize(gray, None, fx=scale, fy=scale, interpolation=interp)
    return gray


def _deskew(gray: np.ndarray) -> np.ndarray:
    """Estimate and correct small rotation using the minimum-area rect
    of dark (text) pixels. Falls back to the original image if the
    detected angle is implausible (e.g. near-blank image)."""
    inv = cv2.bitwise_not(gray)
    thresh = cv2.threshold(inv, 0, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)[1]
    coords = cv2.findNonZero(thresh)
    if coords is None:
        return gray

    angle = cv2.minAreaRect(coords)[-1]
    # cv2.minAreaRect returns angles in [-90, 0); normalize to a small
    # rotation rather than a 90-degree flip.
    if angle < -45:
        angle = -(90 + angle)
    else:
        angle = -angle

    if abs(angle) < 0.5 or abs(angle) > 15:
        # Either already straight, or the estimate is unreliable
        # (large angles are usually noise, not real skew for a
        # label photo held roughly upright).
        return gray

    (h, w) = gray.shape[:2]
    center = (w // 2, h // 2)
    M = cv2.getRotationMatrix2D(center, angle, 1.0)
    rotated = cv2.warpAffine(
        gray, M, (w, h),
        flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE
    )
    return rotated


def preprocess_image(image_path: str, debug_path: Optional[str] = None) -> np.ndarray:
    """Load a raw photo and return a binarized, deskewed, OCR-ready image."""
    img = cv2.imread(image_path, cv2.IMREAD_COLOR)
    if img is None:
        raise FileNotFoundError(f"Could not read image at {image_path}")

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    gray = _resize_for_ocr(gray)

    # Denoise while preserving text edges better than a plain blur.
    gray = cv2.fastNlMeansDenoising(gray, h=10)

    gray = _deskew(gray)

    # Improve local contrast (helps with uneven lighting/glare on
    # glossy nutrition labels) before binarizing.
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    gray = clahe.apply(gray)

    # Adaptive threshold handles uneven lighting far better than a
    # single global threshold across a photographed label.
    binary = cv2.adaptiveThreshold(
        gray, 255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY,
        blockSize=31, C=15
    )

    # Light morphological close to reconnect thin character strokes
    # broken by thresholding.
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2, 2))
    binary = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel)

    if debug_path:
        cv2.imwrite(debug_path, binary)

    return binary


# --------------------------------------------------------------------------
# Stage 2: OCR + reading-order reconstruction
# --------------------------------------------------------------------------

@dataclass
class OcrLine:
    text: str
    confidence: float
    top: int
    left: int


def ocr_extract_lines(binary_image: np.ndarray, lang: str = "eng") -> list[OcrLine]:
    """Run Tesseract and reconstruct text as ordered lines (not just a
    flat word blob), grouping words by Tesseract's own line/block/par
    indices so words on the same physical line stay together and in
    left-to-right order, and lines stay in top-to-bottom order."""
    config = "--oem 3 --psm 6"  # psm 6: assume a single uniform block of text
    data = pytesseract.image_to_data(
        binary_image, lang=lang, config=config, output_type=Output.DICT
    )

    n = len(data["text"])
    groups: dict[tuple, list[int]] = {}
    for i in range(n):
        word = data["text"][i].strip()
        if not word:
            continue
        key = (data["block_num"][i], data["par_num"][i], data["line_num"][i])
        groups.setdefault(key, []).append(i)

    lines: list[OcrLine] = []
    for key in sorted(groups.keys()):
        idxs = sorted(groups[key], key=lambda i: data["left"][i])
        words = [data["text"][i].strip() for i in idxs]
        confs = [float(data["conf"][i]) for i in idxs if float(data["conf"][i]) >= 0]
        lines.append(OcrLine(
            text=" ".join(words),
            confidence=sum(confs) / len(confs) if confs else 0.0,
            top=min(data["top"][i] for i in idxs),
            left=min(data["left"][i] for i in idxs),
        ))

    lines.sort(key=lambda l: l.top)
    return lines


# --------------------------------------------------------------------------
# End-to-end OCR convenience function
# --------------------------------------------------------------------------

def extract_text_from_image(image_path: str, debug_path: Optional[str] = None) -> dict:
    binary = preprocess_image(image_path, debug_path=debug_path)
    lines = ocr_extract_lines(binary)
    return {
        "raw_ordered_text": [l.text for l in lines],
        "lines": [
            {
                "text": l.text,
                "confidence": round(l.confidence, 1),
                "top": l.top,
                "left": l.left,
            }
            for l in lines
        ],
    }


# --------------------------------------------------------------------------
# Stage 3: Nutrition-label vs food-item classification
# --------------------------------------------------------------------------

# Keywords that reliably show up on a nutrition facts panel but not on
# a plain photo of a food item. Matched as substrings against the
# lowercased OCR text.
_NUTRITION_KEYWORDS = [
    "nutrition", "nutritional", "nutritional information",
    "energy", "kcal", "calories",
    "protein", "carbohydrate", "total fat", "saturated fat", "trans fat",
    "sugar", "sodium", "fibre", "fiber",
    "serving size", "per 100g", "per serving", "daily value", "rda",
]

# How many distinct keyword hits before we call it a nutrition label.
# A plain food photo occasionally OCRs a stray word or two from
# background packaging text, so require more than one hit.
_MIN_KEYWORD_MATCHES = 3


def classify_image(image_path: str, debug_path: Optional[str] = None) -> dict:
    """
    Run OCR on the image and decide whether it looks like a nutrition
    facts label (vs. a plain photo of a food item, e.g. an apple or
    a plate of pav bhaji).

    This is a cheap keyword-based heuristic on the OCR output, not an
    LLM call — it just needs to be good enough to route the image to
    the right downstream LLM step (text-based nutrition extraction vs.
    multimodal food-item identification).

    Returns:
        {
            "is_nutrition_label": bool,
            "raw_text": str   # OCR'd text, "" if nothing readable
        }
    """
    result = extract_text_from_image(image_path, debug_path=debug_path)
    raw_text = "\n".join(result["raw_ordered_text"])

    lowered = raw_text.lower()
    matches = {kw for kw in _NUTRITION_KEYWORDS if kw in lowered}
    is_nutrition_label = len(matches) >= _MIN_KEYWORD_MATCHES

    return {
        "is_nutrition_label": is_nutrition_label,
        "raw_text": raw_text,
    }


if __name__ == "__main__":
    import json

    path = "./data/FoodItem-Images/nutrition-labels/Amul Gold Nutrition Label.webp"
    debug = True

    debug_path = "debug_preprocessed.png" if debug else None
    output = classify_image(path, debug_path=debug_path)

    print(json.dumps(output, indent=2))