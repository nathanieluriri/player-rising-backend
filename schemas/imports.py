from __future__ import annotations
from bson import ObjectId
from pydantic import BaseModel, Field, model_validator, root_validator, validator
from pydantic_core import core_schema
from datetime import datetime,timezone
from typing import List, Optional, Union, Literal, Annotated, Dict, Any
from enum import Enum
import time
from pydantic.error_wrappers import ValidationError
import json

from typing import List, Optional, Union, Literal


# --- Nested Schemas ---

class Author(BaseModel):
    """Schema for the article author details."""
    name: str
    avatarUrl: Optional[str] = Field(None, description="URL of the author's avatar image.")
    affiliation: str
 
 

 
# --- All club names and slugs have been added here ---

class CategorySlugEnum(str, Enum):
    # Premier League (England)
    MANCHESTER_UNITED = "manchester-united"
    MANCHESTER_CITY = "manchester-city"
    ARSENAL = "arsenal"
    CHELSEA = "chelsea"
    LIVERPOOL = "liverpool"
    TOTTENHAM = "tottenham-hotspur" # Changed to be more explicit
    LEICESTER = "leicester-city"
    EVERTON = "everton-fc"
    WEST_HAM = "west-ham-united"
    NEWCASTLE = "newcastle-united"

    # La Liga (Spain)
    BARCELONA = "fc-barcelona"
    REAL_MADRID = "real-madrid"
    ATLETICO_MADRID = "atletico-madrid"
    SEVILLA = "sevilla-fc"
    VALENCIA = "valencia-cf"

    # Bundesliga (Germany)
    BAYERN_MUNICH = "bayern-munich"
    BORUSSIA_DORTMUND = "borussia-dortmund"
    RB_LEIPZIG = "rb-leipzig"
    SCHALKE = "schalke-04"

    # Serie A (Italy)
    JUVENTUS = "juventus"
    INTER_MILAN = "inter-milan"
    AC_MILAN = "ac-milan"
    NAPOLI = "napoli-fc"
    ROMA = "as-roma"

    # Ligue 1 (France)
    PSG = "paris-saint-germain"
    OLYMPIQUE_LYONNAIS = "olympique-lyonnais"
    MARSEILLE = "olympique-de-marseille"

    # Other Major European Clubs
    AJAX = "afc-ajax"
    PORTO = "fc-porto"
    BENFICA = "sl-benfica"
    CELTIC = "celtic-fc"
    RANGERS = "rangers-fc"


class CategoryNameEnum(str, Enum):
    # Premier League (England)
    MANCHESTER_UNITED = "Manchester United"
    MANCHESTER_CITY = "Manchester City"
    ARSENAL = "Arsenal"
    CHELSEA = "Chelsea"
    LIVERPOOL = "Liverpool"
    TOTTENHAM = "Tottenham Hotspur"
    LEICESTER = "Leicester City"
    EVERTON = "Everton FC"
    WEST_HAM = "West Ham United"
    NEWCASTLE = "Newcastle United"

    # La Liga (Spain)
    BARCELONA = "FC Barcelona"
    REAL_MADRID = "Real Madrid"
    ATLETICO_MADRID = "Atlético Madrid"
    SEVILLA = "Sevilla FC"
    VALENCIA = "Valencia CF"

    # Bundesliga (Germany)
    BAYERN_MUNICH = "Bayern Munich"
    BORUSSIA_DORTMUND = "Borussia Dortmund"
    RB_LEIPZIG = "RB Leipzig"
    SCHALKE = "Schalke 04"

    # Serie A (Italy)
    JUVENTUS = "Juventus"
    INTER_MILAN = "Inter Milan"
    AC_MILAN = "AC Milan"
    NAPOLI = "Napoli FC"
    ROMA = "AS Roma"

    # Ligue 1 (France)
    PSG = "Paris Saint-Germain"
    OLYMPIQUE_LYONNAIS = "Olympique Lyonnais"
    MARSEILLE = "Olympique de Marseille"

    # Other Major European Clubs
    AJAX = "AFC Ajax"
    PORTO = "FC Porto"
    BENFICA = "SL Benfica"
    CELTIC = "Celtic FC"
    RANGERS = "Rangers FC"

# --- CATEGORY_PAIRS dictionary creation ---

CATEGORY_PAIRS: Dict[CategoryNameEnum, CategorySlugEnum] = {
    # Premier League (England)
    CategoryNameEnum.MANCHESTER_UNITED: CategorySlugEnum.MANCHESTER_UNITED,
    CategoryNameEnum.MANCHESTER_CITY: CategorySlugEnum.MANCHESTER_CITY,
    CategoryNameEnum.ARSENAL: CategorySlugEnum.ARSENAL,
    CategoryNameEnum.CHELSEA: CategorySlugEnum.CHELSEA,
    CategoryNameEnum.LIVERPOOL: CategorySlugEnum.LIVERPOOL,
    CategoryNameEnum.TOTTENHAM: CategorySlugEnum.TOTTENHAM,
    CategoryNameEnum.LEICESTER: CategorySlugEnum.LEICESTER,
    CategoryNameEnum.EVERTON: CategorySlugEnum.EVERTON,
    CategoryNameEnum.WEST_HAM: CategorySlugEnum.WEST_HAM,
    CategoryNameEnum.NEWCASTLE: CategorySlugEnum.NEWCASTLE,

    # La Liga (Spain)
    CategoryNameEnum.BARCELONA: CategorySlugEnum.BARCELONA,
    CategoryNameEnum.REAL_MADRID: CategorySlugEnum.REAL_MADRID,
    CategoryNameEnum.ATLETICO_MADRID: CategorySlugEnum.ATLETICO_MADRID,
    CategoryNameEnum.SEVILLA: CategorySlugEnum.SEVILLA,
    CategoryNameEnum.VALENCIA: CategorySlugEnum.VALENCIA,

    # Bundesliga (Germany)
    CategoryNameEnum.BAYERN_MUNICH: CategorySlugEnum.BAYERN_MUNICH,
    CategoryNameEnum.BORUSSIA_DORTMUND: CategorySlugEnum.BORUSSIA_DORTMUND,
    CategoryNameEnum.RB_LEIPZIG: CategorySlugEnum.RB_LEIPZIG,
    CategoryNameEnum.SCHALKE: CategorySlugEnum.SCHALKE,

    # Serie A (Italy)
    CategoryNameEnum.JUVENTUS: CategorySlugEnum.JUVENTUS,
    CategoryNameEnum.INTER_MILAN: CategorySlugEnum.INTER_MILAN,
    CategoryNameEnum.AC_MILAN: CategorySlugEnum.AC_MILAN,
    CategoryNameEnum.NAPOLI: CategorySlugEnum.NAPOLI,
    CategoryNameEnum.ROMA: CategorySlugEnum.ROMA,

    # Ligue 1 (France)
    CategoryNameEnum.PSG: CategorySlugEnum.PSG,
    CategoryNameEnum.OLYMPIQUE_LYONNAIS: CategorySlugEnum.OLYMPIQUE_LYONNAIS,
    CategoryNameEnum.MARSEILLE: CategorySlugEnum.MARSEILLE,

    # Other Major European Clubs
    CategoryNameEnum.AJAX: CategorySlugEnum.AJAX,
    CategoryNameEnum.PORTO: CategorySlugEnum.PORTO,
    CategoryNameEnum.BENFICA: CategorySlugEnum.BENFICA,
    CategoryNameEnum.CELTIC: CategorySlugEnum.CELTIC,
    CategoryNameEnum.RANGERS: CategorySlugEnum.RANGERS,
}

class Category(BaseModel):
    itemIndex:Optional[int]=None
    name: CategoryNameEnum
    slug: CategorySlugEnum    
    @model_validator(mode="after")
    def validate_pair(self):
        if CATEGORY_PAIRS[self.name] != self.slug:
            raise ValueError(f"Category '{self.name}' must use slug '{CATEGORY_PAIRS[self.name]}'")
        return self
    
    
    
class ListOfCategories(BaseModel):
    listOfCategories:List[Category]
    totalItems:int

    
class BlogStatus(str,Enum):
    published= "published"
    draft = "draft"
    
    
class BlogType(str,Enum):
    editors_pick= "editors pick"
    featured_story = "featured story"
    hero_section="hero section"
    normal="normal"
    

class MediaAsset(BaseModel):
    """Schema for feature and inline images."""
    url: str
    altText: str = Field(..., description="A brief description of the image for accessibility.")
    credit: Optional[str] = Field(None, description="Image credit/source information.")

class Pagination(BaseModel):
    """Schema for multi-page article navigation details."""
    currentPage: int
    totalPages: int
    
 # blocknote_schema.py

# ----------------------
# Inline content models
# ----------------------
class StyledText(BaseModel):
    type: Literal["text"]
    text: str
    # BlockNote style flags are optional; keep permissive but typed
    bold: Optional[bool] = False
    italic: Optional[bool] = False
    underline: Optional[bool] = False
    strike: Optional[bool] = False
    # sometimes styles are nested in a `styles` object. We accept both shapes in normalization.
    styles: Optional[Dict[str, Any]] = None

    @root_validator(pre=True)
    def normalize_styles_shape(cls, values):
        # If incoming used `styles: { bold: true }` or top-level booleans, normalize both representations
        s = values.get("styles")
        if s is None:
            # copy top-level booleans into styles for consistency
            styles = {}
            for k in ("bold", "italic", "underline", "strike"):
                if k in values:
                    styles[k] = values.get(k)
            values["styles"] = styles if styles else None
        return values

class LinkInline(BaseModel):
    type: Literal["link"]
    content: List[StyledText]
    href: str

# If you plan to support mentions, tags, etc. add them here and to APIInlineContent union.
APIInlineContent = Annotated[
    Union[StyledText, LinkInline],
    Field(discriminator="type"),
]


# ----------------------
# Base block model
# ----------------------
class BaseBlock(BaseModel):
    id: Optional[str] = None
    type: str
    props: Optional[Dict[str, Any]] = None
    # content can be string, inline content list, or other structured content (table)
    content: Optional[Union[str, List[APIInlineContent], Dict[str, Any]]] = None
    children: Optional[List["BaseBlock"]] = None  # recursive
    align: Optional[Literal["left", "center", "right"]] = None


    model_config = {
        "extra": "allow",  # allow extra fields
        "populate_by_name": True,  # if you need snake_case -> camelCase
    }
    # Recursively ensure children parse into BaseBlock
    @validator("children", pre=True, each_item=False)
    def parse_children(cls, v):
        if v is None:
            return v
        parsed_children = []
        for c in v:
            # If it's already a BaseBlock, keep it; else try to parse dict into BaseBlock
            if isinstance(c, BaseBlock):
                parsed_children.append(c)
            elif isinstance(c, dict):
                parsed_children.append(BaseBlock.parse_obj(c))
            else:
                raise ValueError("children must be list of block dicts or BaseBlock instances")
        return parsed_children


# ----------------------
# Concrete block types
# ----------------------
class ParagraphBlock(BaseBlock):
    type: Literal["paragraph"]

class HeadingBlock(BaseBlock):
    type: Literal["heading"]
    level: Optional[int] = None  # usually 1..3

class QuoteBlock(BaseBlock):
    type: Literal["quote"]

class DividerBlock(BaseBlock):
    type: Literal["divider"]

class CodeBlock(BaseBlock):
    type: Literal["codeBlock"]

class ListItemBlock(BaseBlock):
    # bulletListItem, numberedListItem, checkListItem, toggleListItem
    type: Literal["bulletListItem", "numberedListItem", "checkListItem", "toggleListItem"]

class ListBlock(BaseBlock):
    # the top-level list container (some BlockNote variants use 'bulletList' or 'numberedList')
    type: Literal["bulletList", "numberedList", "checkList", "toggleList"]

class TableContentRow(BaseModel):
    cells: List[Union[str, List[APIInlineContent], Dict[str, Any]]]

class TableContent(BaseModel):
    type: Literal["tableContent"]
    rows: List[TableContentRow]

class TableBlock(BaseBlock):
    type: Literal["table"]
    # content usually contains the table data
    content: TableContent

class FileBlock(BaseBlock):
    type: Literal["file"]

    def url(self) -> Optional[str]:
        return (self.props or {}).get("url")

    def name(self) -> Optional[str]:
        return (self.props or {}).get("name")

class ImageBlock(BaseBlock):
    type: Literal["image"]

    def url(self) -> Optional[str]:
        return (self.props or {}).get("url")

    def caption(self) -> Optional[str]:
        return (self.props or {}).get("caption")

    def preview_width(self) -> Optional[float]:
        return (self.props or {}).get("previewWidth")

    def preview_height(self) -> Optional[float]:
        return (self.props or {}).get("previewHeight")

class VideoBlock(BaseBlock):
    type: Literal["video"]

    def url(self) -> Optional[str]:
        return (self.props or {}).get("url")

    def caption(self) -> Optional[str]:
        return (self.props or {}).get("caption")

class AudioBlock(BaseBlock):
    type: Literal["audio"]

    def url(self) -> Optional[str]:
        return (self.props or {}).get("url")

# If new block types appear, you can add them here.

# Final discriminated union for convenience (used when strict parsing needed)
BlockUnion = Annotated[
    Union[
        ParagraphBlock,
        HeadingBlock,
        QuoteBlock,
        DividerBlock,
        CodeBlock,
        ListItemBlock,
        ListBlock,
        TableBlock,
        FileBlock,
        ImageBlock,
        VideoBlock,
        AudioBlock,
        BaseBlock,  # fallback permissive block
    ],
    Field(discriminator="type"),
]


# --------------
# Parsing helpers
# --------------
def parse_block_dict(block_dict: Dict[str, Any]) -> BaseBlock:
    """
    Parse a raw block dict coming from BlockNote into a typed Pydantic model.
    Uses the discriminated union when possible, otherwise falls back to BaseBlock.
    """
    # First try to map using BlockUnion (discriminated by type)
    try:
        m = BlockUnion.parse_obj(block_dict)
        # Ensure children are recursively parsed if raw dicts
        if getattr(m, "children", None):
            m.children = [parse_block_dict(c) if isinstance(c, dict) else c for c in m.children]
        return m
    except ValidationError:
        # fallback: parse as BaseBlock (keep unknown fields)
        base = BaseBlock.parse_obj(block_dict)
        if getattr(base, "children", None):
            base.children = [parse_block_dict(c) if isinstance(c, dict) else c for c in base.children]
        return base


def parse_document(blocks_json: List[Dict[str, Any]]) -> List[BaseBlock]:
    """
    Parse an entire BlockNote document (list of block dicts) into typed models recursively.
    Raises ValidationError if something critical is malformed.
    """
    parsed: List[BaseBlock] = []
    for b in blocks_json:
        parsed.append(parse_block_dict(b))
    return parsed


# --------------------------
# Normalization utilities
# --------------------------
def _normalize_media_props(block: BaseBlock) -> Dict[str, Any]:
    """
    Bring common media fields to canonical props dict shape:
    - ensure props exists
    - if url is top-level, move into props['url']
    - copy previewWidth/Height, caption etc from both top-level and props
    Returns a normalized props dict.
    """
    props = dict(block.props or {})
    # possible top-level fields (sometimes frontend stores url/caption at top)
    if isinstance(block.content, str):
        # some blocks might misuse 'content' for url; rarely used but we normalize defensively
        if block.type in ("image", "video", "audio", "file") and block.content.startswith("http"):
            props.setdefault("url", block.content)

    for k in ("url", "caption", "previewWidth", "previewHeight", "name", "size"):
        if k in block.__dict__ and getattr(block, k, None) is not None:
            props.setdefault(k, getattr(block, k))
    # normalize url from props if present in block dict keys (sometimes top-level)
    # This ensures props has url consistently.
    return props


def normalize_block(block: BaseBlock) -> Dict[str, Any]:
    """
    Return a canonical dict for storage derived from a parsed BaseBlock.
    Includes:
      - type, id
      - props normalized
      - content normalized (inline content converted to serializable dicts)
      - recursively normalized children
    """
    out: Dict[str, Any] = {}
    out["type"] = block.type
    if block.id:
        out["id"] = block.id

    # normalize props for media blocks
    if block.type in ("image", "video", "audio", "file"):
        props = _normalize_media_props(block)
        out["props"] = props if props else None
    else:
        out["props"] = block.props or None

    # normalize content
    if isinstance(block.content, str) or block.content is None:
        out["content"] = block.content
    else:
        # content might be inline content list or structured object (tableContent)
        if isinstance(block.content, dict):
            # For table content, keep it mostly as-is but ensure inner rows/cells are canonical
            out["content"] = block.content
        else:
            # inline content list: serialize each StyledText/LinkInline to dict
            serialized = []
            for it in block.content:
                if isinstance(it, BaseModel):
                    serialized.append(it.dict(exclude_none=True))
                elif isinstance(it, dict):
                    serialized.append(it)
                else:
                    # unknown inline shape; coerce to str safe representation
                    serialized.append({"type": "text", "text": str(it)})
            out["content"] = serialized

    # children recursion
    if block.children:
        out["children"] = [normalize_block(c) for c in block.children]
    else:
        out["children"] = None

    # alignment
    if block.align:
        out["align"] = block.align

    # Any extra fields the app might want to preserve:
    # BlockNote sometimes attaches ephemeral keys: keep them under `meta` to avoid collisions.
    # (We intentionally avoid copying everything to keep stored shape minimal.)
    return {k: v for k, v in out.items() if v is not None}


def normalize_document(blocks_json: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Parse and normalize an entire document, returning a list of canonical block dicts.
    This is what you should persist to your DB.
    """
    parsed = parse_document(blocks_json)
    return [normalize_block(b) for b in parsed]


class Page(BaseModel):
    pageNumber:int
    pageBody:List[Dict[str, Any]]
    
    
class SearchQuery(BaseModel):
    title: Optional[str] = Field(None, description="Search blog titles")
    author: Optional[str] = Field(None, description="Search blog authors")
    start:Optional[int]=0
    stop:Optional[int]=100
  