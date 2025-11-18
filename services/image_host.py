import os
import httpx
from fastapi import UploadFile, HTTPException, status
import uuid
from typing import Literal
# --- Configuration (assumed to be accessible) ---
FREEIMAGE_API_KEY = os.environ.get("FREEIMAGE_API_KEY")
FREEIMAGE_API_URL = "https://freeimage.host/api/1/upload"

# ------------------------------
# Upload Image Service
# ------------------------------

async def upload_to_freeimage_service(file: UploadFile) -> str:
    """
    Service function to upload an image to freeimage.host.

    Handles API key check, file processing, external API call, 
    and all error handling.

    Args:
        file: The UploadFile object from the FastAPI request.

    Returns:
        str: The URL of the successfully uploaded image.

    Raises:
        HTTPException 500: If the API key is not configured.
        HTTPException 503: If the external service is unreachable.
        HTTPException 4xx/5xx: If the external service returns an error.
        HTTPException 400: If the external service's response is valid
                           but indicates a logical failure.
        HTTPException 500: If the external service's response is malformed.
    """
    
    # 1. Check for API Key
    if not FREEIMAGE_API_KEY:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Image hosting service is not configured. API key is missing."
        )

    # 2. Prepare the request for the external API
    params = {
        "key": FREEIMAGE_API_KEY,
        "action": "upload",
        "format": "json"
    }

    # Read the file content and prepare the multipart/form-data payload
    try:
        file_content = await file.read()
        files_payload = {
            "source": (file.filename, file_content, file.content_type)
        }
    finally:
        await file.close()

    # 3. Send the request to the external API
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                FREEIMAGE_API_URL,
                params=params,
                files=files_payload
            )
            
            # Raise an exception for HTTP errors (e.g., 404, 500)
            response.raise_for_status()

        except httpx.RequestError as e:
            # Network-related errors
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"Failed to connect to the image hosting service: {e}"
            )
        
        except httpx.HTTPStatusError as e:
            # Errors returned by the external API (4xx, 5xx)
            raise HTTPException(
                status_code=e.response.status_code,
                detail=f"Image host returned an error: {e.response.text}"
            )

    # 4. Parse the response from the external API
    try:
        data = response.json()
        
        # Check for *logical* errors reported in the JSON body
        if data.get("status_code") != 200 or "image" not in data or "url" not in data["image"]:
            error_detail = data.get("status_txt", "Unknown error from image host")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Image host failed to process the image: {error_detail}"
            )
            
        # 5. Return the image URL on success
        image_url: str = data["image"]["url"]
        return image_url

    except Exception:
        # Catch JSON decoding errors or unexpected structures
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to parse response from image host: {response.text}"
        )
        
        

def generate_media_json(
    file_url: str, 
    caption: str = "", 
    media_type: Literal["image", "video"] = "image"
) -> dict:
    """
    Generates a JSON object for an uploaded media file.

    :param file_url: URL where the media is accessible
    :param caption: Optional caption for the media (camera emoji will be prepended automatically)
    :param media_type: Must be either 'image' or 'video'
    :return: dict representing the JSON structure
    """
    # Ensure the caption always includes the camera emoji
    full_caption = f"📷 {caption}" if caption else "📷"

    return {
        "id": str(uuid.uuid4()),  # unique ID for every upload
        "type": media_type,
        "props": {
            "textAlignment": "center",
            "backgroundColor": "default",
            "name": "",
            "url": file_url,
            "caption": full_caption,
            "showPreview": True,
            "previewWidth": 756
        },
        "children": []
    }