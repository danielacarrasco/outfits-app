from typing import List

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from .. import models
from ..db import get_db
from ..schemas import GapItem
from ..ai.gaps import analyse_gaps, refine_gap, verdict_on_gaps
from ..ai.client import AIUnavailable


router = APIRouter(prefix="/api/gaps", tags=["gaps"])


class GapRequest(BaseModel):
    brief: str = ""


class RefineRequest(BaseModel):
    piece: GapItem
    message: str
    brief: str = ""


class VerdictRequest(BaseModel):
    pieces: List[GapItem]
    brief: str = ""


@router.post("/analyse")
def run_gap_analysis(payload: GapRequest = GapRequest(), db: Session = Depends(get_db)):
    items = db.query(models.WardrobeItem).all()
    if not items:
        raise HTTPException(400, "Add wardrobe items first.")
    pref = db.query(models.UserPreference).first()
    feedback = db.query(models.OutfitFeedback).all()
    try:
        result = analyse_gaps(items, pref, feedback, brief=payload.brief)
    except AIUnavailable as e:
        raise HTTPException(503, str(e))
    return result.model_dump()


@router.post("/refine")
def refine_gap_endpoint(payload: RefineRequest, db: Session = Depends(get_db)):
    if not payload.message.strip():
        raise HTTPException(400, "Describe what you'd like to change.")
    items = db.query(models.WardrobeItem).all()
    pref = db.query(models.UserPreference).first()
    try:
        revised = refine_gap(payload.piece.model_dump(), payload.message, items, pref, brief=payload.brief)
    except AIUnavailable as e:
        raise HTTPException(503, str(e))
    return revised.model_dump()


@router.post("/verdict")
def verdict_endpoint(payload: VerdictRequest, db: Session = Depends(get_db)):
    if not payload.pieces:
        raise HTTPException(400, "No recommendations to assess.")
    items = db.query(models.WardrobeItem).all()
    pref = db.query(models.UserPreference).first()
    try:
        verdict = verdict_on_gaps([p.model_dump() for p in payload.pieces], items, pref, brief=payload.brief)
    except AIUnavailable as e:
        raise HTTPException(503, str(e))
    return verdict.model_dump()
