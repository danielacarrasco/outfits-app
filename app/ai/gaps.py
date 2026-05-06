"""Wardrobe gap analysis."""

from typing import List

from ..config import settings
from ..schemas import GapResponse
from .client import require_client


SYSTEM_PROMPT = (
    "You are a wardrobe strategist. Analyse the user's existing wardrobe, "
    "their outfit feedback history, and their preferences. Identify ONLY "
    "high-impact gaps — pieces that would unlock multiple new outfits or "
    "fix repeated frustrations. Distinguish foundation pieces, statement "
    "pieces, duplicates, and nice-to-haves. Do not recommend random "
    "shopping. Return at most 5 recommendations as JSON matching the schema."
)


def analyse_gaps(items: List, preferences, feedback_rows: List) -> GapResponse:
    client = require_client()

    inventory = [
        {
            "id": i.id,
            "category": i.category,
            "subcategory": i.subcategory,
            "colour_family": i.colour_family,
            "silhouette": i.silhouette,
            "fabric": i.fabric_guess,
            "season": i.season,
            "formality_level": i.formality_level,
            "warmth_level": i.warmth_level,
        }
        for i in items
    ]
    feedback = [
        {
            "outfit_id": f.outfit_id,
            "tag": f.tag,
            "note": f.note,
        }
        for f in feedback_rows
    ]
    prefs = (
        {
            "preferred_colours": preferences.preferred_colours,
            "avoided_colours": preferences.avoided_colours,
            "preferred_silhouettes": preferences.preferred_silhouettes,
            "avoided_silhouettes": preferences.avoided_silhouettes,
            "preferred_fabrics": preferences.preferred_fabrics,
            "avoided_fabrics": preferences.avoided_fabrics,
            "style_keywords": preferences.style_keywords,
            "work_constraints": preferences.work_constraints,
            "climate_constraints": preferences.climate_constraints,
            "allergy_constraints": preferences.allergy_constraints,
        }
        if preferences
        else {}
    )

    payload = {
        "wardrobe_inventory": inventory,
        "feedback": feedback,
        "preferences": prefs,
    }

    response = client.responses.parse(
        model=settings.openai_text_model,
        input=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": str(payload)},
        ],
        text_format=GapResponse,
    )
    parsed = response.output_parsed
    if parsed is None:
        raise RuntimeError("OpenAI returned no parsed gap analysis.")
    return parsed
