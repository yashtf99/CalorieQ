"""
nutrition_llm_extract.py — Extract nutrition from labels or food photos via LLM.

Uses Bedrock Nova model with structured output for nutrition extraction.
"""

import base64
import mimetypes
import os
from typing import Optional

from langchain_aws import ChatBedrockConverse
from pydantic import BaseModel, Field

from config import settings


def _ensure_aws_credentials() -> None:
    """Set AWS credentials from settings to environment."""
    if settings.AWS_BEARER_TOKEN_BEDROCK:
        os.environ["AWS_BEARER_TOKEN_BEDROCK"] = settings.AWS_BEARER_TOKEN_BEDROCK


class MealNutrition(BaseModel):
    """Nutrition fields extracted from a nutrition facts label."""

    energy_kcal: Optional[float] = Field(
        default=None, description="Total energy / calories, in kcal."
    )
    protein_g: Optional[float] = Field(
        default=None, description="Protein content, in grams."
    )
    carb_g: Optional[float] = Field(
        default=None, description="Total carbohydrate content, in grams."
    )
    fat_g: Optional[float] = Field(
        default=None, description="Total fat content, in grams."
    )
    fibre_g: Optional[float] = Field(
        default=None, description="Dietary fibre content, in grams. Null if not listed."
    )
    sodium_mg: Optional[float] = Field(
        default=None, description="Sodium content, in milligrams. Null if not listed."
    )
    quantity_g: Optional[float] = Field(
        default=None,
        description=(
            "The portion/serving size, in grams, that the above values are "
            "based on (e.g. 'per 100g' -> 100, 'per serving (30g)' -> 30). "
            "Null if the label doesn't state a gram-based serving size."
        ),
    )


_EXTRACTION_PROMPT = """You are extracting structured nutrition data from raw OCR \
text of a photographed nutrition facts label. The text may contain OCR noise, \
misread characters, misaligned rows/columns, or stray words from the packaging.

Rules:
- Only extract values that are actually present in the text below. Do not \
estimate, guess, or fill in "typical" values for anything you cannot find.
- If a field is missing, unreadable, or ambiguous, set it to null.
- Ignore any %RDA / %DV (percentage daily value) columns — only extract the \
absolute quantity (grams/mg/kcal), not the percentage.
- If the label lists multiple columns (e.g. "per 100g" and "per serving"), \
prefer the "per serving" column if quantity_g for a serving is stated; \
otherwise use "per 100g" and set quantity_g to 100.
- Normalize units: convert kJ to kcal only if kcal is not separately given \
(1 kcal = 4.184 kJ). Convert any energy/fat/protein/carb value given in mg \
to grams if needed for consistency with the field's unit.

OCR TEXT:
---
{raw_text}
---
"""


def extract_nutrition_from_text(
    raw_text: str,
    model: str | None = None,
    region_name: str | None = None,
) -> dict:
    """Call the LLM with structured output and return a plain dict."""
    _ensure_aws_credentials()
    model = model or settings.BEDROCK_MODEL_ID
    region_name = region_name or settings.AWS_REGION
    llm = ChatBedrockConverse(model=model, region_name=region_name)
    structured_llm = llm.with_structured_output(MealNutrition)

    prompt = _EXTRACTION_PROMPT.format(raw_text=raw_text)
    result: MealNutrition = structured_llm.invoke(prompt)

    return result.model_dump()


class MealNutritionEstimate(MealNutrition):
    """Same fields as MealNutrition, plus identification/estimation context."""

    food_item_name: Optional[str] = Field(
        default=None,
        description="Best guess at the food/dish name shown in the image (e.g. 'pav bhaji', 'apple, medium').",
    )
    estimation_basis: Optional[str] = Field(
        default=None,
        description=(
            "One short sentence on how the portion size was estimated from "
            "the image (e.g. 'plate ~26cm, food covers half, typical density "
            "for a mixed vegetable curry')."
        ),
    )
    confidence: Optional[str] = Field(
        default=None, description="One of: low, medium, high — your confidence in this estimate."
    )


_MULTIMODAL_PROMPT = """You are a nutrition estimation assistant. You are given a \
photo of a food item or meal — there is no nutrition label, ingredient list, or \
text of any kind to read. You must work entirely from what you can see.

Do the following, in order:
1. Identify the food or dish in the image as specifically as you reasonably can \
(e.g. "banana, medium" rather than just "fruit"; "pav bhaji" rather than just \
"curry", if recognizable as a specific dish).
2. Estimate the portion size actually visible in the image, in grams. Use visual \
reference cues for scale — a standard plate is ~26-28cm across, a standard bowl \
~500-750ml, a dinner spoon ~15ml, an average adult hand for scale if visible, \
packaging size if a wrapper/container is visible, etc. State the reasoning \
briefly in estimation_basis.
3. Estimate the macro/micronutrient content for THAT estimated portion (not per \
100g, not a generic "average serving" from a database) using your general \
knowledge of that food's typical nutritional composition, adjusted for any \
visible preparation (fried vs. steamed, visible oil/ghee, added sauce, etc.).
4. Set confidence to "low" if the food is ambiguous, mixed, or partially hidden; \
"medium" if identifiable but the portion/recipe could vary a lot (e.g. home-cooked \
mixed dishes); "high" only for simple, clearly-visible, single-ingredient items \
(e.g. a whole apple).

Rules:
- This is an estimate, not a measurement. Never claim precision the image can't \
support — round to sensible values (nearest 5-10 kcal, nearest 0.5g), don't return \
implausibly precise numbers like "247.3 kcal".
- If you genuinely cannot identify the food (image unclear, not food, etc.), set \
food_item_name to null, set confidence to "low", and leave the nutrient fields null \
rather than guessing at random.
- quantity_g should be your estimated grams for the portion shown — this is the \
basis for all other values, so make sure the nutrient values are consistent with it \
(i.e. don't estimate quantity_g=150 but give calories for a 300g portion).
"""


def extract_nutrition_from_image(
    image_path: str,
    model: str | None = None,
    region_name: str | None = None,
) -> dict:
    """Send the raw image to the multimodal LLM and get back estimated nutrition."""
    _ensure_aws_credentials()
    model = model or settings.BEDROCK_MODEL_ID
    region_name = region_name or settings.AWS_REGION

    mime_type, _ = mimetypes.guess_type(image_path)
    mime_type = mime_type or "image/jpeg"

    with open(image_path, "rb") as f:
        b64_data = base64.b64encode(f.read()).decode("utf-8")

    llm = ChatBedrockConverse(model=model, region_name=region_name)
    structured_llm = llm.with_structured_output(MealNutritionEstimate)

    message = {
        "role": "user",
        "content": [
            {"type": "text", "text": _MULTIMODAL_PROMPT},
            {
                "type": "image",
                "source_type": "base64",
                "data": b64_data,
                "mime_type": mime_type,
            },
        ],
    }

    result: MealNutritionEstimate = structured_llm.invoke([message])
    return result.model_dump()
