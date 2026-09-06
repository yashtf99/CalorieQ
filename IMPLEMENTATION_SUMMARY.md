# Image Upload Meal Creation — Implementation Summary

## What Was Built

A **complete happy path for adding meals via image upload**, integrating AI-based nutrition extraction into the existing meal logging workflow.

## User Experience

1. **Entry point**: "Add Meal" drawer → "Upload image" button (new)
2. **Upload**: Select nutrition label or food photo
3. **Processing**: Backend classifies image, extracts nutrition via Bedrock
4. **Confirmation**: User sees pre-filled nutrition, can edit quantity + macros
5. **Save**: Logs as meal with `source: 'ai'`, preserves all extracted data

## Technical Architecture

### Backend (Python/FastAPI)

**New Services** (`app/services/ai/`):
- `nutrition_ocr.py` — Tesseract OCR pipeline + label classification
- `nutrition_llm_extract.py` — Bedrock Nova structured extraction
- `image_extraction.py` — Orchestrator, routes images to correct extractor

**New API** (`app/api/v1/ai.py`):
- `POST /api/v1/ai/extract_image` — Accepts multipart file, returns `ImageExtractionOut`

**New Schema** (`app/schemas/ai.py`):
- `ImageExtractionOut` — Validated response with optional nutrition fields

### Frontend (React/TypeScript)

**New API Client** (`frontend/src/api/ai.ts`):
- `useExtractImage()` — React Query mutation for file upload

**Updated Component** (`AddMealDrawer.tsx`):
- New views: `'image'` (upload UI), `'image-detail'` (edit + confirm)
- Image preview, file picker, editable nutrition inputs
- Integrates with existing meal save flow

## Key Features

✅ **Two extraction modes**:
- Nutrition labels → OCR + LLM = accurate reads
- Food photos → Multimodal LLM = estimated nutrition with confidence

✅ **User control**:
- Edit all pre-filled values before saving
- Adjust quantity independently

✅ **Graceful error handling**:
- Missing AWS token → 400 UNPROCESSABLE
- Failed image processing → error message shown

✅ **Consistent with existing UX**:
- Same meal drawer, meal type selection, time defaults
- Feels like "search" → "custom" but with AI assistance

## Files Created

### Backend
```
backend/
├── app/services/ai/
│   ├── __init__.py (updated)
│   ├── image_extraction.py ⭐ (NEW)
│   ├── nutrition_ocr.py ⭐ (NEW)
│   └── nutrition_llm_extract.py ⭐ (NEW)
├── app/api/v1/
│   ├── ai.py ⭐ (NEW)
│   └── router.py (updated)
├── app/schemas/
│   └── ai.py ⭐ (NEW)
└── docs/
    └── image-upload-feature.md ⭐ (NEW)
```

### Frontend
```
frontend/
├── src/api/
│   └── ai.ts ⭐ (NEW)
└── src/components/dashboard/meals/
    └── AddMealDrawer.tsx (updated)
```

## Setup & Dependencies

### Add to `backend/requirements.txt`
```
opencv-python-headless>=4.8.0
pytesseract>=0.3.10
langchain-aws>=0.2.0
```

### System Dependencies
```bash
# Ubuntu/Debian
apt-get install tesseract-ocr

# macOS
brew install tesseract
```

### Environment
Update `.env`:
```
AWS_BEARER_TOKEN_BEDROCK=<token>
```

## Testing Checklist

- [ ] Backend starts without import errors
- [ ] Frontend dev server compiles
- [ ] "Upload image" button appears in Add Meal drawer
- [ ] File picker opens on button click
- [ ] Image selected → loading spinner shows
- [ ] API call completes → nutrition appears (or error shown)
- [ ] Can edit quantity + macro values
- [ ] "Add to [meal type]" saves meal with source: 'ai'
- [ ] Meal appears in log with correct nutrition
- [ ] Existing search/custom flows still work

## API Contract

### Request
```
POST /api/v1/ai/extract_image
Authorization: Bearer <token>
Content-Type: multipart/form-data

file: <binary>
```

### Response (200)
```json
{
  "is_nutrition_label": true,
  "quantity_g": 100,
  "energy_kcal": 520,
  "protein_g": 12,
  "carb_g": 65,
  "fat_g": 18,
  "fibre_g": null,
  "sodium_mg": null,
  "food_item_name": null,
  "confidence": null,
  "estimation_basis": null
}
```

### Error (400)
```json
{
  "error": {
    "code": "UNPROCESSABLE",
    "message": "Failed to extract nutrition from image: ..."
  }
}
```

## Future Improvements

- [ ] Rate limiting per user (prevent runaway Bedrock costs)
- [ ] Image size validation (reject >10MB files)
- [ ] Async processing + webhook for large batches
- [ ] Store extracted images for debugging/retraining
- [ ] Confidence thresholds (warn on low confidence)
- [ ] Batch extraction API for bulk uploads

## Notes

- All AI module code is now in `backend/app/services/ai/` — no external dependency on `AI_based_nutrition/`
- Temporary image files are cleaned up after processing
- Pydantic models validate all numeric ranges at schema layer
- Frontend uses existing auth + meal logging infrastructure
