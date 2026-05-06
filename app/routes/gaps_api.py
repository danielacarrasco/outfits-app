from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from .. import models
from ..db import get_db
from ..ai.gaps import analyse_gaps
from ..ai.client import AIUnavailable


router = APIRouter(prefix="/api/gaps", tags=["gaps"])


@router.post("/analyse")
def run_gap_analysis(db: Session = Depends(get_db)):
    items = db.query(models.WardrobeItem).all()
    if not items:
        raise HTTPException(400, "Add wardrobe items first.")
    pref = db.query(models.UserPreference).first()
    feedback = db.query(models.OutfitFeedback).all()
    try:
        result = analyse_gaps(items, pref, feedback)
    except AIUnavailable as e:
        raise HTTPException(503, str(e))
    return result.model_dump()
