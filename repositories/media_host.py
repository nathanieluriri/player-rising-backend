# ============================================================================
# Media_HOST REPOSITORY
# ============================================================================

# ============================================================================

from pymongo import ReturnDocument
from core.database import db
from fastapi import HTTPException, UploadFile,status
from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorGridFSBucket
from schemas.media_host import MediaCreate, MediaBase, MediaOut,MediaUpdate
from typing import List,Optional


fs = AsyncIOMotorGridFSBucket(db)

 

async def create_media(media_data: MediaCreate) -> MediaOut:
    media_dict = media_data.model_dump()
    result =await db.media.insert_one(media_dict)
    result = await db.media.find_one(filter={"_id":result.inserted_id})
    returnable_result = MediaOut(**result)
    return returnable_result

async def get_media(filter_dict: dict) -> Optional[MediaOut]:
    try:
        result = await db.media.find_one(filter_dict)

        if result is None:
            return None

        return MediaOut(**result)

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while fetching media: {str(e)}"
        )
    
async def get_media_files(
    filter_dict: Optional[dict] = None,
    start: int = 0,
    stop: int = 100,
    sort_field: Optional[str] = None,
    sort_order: Optional[int] = None  # 1 for ascending, -1 for descending
) -> List[MediaOut]:
 
    try:
        if filter_dict is None:
            filter_dict = {}

        # Base query
        cursor = db.media.find(filter_dict)
        total_media = await db.media.count_documents(filter_dict)
        # Apply sorting
        if sort_field and sort_order:
            cursor = cursor.sort(sort_field, sort_order)
        else:
            # Default sorting: newest first
            cursor = cursor.sort("date_created", -1)

        # Apply pagination AFTER sorting
        cursor = cursor.skip(start).limit(stop - start)

        media_list = []
        itemIndex=1
        async for doc in cursor:
            media_doc = MediaOut(**doc)
            media_doc.totalItems= total_media
            media_doc.itemIndex=itemIndex
            media_list.append(media_doc)
            itemIndex += 1

        return media_list

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while fetching media: {str(e)}"
        )

async def update_media_category(filter_dict: dict, media_data: MediaUpdate) -> MediaOut:
    result = await db.media.find_one_and_update(
        filter_dict,
        {"$set": media_data.model_dump(exclude_none=True)},
        return_document=ReturnDocument.AFTER
    )
    returnable_result = MediaOut(**result)
    return returnable_result

async def delete_media(filter_dict: dict):
    return await db.media.delete_one(filter_dict)

async def save_video_to_mongodb(file: UploadFile) -> str:

    upload_stream = fs.open_upload_stream(
        file.filename,
        metadata={"content_type": file.content_type}
    )

    # 2. Write file in chunks
    while True:
        chunk = await file.read(1024 * 1024)  # 1 MB chunks
        if not chunk:
            break
        await upload_stream.write(chunk)

    # 3. Close stream
    await upload_stream.close()

    # 4. Get the object ID of the uploaded file
    video_id = upload_stream._id

    # 5. Return a URL to access the video
    return f"/videos/{str(video_id)}"

async def save_video_to_mongodb_from_bytes(
    file_bytes: bytes,
    filename: str,
    content_type: str
) -> str:

    # 1. Create GridFS upload stream
    upload_stream = fs.open_upload_stream(
        filename,
        metadata={"content_type": content_type}
    )

    # 2. Write bytes in chunks (GridFS requires streaming)
    CHUNK_SIZE = 1024 * 1024  # 1 MB

    for i in range(0, len(file_bytes), CHUNK_SIZE):
        chunk = file_bytes[i : i + CHUNK_SIZE]
        await upload_stream.write(chunk)

    # 3. Finalize the upload
    await upload_stream.close()

    # 4. Get GridFS file ID
    video_id = upload_stream._id

    # 5. Return URL to the video
    return f"/videos/{str(video_id)}"