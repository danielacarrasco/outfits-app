"""Wardrobe gap analysis + interactive refinement."""

from typing import List, Optional

from ..config import settings
from ..schemas import GapItem, GapResponse, GapVerdict
from .client import require_client


SYSTEM_PROMPT = (
    "You are a wardrobe strategist. Analyse the user's existing wardrobe, "
    "their outfit feedback history, and their preferences. Identify ONLY "
    "high-impact gaps — pieces that would unlock multiple new outfits or "
    "fix repeated frustrations. Distinguish foundation pieces, statement "
    "pieces, duplicates, and nice-to-haves. Do not recommend random "
    "shopping. Return at most 5 recommendations as JSON matching the schema. "
    "If the user provides a brief describing what they're after, treat it as "
    "the priority lens: weight recommendations toward what they asked for "
    "while staying honest about what genuinely improves the wardrobe."
)

REFINE_PROMPT = (
    "You are revising a SINGLE wardrobe gap recommendation in response to the "
    "user's request. Keep it high-impact and aligned with their preferences "
    "and existing wardrobe. Honour the request (e.g. a different fabric, "
    "colour, silhouette, price sensibility, or a completely different piece) "
    "while still recommending something that genuinely improves the wardrobe. "
    "Return exactly one revised recommendation as JSON matching the schema."
)

VERDICT_PROMPT = (
    "You are assessing a FINAL set of recommended wardrobe additions as a "
    "whole. Judge whether, together, they form a coherent, high-impact "
    "strategy for this wearer. Flag any redundancy or overlap, suggest the "
    "best order to acquire them, and give an honest overall verdict. Return "
    "JSON matching the schema."
)


def _inventory(items: List) -> list:
    return [
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


def _prefs(preferences) -> dict:
    if not preferences:
        return {}
    return {
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


def analyse_gaps(
    items: List,
    preferences,
    feedback_rows: List,
    brief: Optional[str] = None,
) -> GapResponse:
    client = require_client()
    payload = {
        "wardrobe_inventory": _inventory(items),
        "feedback": [
            {"outfit_id": f.outfit_id, "tag": f.tag, "note": f.note}
            for f in feedback_rows
        ],
        "preferences": _prefs(preferences),
        "user_brief": (brief or "").strip(),
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


def refine_gap(
    piece: dict,
    message: str,
    items: List,
    preferences,
    brief: Optional[str] = None,
) -> GapItem:
    client = require_client()
    payload = {
        "current_recommendation": piece,
        "user_request": (message or "").strip(),
        "wardrobe_inventory": _inventory(items),
        "preferences": _prefs(preferences),
        "user_brief": (brief or "").strip(),
    }
    response = client.responses.parse(
        model=settings.openai_text_model,
        input=[
            {"role": "system", "content": REFINE_PROMPT},
            {"role": "user", "content": str(payload)},
        ],
        text_format=GapItem,
    )
    parsed = response.output_parsed
    if parsed is None:
        raise RuntimeError("OpenAI returned no parsed refined recommendation.")
    return parsed


def verdict_on_gaps(
    pieces: List[dict],
    items: List,
    preferences,
    brief: Optional[str] = None,
) -> GapVerdict:
    client = require_client()
    payload = {
        "final_recommendations": pieces,
        "wardrobe_inventory": _inventory(items),
        "preferences": _prefs(preferences),
        "user_brief": (brief or "").strip(),
    }
    response = client.responses.parse(
        model=settings.openai_text_model,
        input=[
            {"role": "system", "content": VERDICT_PROMPT},
            {"role": "user", "content": str(payload)},
        ],
        text_format=GapVerdict,
    )
    parsed = response.output_parsed
    if parsed is None:
        raise RuntimeError("OpenAI returned no parsed verdict.")
    return parsed
