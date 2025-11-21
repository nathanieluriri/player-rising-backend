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
    @model_validator(mode="before")
    @classmethod
    def convert_objectid(cls, values: Dict[str, Any]) -> Dict[str, Any]:
        # 1. coerce ObjectId to str for _id if needed
        if "_id" in values and isinstance(values["_id"], ObjectId):
            values["_id"] = str(values["_id"])
        return values
    
    
class ListOfMediaOut(BaseModel):
    totalItems:Optional[int]=None
    listOfMedia:List[MediaOutUser]