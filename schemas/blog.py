# ============================================================================
# BLOG SCHEMA
# ============================================================================
# This file was auto-generated on: 2025-11-14 19:55:59 WAT
# It contains Pydantic classes  database
# for managing attributes and validation of data in and out of the MongoDB database.
#
# ============================================================================

from schemas.imports import *
from pydantic import Field, BaseModel, model_validator
import time

from bson import ObjectId # Assuming ObjectId is available
import re # Added import for slug generation



class BlogBase(BaseModel):
    """Base schema for a Blog article, covering main content fields."""
    title: str = Field(..., description="The main title of the article.")
    author: Author
    publishDate: str = Field(..., description="Publication date in ISO 8601 format (e.g., 'YYYY-MM-DDTHH:MM:SSZ').")
    category: Category
    featureImage: MediaAsset
    # Pagination is optional, as it only appears on multi-page articles
    pagination: Optional[Pagination] = None 
    # The body content for the current page, which is a list of mixed content types
    currentPageBody: List[BodyBlock] = Field(..., description="List of content blocks for the current page of the article.")


class BlogCreate(BlogBase):
    """
    Schema for creating a new Blog entry. 
    Overrides slug and excerpt to be optional and auto-generated if missing.
    """
    # Overriding BlogBase fields to make them optional for creation
    slug: Optional[str] = Field(None, description="Optional. If None, will be auto-generated from the title.")
    excerpt: Optional[str] = Field(None, description="Optional. If None, will be auto-generated from the first text block in the body.")

    date_created: int = Field(default_factory=lambda: int(time.time()))
    last_updated: int = Field(default_factory=lambda: int(time.time()))

    @staticmethod
    def _generate_slug(title: str) -> str:
        """Helper to slugify a title."""
        title = title.lower()
        # Replace non-alphanumeric (except spaces and hyphens) with nothing
        title = re.sub(r'[^a-z0-9\s-]', '', title)
        # Replace one or more spaces/hyphens with a single hyphen
        title = re.sub(r'[\s-]+', '-', title)
        # Remove leading/trailing hyphens
        title = title.strip('-')
        return title if title else "untitled-blog"

    @staticmethod
    def _generate_excerpt(body: List[BodyBlock]) -> str:
        """Helper to generate an excerpt from the first TextBlock content."""
        MAX_EXCERPT_LENGTH = 150
        
        for block in body:
            # Check for the literal type 'text'
            # Note: Pydantic deserializes the Union type based on the 'type' field
            if block.type == 'text':
                content = block.content.strip()
                if not content:
                    continue # Skip empty text blocks
                
                # Truncate content for excerpt
                if len(content) > MAX_EXCERPT_LENGTH:
                    return content[:MAX_EXCERPT_LENGTH].strip() + "..."
                return content
                
        return "No introductory text available for excerpt generation." # Fallback if no text is found

    @model_validator(mode="after")
    def set_defaults(self) -> 'BlogCreate':
        """Auto-generate slug and excerpt if they were not provided."""
        
        # 1. Generate Slug if missing
        if not self.slug and self.title:
            self.slug = self._generate_slug(self.title)
        elif not self.slug:
             self.slug = "invalid-slug"

        # 2. Generate Excerpt if missing and body exists
        if not self.excerpt and self.currentPageBody:
            self.excerpt = self._generate_excerpt(self.currentPageBody)
        elif not self.excerpt:
            self.excerpt = "Article content is currently empty."
            
        return self


class BlogUpdate(BaseModel):
    """Schema for updating an existing Blog entry (partial update via PATCH)."""
    # All fields are Optional to allow non-breaking partial updates
    state:Optional[BlogStatus]=BlogStatus.draft
    title: Optional[str] = None
    author: Optional[Author] = None
    publishDate: Optional[int] = None
    category: Optional[Category] = None
    featureImage: Optional[MediaAsset] = None
    excerpt: Optional[str] = None
    pagination: Optional[Pagination] = None
    currentPageBody: Optional[List[BodyBlock]] = None
    last_updated: int = Field(default_factory=lambda: int(time.time()))
 

    @staticmethod
    def _generate_excerpt(body: List[BodyBlock]) -> str:
        """Helper to generate an excerpt from the first TextBlock content."""
        MAX_EXCERPT_LENGTH = 150
        
        for block in body:
            # Check for the literal type 'text'
            # Note: Pydantic deserializes the Union type based on the 'type' field
            if block.type == 'text':
                content = block.content.strip()
                if not content:
                    continue # Skip empty text blocks
                
                # Truncate content for excerpt
                if len(content) > MAX_EXCERPT_LENGTH:
                    return content[:MAX_EXCERPT_LENGTH].strip() + "..."
                return content
                
        return "No introductory text available for excerpt generation." # Fallback if no text is found

    @model_validator(mode="after")
    def set_defaults(self) -> 'BlogUpdate':
        """Auto-generate excerpt if they were not provided."""
        
        # 2. Generate Excerpt if missing and body exists
        if not self.excerpt and self.currentPageBody:
            self.excerpt = self._generate_excerpt(self.currentPageBody)
        elif not self.excerpt:
            self.excerpt = "Article content is currently empty."
        
        if self.state ==BlogStatus.published:
            self.publishDate = int(time.time())
        
        return self

class BlogOut(BlogBase):
    """Output schema for a Blog entry, including MongoDB ID and timestamps."""
    id: Optional[str] = Field(default=None, alias="_id")
    date_created: Optional[int] = None
    last_updated: Optional[int] = None
    slug: Optional[str] = None
    excerpt: Optional[str] = None
    @model_validator(mode="before")
    @classmethod
    def convert_objectid(cls, values):
        if "_id" in values and isinstance(values["_id"], ObjectId):
            values["_id"] = str(values["_id"])  # coerce to string before validation
        return values
            
    class Config:
        populate_by_name = True  # allows using `id` when constructing the model
        arbitrary_types_allowed = True  # allows ObjectId type
        json_encoders = {
            ObjectId: str  # automatically converts ObjectId to str
        }