# Image Upload Feature — Quick Start for Developers

## What's New?

Users can now upload **nutrition label photos** or **food photos** to quickly log meals without searching.

```
Add Meal → [Upload image] → Select photo → Edit nutrition → Save
```

## 3-Minute Setup

### 1. Backend Dependencies
```bash
cd backend
pip install opencv-python-headless pytesseract langchain-aws
# Ubuntu: apt-get install tesseract-ocr
# macOS: brew install tesseract
```

### 2. Environment
Add to `.env`:
```
AWS_BEARER_TOKEN_BEDROCK=<your-bedrock-token>
```

### 3. Start Servers
```bash
# Terminal 1
cd backend && bash start.sh

# Terminal 2
cd frontend && bash start.sh
```

## Where to Look

### Code Changes
- **Backend AI logic**: `backend/app/services/ai/` (3 files)
- **API endpoint**: `backend/app/api/v1/ai.py`
- **Frontend UI**: `frontend/src/components/dashboard/meals/AddMealDrawer.tsx`
- **Frontend API**: `frontend/src/api/ai.ts`

### Documentation
- Full feature docs: `backend/docs/image-upload-feature.md`
- Implementation details: `IMPLEMENTATION_SUMMARY.md`
- Deployment steps: `DEPLOY_CHECKLIST.md`
- UI flow diagram: `frontend/docs/IMAGE_UPLOAD_FLOW.md`

## Testing

### Quick Smoke Test
```bash
# Backend running?
curl -s http://localhost:8000/docs | grep -q "extract_image" && echo "✓ Backend OK"

# Frontend running?
curl -s http://localhost:5173 | grep -q "CalorieQ" && echo "✓ Frontend OK"
```

### Manual Test
1. Go to http://localhost:5173
2. Login
3. Click "Add Meal" → "Upload image"
4. Select a nutrition label photo or food photo
5. Verify nutrition fields appear
6. Click "Add to lunch"
7. Verify meal appears in log

## Key Files at a Glance

| File | Purpose | Lines |
|------|---------|-------|
| `app/services/ai/image_extraction.py` | Orchestrator | ~50 |
| `app/services/ai/nutrition_ocr.py` | Tesseract pipeline | ~180 |
| `app/services/ai/nutrition_llm_extract.py` | Bedrock extraction | ~210 |
| `app/api/v1/ai.py` | API endpoint | ~20 |
| `app/schemas/ai.py` | Response schema | ~25 |
| `frontend/src/api/ai.ts` | API client | ~25 |
| `AddMealDrawer.tsx` | UI component | ~730 (total, 200+ lines added) |

## How It Works (30-second version)

```
User uploads image
    ↓
Backend saves to temp file
    ↓
Tesseract OCR extracts text
    ↓
Check if nutrition label keywords present
    ├─ YES → Send OCR text to Bedrock → Get structured nutrition
    └─ NO → Send image to multimodal Bedrock → Estimate nutrition + confidence
    ↓
Return JSON with nutrition fields
    ↓
Frontend shows editable form with extracted values
    ↓
User clicks "Add" → Saves as meal with source: 'ai'
```

## Debugging

### "No module named 'pytesseract'"
- Missing: `pip install pytesseract`
- Also need: Tesseract binary (`apt-get install tesseract-ocr`)

### "AWS_BEARER_TOKEN_BEDROCK not found"
- Add to `.env`: `AWS_BEARER_TOKEN_BEDROCK=<token>`
- Restart backend: `bash start.sh`

### Image upload hangs
- Check backend logs: `tail -f backend/logs/backend.log`
- Network timeout? Try smaller image (<2MB)
- Bedrock down? Check AWS console

### Nutrition fields empty
- Image too blurry/small? Try clearer photo
- Wrong image type? (Should be actual nutrition label or food, not random image)
- Check backend console for LLM errors

## Common Customizations

### Change default portion size
Edit `AddMealDrawer.tsx` line ~130:
```javascript
const [quantity, setQuantity] = useState(100) // Change to 150
```

### Adjust image size limit
Edit `api/ai.ts` (add validation):
```typescript
if (file.size > 5 * 1024 * 1024) throw new Error('File too large')
```

### Skip manual editing
Comment out inputs in `image-detail` view in `AddMealDrawer.tsx`

## What's Self-Contained

✓ All AI code lives in `backend/app/services/ai/` (not depending on root-level `AI_based_nutrition/`)  
✓ No external API calls except Bedrock (AWS)  
✓ No database schema changes needed  
✓ Frontend uses existing React patterns + Tailwind

## What's NOT Included

✗ Rate limiting (add if worried about Bedrock costs)  
✗ Image storage (temp files deleted after request)  
✗ Batch processing API  
✗ Mobile camera permission handling (browser handles)
