# Define the specific data model for this endpoint's response
from pydantic import BaseModel


class ImageUploadResponse(BaseModel):
    """
    The "data" part of the response, containing the uploaded image URL.
    """
    url: str


class VideoUploadResponse(BaseModel):
    """
    The "data" part of the response, containing the uploaded Video URL.
    """
    url: str
