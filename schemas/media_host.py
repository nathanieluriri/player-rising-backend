# Define the specific data model for this endpoint's response
from typing import Any, Dict, List, Literal, Optional
from bson import ObjectId
from pydantic import AliasChoices, BaseModel, Field, model_validator
from schemas.imports import Category, CategoryNameEnum
import time


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
    
class MediaUpdate(BaseModel):
    category: CategoryNameEnum
    
class MediaCreate(MediaBase):
    url:str
    name:str
    date_created: int = Field(default_factory=lambda: int(time.time()))
    last_updated: int = Field(default_factory=lambda: int(time.time()))
class MediaOut(MediaCreate):
    totalItems:Optional[int]=None
    itemIndex:Optional[int]=None
    date_created: Optional[int] = Field(
        default=None,
        validation_alias=AliasChoices("date_created", "dateCreated"),
        serialization_alias="dateCreated",
    )
    last_updated: Optional[int] = Field(
        default=None,
        validation_alias=AliasChoices("last_updated", "lastUpdated"),
        serialization_alias="lastUpdated",
    )
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
    
    
class MediaOutUser(MediaCreate):
   
    itemIndex:Optional[int]=None
    date_created: Optional[int] = Field(
        default=None,
        validation_alias=AliasChoices("date_created", "dateCreated"),
        serialization_alias="dateCreated",
    )
    last_updated: Optional[int] = Field(
        default=None,
        validation_alias=AliasChoices("last_updated", "lastUpdated"),
        serialization_alias="lastUpdated",
    )
    id: Optional[str] = Field(
        default=None,
        validation_alias=AliasChoices("_id", "id"),
        serialization_alias="id",
    )
    @staticmethod
    def convert_http_to_https(value: str) -> str:
        """Convert an http URL to https if it starts with http://"""
        if isinstance(value, str) and value.startswith("http://"):
            return "https://" + value[len("http://"):]
        return value
    @model_validator(mode="before")
    @classmethod
    def convert_objectid_and_urls(cls, values: Any) -> Dict[str, Any]:
        # If values is not a dict, return it unchanged
        if not isinstance(values, dict):
            return values

        # 1. coerce ObjectId to str for _id if needed
        if "_id" in values and isinstance(values["_id"], ObjectId):
            values["_id"] = str(values["_id"])
        
        # 2. Convert http URLs to https for all string fields
        for k, v in values.items():
            if isinstance(v, str):
                values[k] = cls.convert_http_to_https(v)
            elif isinstance(v, list):
                values[k] = [cls.convert_http_to_https(item) if isinstance(item, str) else item for item in v]
        
        return values
    
class ListOfMediaOut(BaseModel):
    totalItems:Optional[int]=None
    listOfMedia:List[MediaOutUser]