# updated_blog_schema.py
from __future__ import annotations
from typing import List, Optional, Dict, Any, Union
from pydantic import AliasChoices, Field, BaseModel, model_validator, root_validator
import time
import re
from bson import ObjectId
from schemas.imports import *

# ====================================================================
# BLOG SCHEMA (updated to parse & validate BlockNote JSON)
# ====================================================================

class BlogBase(BaseModel):
    """Base schema for a Blog article, covering main content fields."""
    title: str = Field(..., description="The main title of the article.")
    author: Author
    category: Category
    blogType: Optional[BlogType] = BlogType.normal
    featureImage: Optional[MediaAsset] = None
    # pages is optional, as it only appears on multi-page articles
    pages: Optional[List[Page]] = None 
    # The body content for the current page: accept raw BlockNote JSON (list of dicts)
    currentPageBody: Optional[List[Dict[str, Any]]] = Field(
        None, description="List of BlockNote-style content blocks for the current page."
    )
 

    @model_validator(mode="after")
    def check_mutually_exclusive_fields(self) -> "BlogBase":
        """
        Ensure the input provides either pages OR currentPageBody (not both).
        If currentPageBody is present and pages is None, parse and populate `parsed`.
        If pages is present and currentPageBody is None, parse each page.pageBody into parsed.
        """
        if self.pages is not None and self.currentPageBody is not None:
            raise ValueError("You must provide EITHER 'pages' OR 'currentPageBody', not both.")
        if self.pages is None and self.currentPageBody is None:
            raise ValueError("You must provide one of: 'pages' OR 'currentPageBody'.")
 
        return self


class BlogCreate(BlogBase):
    """
    Schema for creating a new Blog entry. 
    Overrides slug and excerpt to be optional and auto-generated if missing.
    """
    state: Optional[BlogStatus] = BlogStatus.draft
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
    def _generate_excerpt(current_page_body: List[Dict], max_length: int = 200) -> str:
        """
        Generate a text excerpt from a page body structure.

        Args:
            current_page_body (List[Dict]): List of blocks as in your example.
            max_length (int): Maximum length of the excerpt.

        Returns:
            str: Combined text excerpt truncated to max_length.
        """
        texts = []

        for block in current_page_body:
            # Extract text from block content
            content_list = block.get("content", [])
            for content in content_list:
                if content.get("type") == "text":
                    texts.append(content.get("text", ""))

        # Join all text segments
        full_text = " ".join(texts).strip()

        # Truncate if necessary
        if len(full_text) > max_length:
            return full_text[:max_length].rstrip() + "..."
        return full_text
    

    @model_validator(mode="after")
    def set_defaults(self) -> BlogCreate:
        """Auto-generate slug and excerpt if they were not provided."""
        # 1. Generate Slug if missing
        if not self.slug and self.title:
            self.slug = self._generate_slug(self.title)
        elif not self.slug:
            self.slug = "invalid-slug"

        # 2. Generate Excerpt if missing and parsed exists
        if not self.excerpt or self.excerpt=="Article content is currently empty.":
            self.excerpt = self._generate_excerpt(self.currentPageBody)
        elif not self.excerpt:
            self.excerpt = "Article content is currently empty."

        return self


class BlogUpdate(BaseModel):
    """Schema for updating an existing Blog entry (partial update via PATCH)."""
    state: Optional[BlogStatus] = None
    title: Optional[str] = None
    author: Optional[Author] = None
    publishDate: Optional[int] = None
    category: Optional[Category] = None
    featureImage: Optional[MediaAsset] = None
    excerpt: Optional[str] = None
    pages: Optional[List[Page]] = None 
    currentPageBody: Optional[List[Dict[str, Any]]] = None
    blogType: Optional[BlogType] = None
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
    def _generate_excerpt(current_page_body: List[Dict], max_length: int = 200) -> str:
        """
        Generate a text excerpt from a page body structure.

        Args:
            current_page_body (List[Dict]): List of blocks as in your example.
            max_length (int): Maximum length of the excerpt.

        Returns:
            str: Combined text excerpt truncated to max_length.
        """
        texts = []
        if current_page_body  is not None:
            for block in current_page_body:
                # Extract text from block content
                content_list = block.get("content", [])
                for content in content_list:
                    if content.get("type") == "text":
                        texts.append(content.get("text", ""))

            # Join all text segments
            full_text = " ".join(texts).strip()

            # Truncate if necessary
            if len(full_text) > max_length:
                return full_text[:max_length].rstrip() + "..."
            return full_text
        

    @model_validator(mode="after")
    def set_defaults(self) -> "BlogUpdate":
        """Auto-generate excerpt if missing and set publishDate when publishing."""
        # If currentPageBody present, parse it now
        

        if not self.excerpt :
            self.excerpt = self._generate_excerpt(self.currentPageBody)

        if self.state == BlogStatus.published and not self.publishDate:
            self.publishDate = int(time.time())

        return self

    @model_validator(mode="after")
    def check_mutually_exclusive_fields(self) -> "BlogUpdate":
        if self.pages is not None and self.currentPageBody is not None:
            raise ValueError("You must provide EITHER 'pages' OR 'currentPageBody', not both.")
        return self




class BlogOutLessDetail(BaseModel):
    """Output schema for a Blog entry, including MongoDB ID and timestamps."""
    id: str = Field(default=None, alias="_id")
    title: str = Field(..., description="The main title of the article.")
    author: Author
    category: Category
    blogType: Optional[BlogType] = BlogType.normal
    featureImage: Optional[MediaAsset] = None
    state: Optional[BlogStatus] = BlogStatus.draft
 
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
    slug: Optional[str] = None
    excerpt: Optional[str] = None
    totalItems:Optional[int]=None
    itemIndex:Optional[int]=None

    @staticmethod
    def _generate_excerpt(current_page_body: List[Dict], max_length: int = 200) -> str:
        """
        Generate a text excerpt from a page body structure.

        Args:
            current_page_body (List[Dict]): List of blocks as in your example.
            max_length (int): Maximum length of the excerpt.

        Returns:
            str: Combined text excerpt truncated to max_length.
        """
        texts = []

        for block in current_page_body:
            # Extract text from block content
            content_list = block.get("content", [])
            for content in content_list:
                if content.get("type") == "text":
                    texts.append(content.get("text", ""))

        # Join all text segments
        full_text = " ".join(texts).strip()

        # Truncate if necessary
        if len(full_text) > max_length:
            return full_text[:max_length].rstrip() + "..."
        return full_text
    
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
    
    @model_validator(mode="before")
    @classmethod
    def convert_objectid(cls, values: Dict[str, Any]) -> Dict[str, Any]:
        # 1. coerce ObjectId to str for _id if needed
        if "_id" in values and isinstance(values["_id"], ObjectId):
            values["_id"] = str(values["_id"])
        return values
    
    @model_validator(mode="before")
    @classmethod
    def set_excerpt(cls, values: Dict[str, Any]) -> Dict[str, Any]:
        # # 2. Generate Excerpt if missing and parsed exists
        if not values.get("excerpt",None) or values.get("excerpt",None)=="Article content is currently empty.":
            values["excerpt"] = cls._generate_excerpt(values.get("currentPageBody",[]))
        elif not values.get("excerpt",None):
            values["excerpt"] = "Article content is currently empty."

        return values
    
    @model_validator(mode="after")
    def set_defaults(self) -> "BlogOutLessDetail":
        """Auto-generate slug and excerpt if they were not provided."""
        # 3. Generate Slug if missing
        if not self.slug and self.title:
            self.slug = self._generate_slug(self.title)
        elif not self.slug:
            self.slug = "invalid-slug"
        return self


    model_config = {
        "populate_by_name": True,        # accept snake_case input
        "ser_json_typed": False,         # your setting
        "json_encoders": {
            ObjectId: str,               # keep your ObjectId encoder
        },
    }


class BlogOut(BlogBase):
    """Output schema for a Blog entry, including MongoDB ID and timestamps."""
    id: str = Field(default=None, alias="_id")
    state: Optional[BlogStatus] = BlogStatus.draft
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
    slug: Optional[str] = None
 
    excerpt: Optional[str] = None

    @staticmethod
    def _generate_excerpt(current_page_body: List[Dict], max_length: int = 200) -> str:
        """
        Generate a text excerpt from a page body structure.

        Args:
            current_page_body (List[Dict]): List of blocks as in your example.
            max_length (int): Maximum length of the excerpt.

        Returns:
            str: Combined text excerpt truncated to max_length.
        """
        texts = []

        for block in current_page_body:
            # Extract text from block content
            content_list = block.get("content", [])
            for content in content_list:
                if content.get("type") == "text":
                    texts.append(content.get("text", ""))

        # Join all text segments
        full_text = " ".join(texts).strip()

        # Truncate if necessary
        if len(full_text) > max_length:
            return full_text[:max_length].rstrip() + "..."
        return full_text
    
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
    @model_validator(mode="before")
    @classmethod
    def convert_objectid(cls, values: Dict[str, Any]) -> Dict[str, Any]:
        # coerce ObjectId to str for _id if needed
        if "_id" in values and isinstance(values["_id"], ObjectId):
            values["_id"] = str(values["_id"])
        return values
    @model_validator(mode="after")
    def set_defaults(self) :
        """Auto-generate slug and excerpt if they were not provided."""
        # 1. Generate Slug if missing
        if not self.slug and self.title or self.slug=="invalid-slug":
            self.slug = self._generate_slug(self.title)
        elif not self.slug:
            self.slug = "invalid-slug"

        # # 2. Generate Excerpt if missing and parsed exists
        if not self.excerpt  or self.excerpt=="Article content is currently empty.":
            self.excerpt = self._generate_excerpt(self.currentPageBody)
        elif not self.excerpt:
            self.excerpt = "Article content is currently empty."

        return self


    model_config = {
        "populate_by_name": True,        # accept snake_case input
        "ser_json_typed": False,         # your setting
        "json_encoders": {
            ObjectId: str,               # keep your ObjectId encoder
        },
    }