# updated_blog_schema.py
from __future__ import annotations
from typing import List, Optional, Dict, Any, Union
from pydantic import Field, BaseModel, model_validator, root_validator
import time
import re
from bson import ObjectId

# ---- Assumed existing imports in your project (Author, Category, Page, MediaAsset, BlogStatus, BlogType, etc.)
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
    # parsed = the parsed/typed tree produced with parse_document(); set at validation time
    parsed: Optional[List[BaseBlock]] = None

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

        # If currentPageBody provided, parse it into typed models
       

        # If pages provided, parse each Page.pageBody into parsed list of lists
         

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
    def _extract_text_from_inline(inline: Union[Dict[str, Any], BaseBlock, Any]) -> str:
        """
        Given an inline element (dict or model) try to extract text.
        Handles shapes:
          - {"type":"text","text":"..."}
          - StyledText Pydantic models
          - LinkInline content lists
        """
        if inline is None:
            return ""
        # If it's a dict
        if isinstance(inline, dict):
            t = inline.get("type")
            if t == "text":
                return (inline.get("text") or "").strip()
            if t == "link":
                # link.content is typically a list of inline texts
                s = ""
                for it in inline.get("content", []):
                    s += BlogCreate._extract_text_from_inline(it)
                return s.strip()
            # unknown inline shape -> attempt to stringify
            return str(inline.get("text") or "")
        # If it's a Pydantic model (BaseModel)
        try:
            # many of our inline models implement .text or .content
            if hasattr(inline, "text"):
                return (getattr(inline, "text") or "").strip()
            if hasattr(inline, "content"):
                # content might be a list of StyledText
                s = ""
                for it in getattr(inline, "content") or []:
                    s += BlogCreate._extract_text_from_inline(it)
                return s.strip()
        except Exception:
            pass
        # Fallback
        return str(inline)

    @staticmethod
    def _generate_excerpt_from_parsed(parsed_blocks: List[BaseBlock]) -> str:
        """
        Walk parsed_blocks (list of BaseBlock models) and return first reasonable text:
         - prefer paragraph blocks, then headings, then text nested within other blocks.
        """
        MAX_EXCERPT_LENGTH = 150
        if not parsed_blocks:
            return "No introductory text available for excerpt generation."
        # parsed_blocks might be a list-of-pages (if pages provided), so flatten if needed
        flat_blocks: List[BaseBlock] = []
        # If first element is a list (multi-page), flatten by pages' first page only for excerpt
        if parsed_blocks and isinstance(parsed_blocks[0], list):
            # take first page's blocks
            flat_blocks = parsed_blocks[0]
        else:
            flat_blocks = parsed_blocks

        for block in flat_blocks:
            try:
                btype = getattr(block, "type", None)
                if btype in ("paragraph", "heading"):
                    content = getattr(block, "content", None)
                    # content can be string or list of inline content
                    if isinstance(content, str):
                        text = content.strip()
                    elif isinstance(content, list):
                        # content is list of inline items: join their text
                        text = "".join(BlogCreate._extract_text_from_inline(it) for it in content).strip()
                    else:
                        # unknown content shape -> skip
                        text = ""
                    if text:
                        return (text[:MAX_EXCERPT_LENGTH].rstrip() + "...") if len(text) > MAX_EXCERPT_LENGTH else text
                # If block contains nested children, try them recursively
                if getattr(block, "children", None):
                    # children are parsed BaseBlock instances
                    for child in block.children:
                        # recursive attempt
                        candidate = BlogCreate._generate_excerpt_from_parsed([child])
                        if candidate and candidate != "No introductory text available for excerpt generation.":
                            return candidate
            except Exception:
                continue
        return "No introductory text available for excerpt generation."

    @model_validator(mode="after")
    def set_defaults(self) -> "BlogCreate":
        """Auto-generate slug and excerpt if they were not provided."""
        # 1. Generate Slug if missing
        if not self.slug and self.title:
            self.slug = self._generate_slug(self.title)
        elif not self.slug:
            self.slug = "invalid-slug"

        # 2. Generate Excerpt if missing and parsed exists
        if not self.excerpt and self.parsed:
            self.excerpt = self._generate_excerpt_from_parsed(self.parsed)
        elif not self.excerpt:
            self.excerpt = "Article content is currently empty."

        return self


class BlogUpdate(BaseModel):
    """Schema for updating an existing Blog entry (partial update via PATCH)."""
    state: Optional[BlogStatus] = BlogStatus.draft
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
    # parsed will be set if currentPageBody present
    parsed: Optional[List[BaseBlock]] = None

    @staticmethod
    def _generate_excerpt_from_parsed(parsed_blocks: List[BaseBlock]) -> str:
        # reuse logic from BlogCreate (mirror)
        return BlogCreate._generate_excerpt_from_parsed(parsed_blocks)

    @model_validator(mode="after")
    def set_defaults(self) -> "BlogUpdate":
        """Auto-generate excerpt if missing and set publishDate when publishing."""
        # If currentPageBody present, parse it now
        

        if not self.excerpt and self.parsed:
            self.excerpt = self._generate_excerpt_from_parsed(self.parsed)

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
    date_created: Optional[int] = None
    last_updated: Optional[int] = None
    slug: Optional[str] = None
    parsed: Optional[Any] = None
    excerpt: Optional[str] = None

    @model_validator(mode="before")
    @classmethod
    def convert_objectid(cls, values: Dict[str, Any]) -> Dict[str, Any]:
        # coerce ObjectId to str for _id if needed
        if "_id" in values and isinstance(values["_id"], ObjectId):
            values["_id"] = str(values["_id"])
        return values

    class Config:
        populate_by_name = True  # allows using `id` when constructing the model
        arbitrary_types_allowed = True
        json_encoders = {
            ObjectId: str
        }



class BlogOut(BlogBase):
    """Output schema for a Blog entry, including MongoDB ID and timestamps."""
    id: str = Field(default=None, alias="_id")
    state: Optional[BlogStatus] = BlogStatus.draft
    date_created: Optional[int] = None
    last_updated: Optional[int] = None
    slug: Optional[str] = None
    parsed: Optional[Any] = None
    excerpt: Optional[str] = None

    @model_validator(mode="before")
    @classmethod
    def convert_objectid(cls, values: Dict[str, Any]) -> Dict[str, Any]:
        # coerce ObjectId to str for _id if needed
        if "_id" in values and isinstance(values["_id"], ObjectId):
            values["_id"] = str(values["_id"])
        return values

    class Config:
        populate_by_name = True  # allows using `id` when constructing the model
        arbitrary_types_allowed = True
        json_encoders = {
            ObjectId: str
        }
