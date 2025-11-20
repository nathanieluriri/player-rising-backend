import os
from celery import Celery
from dotenv import load_dotenv
import asyncio
import celery_aio_pool as aio_pool

from repositories.media_host import create_media, save_video_to_mongodb, save_video_to_mongodb_from_bytes, update_media_category
from schemas.media_host import MediaBase, MediaCreate, MediaUpdate
from services.image_host import upload_to_freeimage_service, upload_to_freeimage_service_from_bytes
load_dotenv()

broker_url = os.getenv("CELERY_BROKER_URL")
backend_url = os.getenv("CELERY_RESULT_BACKEND")

celery_app = Celery("worker", broker=broker_url, backend=backend_url,)
celery_app.conf.update(task_track_started=True)

@celery_app.task(name="celery_worker.test_scheduler")
async def test_scheduler(message):
    print(message)
    
    
@celery_app.task(name="celery_worker.create_media_task")
async def create_media_task(media_dict: dict,file_bytes: bytes, filename: str, content_type: str):
    """
    Celery worker for creating media from async function.
    """
    media = MediaBase(**media_dict)
    if media.mediaType=="image":
        image_url = await upload_to_freeimage_service_from_bytes(file_bytes, filename, content_type)
        media_data = MediaCreate(**media_dict,url=image_url,name=filename)
    elif media.mediaType=="video":
        video_url = await save_video_to_mongodb_from_bytes((file_bytes, filename, content_type))
        full_url = media.requestUrl + video_url
        media_data = MediaCreate(**media_dict,url=full_url,name=filename)
    
    
    return await create_media(media_data)


@celery_app.task(name="celery_worker.update_media_category_task")
async def update_media_category_task(filter_dict: dict, media_dict: dict):
    """
    Celery worker for updating media category from async function.
    """
 
    media_data = MediaUpdate(**media_dict)
    return await update_media_category(filter_dict, media_data)

 