from pymongo import ReturnDocument
from core.database import db
from fastapi import HTTPException, UploadFile,status
from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorGridFSBucket

fs = AsyncIOMotorGridFSBucket(db)

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
