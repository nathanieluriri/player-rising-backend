# Define the specific data model for this endpoint's response
from typing import Any, Dict, Literal, Optional
from bson import ObjectId
from pydantic import AliasChoices, BaseModel, Field, model_validator
from schemas.imports import Category, CategoryNameEnum


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


class MediaBase(BaseModel):
    mediaType: Literal["video", "image"]
    category: CategoryNameEnum
    requestUrl:Optional[str]=None
    
class MediaUpdate(MediaBase):
    pass
    
class MediaCreate(MediaBase):
    url:str
    name:str
class MediaOut(MediaCreate):
    
    id: Optional[str] = Field(
        default=None,
        validation_alias=AliasChoices("_id", "id"),
        serialization_alias="id",
    )
    @model_validator(mode="before")
    @classmethod
    def convert_objectid(cls, values: Dict[str, Any]) -> Dict[str, Any]:
        # 1. coerce ObjectId to str for _id if needed
        if "_id" in values and isinstance(values["_id"], ObjectId):
            values["_id"] = str(values["_id"])
        return values