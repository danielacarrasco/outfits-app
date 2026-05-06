from datetime import datetime
from typing import List, Optional, Literal
from pydantic import BaseModel, Field, ConfigDict


Category = Literal[
    "top", "bottom", "dress", "outerwear", "footwear",
    "bag", "accessory", "fabric", "pattern", "other",
]
Season = Literal["summer", "winter", "transeasonal", "all-season"]
Occasion = Literal["work", "casual work", "weekend", "drinks", "brunch", "show", "travel"]
Weather = Literal["warm", "cold", "variable", "rainy"]


class GarmentClassification(BaseModel):
    """Schema enforced on the OpenAI vision response."""
    name: str = Field(..., description="Short descriptive name, e.g. 'Cropped olive blazer'.")
    category: Category
    subcategory: str
    colour_family: str
    exact_colours: List[str]
    fabric_guess: Literal[
        "cotton", "viscose", "silk", "acetate", "wool",
        "polyester", "leather", "denim", "knit", "crepe",
        "satin", "tweed", "linen", "unknown",
    ]
    fabric_texture: str
    silhouette: str
    warmth_level: int = Field(..., ge=1, le=5)
    formality_level: int = Field(..., ge=1, le=5)
    work_appropriate: bool
    weekend_appropriate: bool
    season: Season
    notes: str
    ai_confidence_score: float = Field(..., ge=0, le=1)


class WardrobeItemOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
    image_path: str
    category: str
    subcategory: str
    colour_family: str
    exact_colours: list
    fabric_guess: str
    fabric_texture: str
    silhouette: str
    warmth_level: int
    formality_level: int
    work_appropriate: bool
    weekend_appropriate: bool
    season: str
    notes: str
    ai_confidence_score: float
    created_at: datetime
    updated_at: datetime


class WardrobeItemUpdate(BaseModel):
    name: Optional[str] = None
    category: Optional[Category] = None
    subcategory: Optional[str] = None
    colour_family: Optional[str] = None
    exact_colours: Optional[List[str]] = None
    fabric_guess: Optional[str] = None
    fabric_texture: Optional[str] = None
    silhouette: Optional[str] = None
    warmth_level: Optional[int] = None
    formality_level: Optional[int] = None
    work_appropriate: Optional[bool] = None
    weekend_appropriate: Optional[bool] = None
    season: Optional[Season] = None
    notes: Optional[str] = None


# ---------- Outfit planner ----------

class PlannerOutfit(BaseModel):
    name: str
    item_ids: List[int]
    occasion: str
    why_it_works: str
    styling_notes: str
    layering_notes: str
    confidence_score: float = Field(..., ge=0, le=1)
    missing_optional_upgrade: str = ""


class PlannerResponse(BaseModel):
    outfits: List[PlannerOutfit]


class PlanRequest(BaseModel):
    occasion: Occasion = "work"
    weather: Weather = "variable"
    formality: int = Field(3, ge=1, le=5)
    mood: str = ""
    must_include_item_id: Optional[int] = None


# ---------- Gap analysis ----------

class GapItem(BaseModel):
    piece: str
    why_it_unlocks_outfits: str
    recommended_colour: str
    recommended_fabric: str
    recommended_silhouette: str
    pairs_with_existing: List[str]
    priority: Literal["high", "medium", "low"]
    kind: Literal["foundation", "statement", "duplicate", "nice-to-have"]
    search_keywords: List[str]


class GapResponse(BaseModel):
    gaps: List[GapItem]
    summary: str


# ---------- Style profile ----------

class StyleProfileSummary(BaseModel):
    favourite_colours: List[str]
    most_worn_categories: List[str]
    low_use_categories: List[str]
    successful_outfit_formulas: List[str]
    disliked_silhouettes: List[str]
    successful_colour_combinations: List[str]
    gaps_by_occasion: List[str]
    notes: str
