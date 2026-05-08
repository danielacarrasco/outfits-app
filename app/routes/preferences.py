from fastapi import APIRouter, Depends, Form, HTTPException
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from .. import models
from ..db import get_db


router = APIRouter(prefix="/api/preferences", tags=["preferences"])


def _csv_to_list(s: str) -> list[str]:
    return [x.strip() for x in (s or "").split(",") if x.strip()]


@router.post("/update")
def update_prefs(
    db: Session = Depends(get_db),
    preferred_colours: str = Form(""),
    avoided_colours: str = Form(""),
    preferred_silhouettes: str = Form(""),
    avoided_silhouettes: str = Form(""),
    preferred_fabrics: str = Form(""),
    avoided_fabrics: str = Form(""),
    style_keywords: str = Form(""),
    work_constraints: str = Form(""),
    climate_constraints: str = Form(""),
    allergy_constraints: str = Form(""),
    notes: str = Form(""),
):
    pref = db.query(models.UserPreference).first()
    if not pref:
        raise HTTPException(404, "No preferences row to update.")
    pref.preferred_colours = _csv_to_list(preferred_colours)
    pref.avoided_colours = _csv_to_list(avoided_colours)
    pref.preferred_silhouettes = _csv_to_list(preferred_silhouettes)
    pref.avoided_silhouettes = _csv_to_list(avoided_silhouettes)
    pref.preferred_fabrics = _csv_to_list(preferred_fabrics)
    pref.avoided_fabrics = _csv_to_list(avoided_fabrics)
    pref.style_keywords = _csv_to_list(style_keywords)
    pref.work_constraints = work_constraints
    pref.climate_constraints = climate_constraints
    pref.allergy_constraints = allergy_constraints
    pref.notes = notes
    db.commit()
    return RedirectResponse(url="/preferences", status_code=303)
