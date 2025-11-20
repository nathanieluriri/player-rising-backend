from bson import ObjectId
from fastapi.responses import StreamingResponse
from celery_worker import celery_app
from typing import TypeVar, Generic, Union
from repositories.media_host import save_video_to_mongodb
from schemas.imports import CategoryNameEnum
from schemas.response_schema import APIResponse
from schemas.media_host import ImageUploadResponse, MediaBase, VideoUploadResponse
from security.auth import verify_admin_token
from services.image_host import generate_media_json, upload_to_freeimage_service
from fastapi import (
    Depends,
    FastAPI,
    APIRouter,
    File,
    Form,
    Request,
    UploadFile,
    HTTPException,
    status
)
from core.database import db
from bson import ObjectId
from services.blog_service import update_blog_by_id, retrieve_blog_by_blog_id
from schemas.blog import BlogOut, BlogUpdate,BlogBase
from motor.motor_asyncio import AsyncIOMotorGridFSBucket

fs = AsyncIOMotorGridFSBucket(db)
# ------------------------------
# Router Setup
# ------------------------------
router = APIRouter(
    prefix="/media",
    tags=["Media"]
)
@router.post(
    "/upload-media",
    
    dependencies=[Depends(verify_admin_token)],
    response_model=Union[APIResponse[VideoUploadResponse],APIResponse[ImageUploadResponse]],
    status_code=status.HTTP_201_CREATED,
    summary="Upload an image or video",
    description=(
        "This endpoint uploads either an image or a video. "
        "Images are uploaded to FreeImage.Host, while videos are stored "
        "in MongoDB GridFS. The endpoint automatically detects media type "
        "based on file MIME type."
    )
)
async def upload_media(
    request: Request,
    file: UploadFile = File(
        ...,
        description="Image or video file (JPG, PNG, GIF, MP4, MOV, AVI, etc.)"
    )
):
    """
    Uploads a media file (image or video).
    - Images → uploaded to FreeImage.Host
    - Videos → stored in MongoDB GridFS
    """

    content_type = file.content_type.lower()

    # Determine if the uploaded file is an image
    if content_type.startswith("image/"):
        # Upload to FreeImage.Host
        image_url = await upload_to_freeimage_service(file)

        return APIResponse(
            status_code=201,
            data=ImageUploadResponse(
                url=image_url,
                media_type="image",
            ),
            detail="Image uploaded successfully"
        )

    # Determine if it’s a video
    elif content_type.startswith("video/"):
        video_url = await save_video_to_mongodb(file)
        full_url = str(request.base_url).rstrip("/") + video_url

        return APIResponse(
            status_code=201,
            data=VideoUploadResponse(
                url=full_url
              
            ),
            detail="Video uploaded successfully"
        )

    # Unsupported file type
    else:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type: {content_type}"
        )
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
@router.post(
    "/",
    
    dependencies=[Depends(verify_admin_token)],
    status_code=status.HTTP_201_CREATED,
    summary="Upload an image or video",
    description=(
        "This endpoint uploads either an image or a video. "
        "Images are uploaded to FreeImage.Host, while videos are stored "
        "in MongoDB GridFS. The endpoint automatically detects media type "
        "based on file MIME type."
    )
)
async def upload_new_content_with_a_category(
    
    request: Request,
    category:CategoryNameEnum=Form(...),
    file: UploadFile = File(
        ...,
        description="Image or video file (JPG, PNG, GIF, MP4, MOV, AVI, etc.)"
    )
):
    """
    Uploads a media file (image or video).
    - Images → uploaded to FreeImage.Host
    - Videos → stored in MongoDB GridFS
    """

    file_bytes = await file.read()

    # Get filename and content type
    filename = file.filename
    content_type = file.content_type
    media = MediaBase(mediaType="image",category=category)
    # Determine if the uploaded file is an image
    if content_type.startswith("image/"):
        # Upload to FreeImage.Host
        
        media.mediaType="image"
        job_id = celery_app.send_task(name= "celery_worker.create_media_task",args=[media.model_dump(), file_bytes, filename, content_type])
         
        return APIResponse(
            status_code=201,
            data=f"{job_id}" ,
            detail="Image Job uploaded successfully"
        )

    # Determine if it’s a video
    elif content_type.startswith("video/"):
        media.mediaType="video"
        media.requestUrl = str(request.base_url).rstrip("/") 
        job_id = celery_app.send_task(name= "celery_worker.create_media_task",args=[media.model_dump(), file_bytes, filename, content_type])
         
        return APIResponse(
            status_code=201,
            data=f"{job_id}" ,
            detail="Video Job uploaded successfully"
        )

    # Unsupported file type
    else:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type: {content_type}"
        )


# ------------------------------
# Upload a new Image
# ------------------------------
@router.post(
    "/upload-image",
    dependencies=[Depends(verify_admin_token)],
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
    
    
    

# ----------------------------------
# Upload a new Video
# ----------------------------------
@router.post(
    "/upload-video",
    response_model=APIResponse[VideoUploadResponse],
    dependencies=[Depends(verify_admin_token)],
    status_code=status.HTTP_201_CREATED,
    summary="Upload a video and store it in MongoDB",
    description=(
        "This endpoint uploads a video file (MP4, MOV, AVI, etc.) and stores "
        "it in MongoDB GridFS. It returns a URL that can be used to stream "
        "or download the stored video."
    )
)
async def upload_video(
    request: Request,
    file: UploadFile = File(
        ...,
        description="Video file to upload (MP4, MOV, AVI, MKV, WEBM)."
    )
):
    """
    Uploads a new video and stores it in MongoDB using GridFS.
    
    This route handles the upload request and delegates the actual
    MongoDB storage logic to the service function.
    """

    # Store the video in MongoDB GridFS
    video_url = await save_video_to_mongodb(file)
    full_url = str(request.base_url).rstrip("/") + video_url
    # Return formatted response
    return APIResponse(
        status_code=201,
        data=VideoUploadResponse(url=full_url),
        detail="Video uploaded successfully"
    )





@router.post(
    "/{blog_id}",
    
    dependencies=[Depends(verify_admin_token)],
    response_model=APIResponse[BlogOut],  # dynamic: contains either image or video URL
    status_code=status.HTTP_201_CREATED,
    summary="Upload an image or video and add the url of the upload to the last item  of the blog",
    description=(
        "Uploads either an image (JPG, PNG, WEBP, GIF) to FreeImage.Host or "
        "a video (MP4, MOV, AVI, MKV, WEBM) to MongoDB GridFS. "
        "Automatically detects file type and returns the appropriate URL."
    )
)
async def add_image_or_video_block_to_a_blog(
    blog_id:str,
    request: Request,
    caption:str=Form(
        ...,
        description="Caption for the content"
    ),

   file: UploadFile = File(
        ...,
        description="Image or video file to upload."
    ),
   
):
    """
    Universal upload endpoint for images and videos.
    """
    blog = await retrieve_blog_by_blog_id(id=blog_id)
    if blog is not None:

        
        content_type = file.content_type.lower()

        # -----------------------------
        # Detect and process IMAGE files
        # -----------------------------
        image_types = {"image/jpeg", "image/png", "image/gif", "image/webp", "image/bmp"}

        if content_type in image_types:
            image_url = await upload_to_freeimage_service(file)
            newly_added_media=  generate_media_json(file_url=image_url,caption=caption)
            blog.currentPageBody.append(newly_added_media)
            blog_page_data =BlogUpdate(currentPageBody=blog.currentPageBody)
            new_blog = await update_blog_by_id(blog_id=blog_id,blog_data=blog_page_data)
            return APIResponse(
                status_code=201,
                data=new_blog,
                detail="Image uploaded successfully"
            )

        # -----------------------------
        # Detect and process VIDEO files
        # -----------------------------
        video_types = {
            "video/mp4",
            "video/quicktime",   # MOV
            "video/x-msvideo",   # AVI
            "video/x-matroska",  # MKV
            "video/webm"
        }

        if content_type in video_types:
            video_url = await save_video_to_mongodb(file)
            full_url = str(request.base_url).rstrip("/") + video_url
            newly_added_media=  generate_media_json(file_url=full_url,caption=caption,media_type="video")
            blog.currentPageBody.append(newly_added_media)
            blog_page_data =BlogUpdate(currentPageBody=blog.currentPageBody)
            new_blog = await update_blog_by_id(blog_id=blog_id,blog_data=blog_page_data)
            return APIResponse(
                status_code=201,
                data=new_blog,
                detail="Video uploaded successfully"
            )

        # -----------------------------
        # Unsupported file type
        # -----------------------------
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type: {content_type}. "
                "Upload must be an image or video."
        )
    else:
        raise HTTPException(
            status_code=404,
            detail="Blog Id Is Invalid because the blog you want to update couldn't be found"
        )