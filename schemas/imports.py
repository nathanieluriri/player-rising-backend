from bson import ObjectId
from pydantic import GetJsonSchemaHandler
from pydantic import BaseModel, EmailStr, Field,model_validator
from pydantic_core import core_schema
from datetime import datetime,timezone
from typing import Optional,List,Any
from enum import Enum
import time
from typing import List, Optional, Union, Literal
# --- Nested Schemas ---

class Author(BaseModel):
    """Schema for the article author details."""
    name: str
    avatarUrl: Optional[str] = Field(None, description="URL of the author's avatar image.")
    affiliation: str

class Category(BaseModel):
    """Schema for the article category."""
    name: str
    slug: str
    
class BlogStatus(str,Enum):
    published= "published"
    draft = "draft"
    

class MediaAsset(BaseModel):
    """Schema for feature and inline images."""
    url: str
    altText: str = Field(..., description="A brief description of the image for accessibility.")
    credit: Optional[str] = Field(None, description="Image credit/source information.")

class Pagination(BaseModel):
    """Schema for multi-page article navigation details."""
    currentPage: int
    totalPages: int
    nextPageUrl: Optional[str] = None
    prevPageUrl: Optional[str] = None
    
# --- Content Block Schemas (Polymorphic Body) ---
# These are used to represent the different 'type' of objects found in currentPageBody.

class TextBlock(BaseModel):
    """A standard block of text content."""
    type: Literal["text"]
    content: str

class ImageBlock(BaseModel):
    """A block containing an inline image."""
    type: Literal["image"]
    url: str
    altText: str
    caption: Optional[str] = None

class QuoteBlock(BaseModel):
    """A block for a pull quote."""
    type: Literal["quote"]
    text: str

class DividerBlock(BaseModel):
    """A simple horizontal rule divider."""
    type: Literal["divider"]
    # No content field needed

# Define the Union of all possible content blocks for the article body
BodyBlock = Union[TextBlock, ImageBlock, QuoteBlock, DividerBlock]
