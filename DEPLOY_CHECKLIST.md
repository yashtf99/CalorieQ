# Image Upload Feature — Deploy Checklist

## Pre-Deployment Verification

### Backend Setup
- [ ] Add dependencies to `backend/requirements.txt`:
  ```
  opencv-python-headless>=4.8.0
  pytesseract>=0.3.10
  langchain-aws>=0.2.0
  ```
- [ ] Install system OCR: `apt-get install tesseract-ocr` (Linux) or `brew install tesseract` (macOS)
- [ ] Set `AWS_BEARER_TOKEN_BEDROCK` in `.env`
- [ ] Run `pip install -r requirements.txt` to install new deps
- [ ] Verify backend starts: `python -m uvicorn app.main:app --reload`
- [ ] Check route exists: `curl -H "Authorization: Bearer <token>" http://localhost:8000/api/v1/ai/extract_image`

### Frontend Setup
- [ ] No additional npm packages needed (already has axios, react-query, lucide-react)
- [ ] Dev server starts: `npm run dev`
- [ ] No TypeScript errors: `npx tsc --noEmit`

### Integration Testing
- [ ] Add Meal drawer opens
- [ ] Search view shows "Upload image" and "Log custom meal" buttons
- [ ] File picker works on click
- [ ] Select small test image (~100KB) → loading spinner appears
- [ ] API completes successfully → image preview + nutrition fields appear
- [ ] Can edit extracted values
- [ ] Click "Add to [meal type]" → meal appears in log
- [ ] Meal shows `source: 'ai'` in database or response
- [ ] Verify existing search and custom meal flows still work

### Error Cases
- [ ] Upload non-image file → graceful error message
- [ ] Network timeout → shows error
- [ ] Missing AWS token → 400 UNPROCESSABLE with helpful message
- [ ] Very large image → handle gracefully (or add size check)

## Deployment Steps

1. **Update dependencies**
   ```bash
   cd backend
   pip install -r requirements.txt
   ```

2. **Ensure system dependencies installed**
   ```bash
   # Linux
   apt-get update && apt-get install tesseract-ocr
   
   # macOS
   brew install tesseract
   ```

3. **Update environment**
   ```bash
   # Add to .env or production config
   AWS_BEARER_TOKEN_BEDROCK=<production-token>
   ```

4. **Restart backend**
   ```bash
   # Kill existing server and restart
   uvicorn app.main:app --reload
   ```

5. **Frontend rebuild (if deploying to prod)**
   ```bash
   cd frontend
   npm run build
   # Deploy dist/ folder
   ```

## Post-Deployment Validation

- [ ] Health check: `GET /docs` loads Swagger UI
- [ ] Auth flow works (login → create user)
- [ ] Upload image → nutrition extracted
- [ ] Meal saved with source: 'ai'
- [ ] Mobile responsiveness: file picker works on mobile
- [ ] Accessibility: tab navigation works, alt text on images

## Monitoring

- [ ] Watch backend logs for extraction errors
- [ ] Monitor Bedrock API costs (CloudWatch or AWS billing)
- [ ] Check for OCR failures (Tesseract crashes)
- [ ] Track user adoption (image uploads per day)

## Rollback Plan

If issues occur:
1. Remove "Upload image" button from frontend (comment out code or feature flag)
2. Disable `/api/v1/ai/extract_image` route (comment out in router)
3. Users can still use search + custom meal flows
4. No data loss or migration needed (images are ephemeral)

## Known Limitations

- Requires Bedrock API access (AWS account required)
- OCR accuracy depends on image quality
- Multimodal estimation is a guess, not a measurement
- No offline support (requires internet for Bedrock)
- Temporary images stored in system temp directory, cleaned up after request
