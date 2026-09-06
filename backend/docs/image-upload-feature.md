# Image Upload for Meal Creation

## Overview

Users can now upload food images (nutrition labels or food photos) to pre-fill meal nutrition data, then adjust quantities and save to their meal log.

## Backend Changes

### New Files

1. **`app/services/ai/nutrition_ocr.py`** — OCR pipeline for nutrition label classification
   - Preprocesses images (resize, deskew, denoise, binarize)
   - Extracts text lines using Tesseract
   - Classifies image as nutrition label vs food photo

2. **`app/services/ai/nutrition_llm_extract.py`** — LLM-based nutrition extraction
   - Extracts structured nutrition from OCR'd label text (via Bedrock Nova)
   - Estimates nutrition from food photo (multimodal LLM)
   - Pydantic models: `MealNutrition`, `MealNutritionEstimate`

3. **`app/services/ai/image_extraction.py`** — Main orchestration service
   - Routes images through classification pipeline
   - Calls appropriate extraction method
   - Returns normalized nutrition dict

4. **`app/api/v1/ai.py`** — FastAPI router
   - `POST /api/v1/ai/extract_image` — Upload image and get nutrition

5. **`app/schemas/ai.py`** — Pydantic response schema
   - `ImageExtractionOut` — API response model with validation

### Modified Files

- **`app/api/v1/router.py`** — Added `ai` router to aggregator
- **`app/services/ai/__init__.py`** — Exported `extract_nutrition_from_image_upload`

### Dependencies

Add to `backend/requirements.txt`:
```
opencv-python-headless>=4.8.0
pytesseract>=0.3.10
langchain-aws>=0.2.0
pillow>=10.0.0
```

Note: Tesseract OCR binary must be installed on the system:
```bash
# Ubuntu/Debian
apt-get install tesseract-ocr

# macOS
brew install tesseract

# Windows: Download from https://github.com/UB-Mannheim/tesseract/wiki
```

### Environment

Set in `.env`:
```
AWS_BEARER_TOKEN_BEDROCK=<your-bedrock-token>
```

## Frontend Changes

### New Files

1. **`frontend/src/api/ai.ts`** — API client hook
   - `useExtractImage()` — Multipart form upload hook
   - `ImageExtractionResult` — Response type

### Modified Files

- **`AddMealDrawer.tsx`** — Added image upload flow
  - New views: `'image'` (upload), `'image-detail'` (confirm/edit)
  - Image preview, file picker, editable nutrition fields
  - "Upload image" button in search view footer
  - Buttons to navigate between search, image, custom, detail views
  - Confirmation dialog with extracted nutrition

## User Flow

1. User clicks "Add Meal" → searches for food
2. From search view, clicks **"Upload image"** button
3. Selects image file (nutrition label or food photo)
4. System processes and shows:
   - Image preview
   - Detected type (label vs food photo)
   - Confidence level (for food photos)
   - Pre-filled nutrition fields (editable)
5. User adjusts quantity and macro values as needed
6. Clicks **"Add to [meal type]"** to save
7. Entry appears in meal log with `source: 'ai'`

## Nutrition Extraction Behavior

### Nutrition Labels
- OCR reads text from label
- LLM extracts structured nutrition
- Returns: quantity, kcal, protein, carbs, fat, fibre, sodium

### Food Photos
- Multimodal LLM identifies food
- Estimates portion size and nutrition
- Returns: food name, quantity, estimated macros + confidence level
- Confidence ratings: "low" (ambiguous), "medium" (home-cooked), "high" (simple items)

## Testing

### Smoke Test (no image file needed)
```bash
# Backend: verify route exists
curl -H "Authorization: Bearer <token>" http://localhost:8000/api/v1/ai/extract_image

# Frontend: dev server loads without errors
npm run dev
```

### With Real Image
1. Upload nutrition label image → Verify OCR accuracy
2. Upload food photo → Verify portion estimate
3. Edit extracted values before saving
4. Verify meal log shows correct source and nutrition

## Notes

- AI module is self-contained in `app/services/ai/` (not dependent on `AI_based_nutrition/`)
- Bedrock costs per API call (~$0.01-0.05 per request)
- Consider rate limiting per user before production
- Temporary image files cleaned up after processing
- Failed extractions return `400 UNPROCESSABLE` with error details
