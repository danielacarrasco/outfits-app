"""Outfit suggestions from existing wardrobe items + user preferences."""

from typing import List, Optional

from ..config import settings
from ..schemas import PlannerResponse, PlanRequest
from .client import require_client


SYSTEM_PROMPT = (
    "You are a personal stylist for a polished, creative Melbourne wearer. "
    "You build outfits ONLY from items in the supplied wardrobe inventory "
    "(by id). Every outfit must be wearable, layered for variable weather "
    "where requested, and aligned with the user's preferences. "
    "Never invent items. Never recommend items not in the inventory. "
    "Return JSON matching the schema."
)


def _inventory_payload(items) -> list:
    return [
        {
            "id": i.id,
            "name": i.name,
            "category": i.category,
            "subcategory": i.subcategory,
            "colour_family": i.colour_family,
            "fabric": i.fabric_guess,
            "silhouette": i.silhouette,
            "formality_level": i.formality_level,
            "warmth_level": i.warmth_level,
            "season": i.season,
            "work_appropriate": i.work_appropriate,
            "notes": i.notes,
        }
        for i in items
    ]


def _preferences_payload(pref) -> dict:
    if not pref:
        return {}
    return {
        "preferred_colours": pref.preferred_colours,
        "avoided_colours": pref.avoided_colours,
        "preferred_silhouettes": pref.preferred_silhouettes,
        "avoided_silhouettes": pref.avoided_silhouettes,
        "preferred_fabrics": pref.preferred_fabrics,
        "avoided_fabrics": pref.avoided_fabrics,
        "style_keywords": pref.style_keywords,
        "work_constraints": pref.work_constraints,
        "climate_constraints": pref.climate_constraints,
        "allergy_constraints": pref.allergy_constraints,
        "notes": pref.notes,
    }


def suggest_outfits(
    request: PlanRequest,
    items: List,
    preferences,
    profile_summary: Optional[dict] = None,
) -> PlannerResponse:
    client = require_client()

    user_message = {
        "request": request.model_dump(),
        "preferences": _preferences_payload(preferences),
        "style_profile": profile_summary or {},
        "wardrobe_inventory": _inventory_payload(items),
        "instructions": (
            "Suggest 3 to 7 outfits for the requested occasion/weather/mood. "
            "Reference items only by their id from the inventory. "
            "If the request includes must_include_item_id, every outfit must include that id."
        ),
    }

    response = client.responses.parse(
        model=settings.openai_text_model,
        input=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": str(user_message)},
        ],
        text_format=PlannerResponse,
    )
    parsed = response.output_parsed
    if parsed is None:
        raise RuntimeError("OpenAI returned no parsed outfit plan.")

    valid_ids = {i.id for i in items}
    for outfit in parsed.outfits:
        outfit.item_ids = [iid for iid in outfit.item_ids if iid in valid_ids]
    parsed.outfits = [o for o in parsed.outfits if o.item_ids]
    return parsed
