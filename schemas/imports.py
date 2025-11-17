from bson import ObjectId
from pydantic import GetJsonSchemaHandler
from pydantic import BaseModel, EmailStr, Field,model_validator
from pydantic_core import core_schema
from datetime import datetime,timezone
from typing import Annotated, Dict, Optional,List,Any
from enum import Enum
import time
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
    name: CategoryNameEnum
    slug: CategorySlugEnum

    @model_validator(mode="after")
    def validate_pair(self):
        if CATEGORY_PAIRS[self.name] != self.slug:
            raise ValueError(f"Category '{self.name}' must use slug '{CATEGORY_PAIRS[self.name]}'")
        return self
    
    

    
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

    
# --- Content Block Schemas (Polymorphic Body) ---
# These are used to represent the different 'type' of objects found in currentPageBody.

# --- API'S INLINE CONTENT TYPE ---
# This new model stores rich text (bold, italic, etc.)
# It matches the `APIInlineContent` type in translator.ts
class APIInlineContent(BaseModel):
    """A single piece of inline text with styling."""
    type: Literal["text"] = "text"
    text: str
    styles: Dict[str, bool] = Field(default_factory=dict)


# --- BASE BLOCK ---
# A new base model to add the optional `align` property to all blocks.
class BaseBlock(BaseModel):
    """Base model for blocks that support alignment."""
    align: Optional[Literal["left", "center", "right"]] = None


# --- NEW BLOCK DEFINITIONS ---

class ParagraphBlock(BaseBlock):
    """
    A standard block of text. Replaces the old `TextBlock`.
    Uses `APIInlineContent` to support rich text.
    """
    type: Literal["paragraph"]
    content: List[APIInlineContent]


class HeadingBlock(BaseBlock):
    """A new block for headings (H1, H2, H3)."""
    type: Literal["heading"]
    level: Literal[1, 2, 3]
    content: List[APIInlineContent]


class ImageBlock(BaseModel):
    """
    An updated block for an image.
    Now includes `previewWidth` and `previewHeight` to prevent crashes.
    """
    type: Literal["image"]
    url: str
    altText: str
    caption: Optional[str] = None
    previewWidth: Optional[float] = Field(None, description="Image preview width")
    previewHeight: Optional[float] = Field(None, description="Image preview height")


class QuoteBlock(BaseBlock):
    """
    An updated block for a pull quote.
    Now uses `APIInlineContent` to support rich text within the quote.
    """
    type: Literal["quote"]
    content: List[APIInlineContent]


class DividerBlock(BaseModel):
    """
    A simple horizontal rule divider.
    This does *not* include alignment, matching the translator's logic.
    """
    type: Literal["divider"]


# --- FINAL UNION OF ALL BLOCKS ---
# We use Annotated[...] with a discriminator to tell Pydantic
# how to parse the union based on the "type" field.

BodyBlock = Annotated[
    Union[
        ParagraphBlock,
        HeadingBlock,
        ImageBlock,
        QuoteBlock,
        DividerBlock,
    ],
    Field(discriminator="type"),
]
class Page(BaseModel):
    pageNumber:int
    pageBody:BodyBlock