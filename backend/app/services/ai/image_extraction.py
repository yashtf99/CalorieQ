"""
Service for extracting nutrition from uploaded food/label images.

Handles image processing, classification, and nutrition extraction.
"""

import os
import tempfile
from typing import Optional

from app.core.exceptions import UnprocessableError
from config import settings

from .nutrition_ocr import classify_image
from .nutrition_llm_extract import extract_nutrition_from_text, extract_nutrition_from_image


def extract_nutrition_from_image_upload(image_bytes: bytes, filename: str) -> dict:
    """
    Process an uploaded image and extract nutrition data.

    Returns a dict with keys:
    - is_nutrition_label: bool
    - food_item_name: str | None (only for food items, not labels)
    - quantity_g: float | None
    - energy_kcal: float | None
    - protein_g: float | None
    - carb_g: float | None
    - fat_g: float | None
    - fibre_g: float | None
    - sodium_mg: float | None
    - confidence: str | None (only for food items: "low", "medium", "high")
    - estimation_basis: str | None (only for food items)
    """
    if not settings.AWS_BEARER_TOKEN_BEDROCK:
        raise UnprocessableError("AI image extraction is not configured — AWS_BEARER_TOKEN_BEDROCK not set")

    # Write uploaded bytes to a temp file
    with tempfile.NamedTemporaryFile(suffix=os.path.splitext(filename)[1], delete=False) as f:
        f.write(image_bytes)
        temp_path = f.name

    try:
        # Step 1: Classify — is this a nutrition label or a food item photo?
        classification = classify_image(temp_path)

        if classification["is_nutrition_label"]:
            # Step 2a: Extract from nutrition label via OCR + LLM
            raw_text = classification["raw_text"]
            nutrition = extract_nutrition_from_text(raw_text)
            return {
                "is_nutrition_label": True,
                "quantity_g": nutrition.get("quantity_g"),
                "energy_kcal": nutrition.get("energy_kcal"),
                "protein_g": nutrition.get("protein_g"),
                "carb_g": nutrition.get("carb_g"),
                "fat_g": nutrition.get("fat_g"),
                "fibre_g": nutrition.get("fibre_g"),
                "sodium_mg": nutrition.get("sodium_mg"),
                "food_item_name": None,
                "confidence": None,
                "estimation_basis": None,
            }
        else:
            # Step 2b: Estimate from food item photo via multimodal LLM
            nutrition = extract_nutrition_from_image(temp_path)
            return {
                "is_nutrition_label": False,
                "quantity_g": nutrition.get("quantity_g"),
                "energy_kcal": nutrition.get("energy_kcal"),
                "protein_g": nutrition.get("protein_g"),
                "carb_g": nutrition.get("carb_g"),
                "fat_g": nutrition.get("fat_g"),
                "fibre_g": nutrition.get("fibre_g"),
                "sodium_mg": nutrition.get("sodium_mg"),
                "food_item_name": nutrition.get("food_item_name"),
                "confidence": nutrition.get("confidence"),
                "estimation_basis": nutrition.get("estimation_basis"),
            }
    except Exception as e:
        raise UnprocessableError(f"Failed to extract nutrition from image: {str(e)}")
    finally:
        # Clean up temp file
        if os.path.exists(temp_path):
            os.unlink(temp_path)
