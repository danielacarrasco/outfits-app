"""Style profile summarisation. Rules-first; LLM optional for narrative summary."""

from collections import Counter
from typing import List, Optional

from sqlalchemy.orm import Session

from .. import models
from ..config import settings
from ..schemas import StyleProfileSummary
from .client import get_client


POSITIVE_TAGS = {"like", "love", "wore", "confident"}
NEGATIVE_TAGS = {
    "dislike", "too_formal", "too_casual",
    "too_boring", "too_exposed", "too_cold", "too_warm",
}


def _liked_outfit_ids(db: Session) -> set[int]:
    rows = db.query(models.OutfitFeedback).filter(
        models.OutfitFeedback.tag.in_(POSITIVE_TAGS)
    ).all()
    return {r.outfit_id for r in rows}


def _disliked_outfit_ids(db: Session) -> set[int]:
    rows = db.query(models.OutfitFeedback).filter(
        models.OutfitFeedback.tag.in_(NEGATIVE_TAGS)
    ).all()
    return {r.outfit_id for r in rows}


def compute_style_profile(db: Session) -> StyleProfileSummary:
    items = db.query(models.WardrobeItem).all()
    outfits = db.query(models.Outfit).all()
    by_id = {i.id: i for i in items}

    liked_ids = _liked_outfit_ids(db)
    disliked_ids = _disliked_outfit_ids(db)

    colour_counter: Counter = Counter()
    category_counter: Counter = Counter()
    silhouette_dislike: Counter = Counter()
    formula_counter: Counter = Counter()
    combo_counter: Counter = Counter()
    occasion_gap_counter: Counter = Counter()

    for outfit in outfits:
        item_ids = [it.id for it in outfit.items]
        for iid in item_ids:
            it = by_id.get(iid)
            if not it:
                continue
            if outfit.id in liked_ids or outfit.user_rating > 0:
                colour_counter[it.colour_family or "unknown"] += 1
                category_counter[it.category] += 1
            if outfit.id in disliked_ids or outfit.user_rating < 0:
                silhouette_dislike[it.silhouette or "unknown"] += 1

        if outfit.id in liked_ids or outfit.user_rating > 0:
            cats = sorted({by_id[i].category for i in item_ids if i in by_id})
            if cats:
                formula_counter[" + ".join(cats)] += 1
            cols = sorted({(by_id[i].colour_family or "unknown") for i in item_ids if i in by_id})
            if len(cols) >= 2:
                combo_counter[" + ".join(cols)] += 1

        if outfit.id in disliked_ids:
            occasion_gap_counter[outfit.occasion] += 1

    most_worn = [c for c, _ in category_counter.most_common(5)]
    all_categories = {i.category for i in items}
    low_use = sorted(all_categories - set(most_worn))

    return StyleProfileSummary(
        favourite_colours=[c for c, _ in colour_counter.most_common(8)],
        most_worn_categories=most_worn,
        low_use_categories=low_use,
        successful_outfit_formulas=[f for f, _ in formula_counter.most_common(5)],
        disliked_silhouettes=[s for s, _ in silhouette_dislike.most_common(5)],
        successful_colour_combinations=[c for c, _ in combo_counter.most_common(5)],
        gaps_by_occasion=[g for g, _ in occasion_gap_counter.most_common(5)],
        notes="Computed from feedback and outfit history.",
    )


def update_style_profile(db: Session) -> StyleProfileSummary:
    summary = compute_style_profile(db)
    snapshot = models.StyleProfileSnapshot(summary=summary.model_dump())
    db.add(snapshot)
    db.commit()
    return summary


def narrate_profile(summary: StyleProfileSummary) -> Optional[str]:
    """Optional: ask the LLM for a short narrative. Returns None if no API key."""
    client = get_client()
    if client is None:
        return None
    response = client.responses.create(
        model=settings.openai_text_model,
        input=[
            {
                "role": "system",
                "content": (
                    "Summarise this wardrobe owner's evolving style in 3-4 "
                    "sentences. Editorial, warm, specific. No fluff."
                ),
            },
            {"role": "user", "content": str(summary.model_dump())},
        ],
    )
    return response.output_text
