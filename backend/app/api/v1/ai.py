from fastapi import APIRouter, Depends, UploadFile, File
from app.api.deps import get_current_user
from app.models.user import User
from app.schemas.ai import ImageExtractionOut
from app.services.ai import extract_nutrition_from_image_upload

router = APIRouter(prefix="/ai", tags=["ai"])


@router.post("/extract_image", response_model=ImageExtractionOut, status_code=200)
async def extract_image(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
):
    """
    Upload an image (nutrition label or food photo) and extract nutrition data.

    Returns:
    - For nutrition labels: extracted macros + serving size
    - For food photos: identified food + estimated macros + confidence level
    """
    contents = await file.read()
    result = extract_nutrition_from_image_upload(contents, file.filename or "image")
    return ImageExtractionOut(**result)
