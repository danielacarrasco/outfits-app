from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, Form, HTTPException
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from .. import models
from ..db import get_db
from ..schemas import PlanRequest
from ..ai.planner import suggest_outfits
from ..ai.client import AIUnavailable
from ..ai.profile import compute_style_profile


router = APIRouter(prefix="/api/outfits", tags=["outfits"])


VALID_FEEDBACK_TAGS = {
    "like", "love", "dislike", "wore",
    "confident", "too_formal", "too_casual",
    "too_boring", "too_exposed", "too_cold", "too_warm",
}


@router.post("/plan")
def plan(payload: PlanRequest, db: Session = Depends(get_db)):
    items = db.query(models.WardrobeItem).all()
    if not items:
        raise HTTPException(400, "Add at least one item to your wardrobe first.")
    pref = db.query(models.UserPreference).first()
    profile = compute_style_profile(db).model_dump()
    try:
        result = suggest_outfits(payload, items, pref, profile)
    except AIUnavailable as e:
        raise HTTPException(503, str(e))
    return result.model_dump()


@router.post("/")
def create_outfit(
    db: Session = Depends(get_db),
    name: str = Form(...),
    occasion: str = Form("work"),
    weather: str = Form("variable"),
    notes: str = Form(""),
    ai_reasoning_summary: str = Form(""),
    item_ids: List[int] = Form(default=[]),
):
    items = db.query(models.WardrobeItem).filter(models.WardrobeItem.id.in_(item_ids)).all()
    if not items:
        raise HTTPException(400, "Select at least one item.")
    outfit = models.Outfit(
        name=name,
        occasion=occasion,
        weather=weather,
        notes=notes,
        ai_reasoning_summary=ai_reasoning_summary,
        items=items,
    )
    db.add(outfit)
    db.commit()
    return RedirectResponse(url=f"/outfits/{outfit.id}", status_code=303)


@router.post("/{outfit_id}/rate")
def rate_outfit(outfit_id: int, rating: int = Form(...), db: Session = Depends(get_db)):
    outfit = db.get(models.Outfit, outfit_id)
    if not outfit:
        raise HTTPException(404)
    if rating not in (-1, 0, 1, 2):
        raise HTTPException(400, "rating must be -1, 0, 1, or 2")
    outfit.user_rating = rating
    db.commit()
    return {"ok": True, "user_rating": outfit.user_rating}


@router.post("/{outfit_id}/feedback")
def add_feedback(
    outfit_id: int,
    tag: str = Form(...),
    note: str = Form(""),
    db: Session = Depends(get_db),
):
    outfit = db.get(models.Outfit, outfit_id)
    if not outfit:
        raise HTTPException(404)
    if tag not in VALID_FEEDBACK_TAGS:
        raise HTTPException(400, f"Unknown tag: {tag}")
    fb = models.OutfitFeedback(outfit_id=outfit_id, tag=tag, note=note)
    db.add(fb)

    if tag == "wore":
        outfit.worn_count = (outfit.worn_count or 0) + 1
        outfit.last_worn_at = datetime.utcnow()
    if tag == "love":
        outfit.user_rating = max(outfit.user_rating, 2)
    elif tag == "like":
        outfit.user_rating = max(outfit.user_rating, 1)
    elif tag == "dislike":
        outfit.user_rating = -1

    db.commit()
    return {"ok": True}


@router.post("/{outfit_id}/delete")
def delete_outfit(outfit_id: int, db: Session = Depends(get_db)):
    outfit = db.get(models.Outfit, outfit_id)
    if not outfit:
        raise HTTPException(404)
    db.delete(outfit)
    db.commit()
    return RedirectResponse(url="/outfits", status_code=303)
