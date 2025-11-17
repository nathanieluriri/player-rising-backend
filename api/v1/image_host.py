import os
import httpx
from typing import TypeVar, Generic
from schemas.response_schema import APIResponse
from schemas.image_host import ImageUploadResponse
from services.image_host import upload_to_freeimage_service
from fastapi import (
    FastAPI,
    APIRouter,
    File,
    UploadFile,
    HTTPException,
    status
)
from pydantic import BaseModel
from pydantic.generics import GenericModel
import uvicorn


# ------------------------------
# Router Setup
# ------------------------------
router = APIRouter(
    prefix="/media",
    tags=["Media"]
)

# ------------------------------
# Upload a new Image
# ------------------------------
@router.post(
    "/upload-image",
    response_model=APIResponse[ImageUploadResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Upload an Image to FreeImage.Host",
    description=(
        "This endpoint uploads an image file (JPG, PNG, GIF, etc.) to the "
        "freeimage.host API and returns a direct link to the hosted image."
    )
)
async def upload_image(
    file: UploadFile = File(
        ...,
        description="The image file to upload (JPG, PNG, BMP, GIF, WEBP)."
    )
):
    """
    Uploads a new image by calling the image hosting service.
    
    This route handles the HTTP request/response, while the underlying
    service function handles the upload logic and error checking.
    """
    
 
 
    
    # Using the local function for this example:
    image_url = await upload_to_freeimage_service(file)


    # 2. If we get here, the upload was successful.
    # Format the successful response.
    return APIResponse(
        status_code=201,
        data=ImageUploadResponse(url=image_url),
        detail="Image uploaded successfully"
    )