import os
import uuid
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from .. import models
from ..config import settings
from ..db import get_db
from ..schemas import GarmentClassification, WardrobeItemUpdate
from ..ai.classify import classify_item
from ..ai.client import AIUnavailable


router = APIRouter(prefix="/api/items", tags=["items"])


ALLOWED_EXTS = {".jpg", ".jpeg", ".png", ".webp", ".heic"}


def _save_upload(file: UploadFile) -> str:
    ext = Path(file.filename or "").suffix.lower()
    if ext not in ALLOWED_EXTS:
        raise HTTPException(400, f"Unsupported file type: {ext}")
    os.makedirs(settings.upload_dir, exist_ok=True)
    fname = f"{uuid.uuid4().hex}{ext}"
    dest = Path(settings.upload_dir) / fname
    with dest.open("wb") as f:
        f.write(file.file.read())
    return str(dest)


@router.post("/upload")
def upload_item(file: UploadFile = File(...), db: Session = Depends(get_db)):
    """Step 1: save image, run AI classification, return draft (not yet committed)."""
    image_path = _save_upload(file)

    ai_payload: Optional[dict] = None
    ai_error: Optional[str] = None
    try:
        result: GarmentClassification = classify_item(image_path)
        ai_payload = result.model_dump()
    except AIUnavailable as e:
        ai_error = str(e)
    except Exception as e:  # pragma: no cover - surface real API errors to UI
        ai_error = f"Classification failed: {e}"

    return {
        "image_path": image_path,
        "ai": ai_payload,
        "ai_error": ai_error,
    }


@router.post("/")
def create_item(
    db: Session = Depends(get_db),
    image_path: str = Form(...),
    name: str = Form(...),
    category: str = Form(...),
    subcategory: str = Form(""),
    colour_family: str = Form(""),
    exact_colours: str = Form(""),
    fabric_guess: str = Form("unknown"),
    fabric_texture: str = Form(""),
    silhouette: str = Form(""),
    warmth_level: int = Form(3),
    formality_level: int = Form(3),
    work_appropriate: bool = Form(False),
    weekend_appropriate: bool = Form(False),
    season: str = Form("transeasonal"),
    notes: str = Form(""),
    ai_confidence_score: float = Form(0.0),
    ai_raw: str = Form(""),
):
    """Step 2: persist the user-approved values + AI log."""
    colours = [c.strip() for c in exact_colours.split(",") if c.strip()]
    item = models.WardrobeItem(
        name=name,
        image_path=image_path,
        category=category,
        subcategory=subcategory,
        colour_family=colour_family,
        exact_colours=colours,
        fabric_guess=fabric_guess,
        fabric_texture=fabric_texture,
        silhouette=silhouette,
        warmth_level=warmth_level,
        formality_level=formality_level,
        work_appropriate=work_appropriate,
        weekend_appropriate=weekend_appropriate,
        season=season,
        notes=notes,
        ai_confidence_score=ai_confidence_score,
    )
    db.add(item)
    db.flush()

    # Audit log: store both AI guess and final values; flag if user changed them.
    import json
    raw = {}
    if ai_raw:
        try:
            raw = json.loads(ai_raw)
        except Exception:
            raw = {"_unparsed": ai_raw}
    final = {
        "name": name, "category": category, "subcategory": subcategory,
        "colour_family": colour_family, "exact_colours": colours,
        "fabric_guess": fabric_guess, "fabric_texture": fabric_texture,
        "silhouette": silhouette, "warmth_level": warmth_level,
        "formality_level": formality_level, "work_appropriate": work_appropriate,
        "weekend_appropriate": weekend_appropriate, "season": season, "notes": notes,
    }
    user_corrected = any(raw.get(k) != v for k, v in final.items() if k in raw)
    log = models.AiClassificationLog(
        item_id=item.id,
        model=settings.openai_vision_model,
        raw_response=raw,
        final_values=final,
        user_corrected=user_corrected,
    )
    db.add(log)
    db.commit()
    return RedirectResponse(url=f"/items/{item.id}", status_code=303)


@router.post("/{item_id}/update")
def update_item(item_id: int, payload: WardrobeItemUpdate, db: Session = Depends(get_db)):
    item = db.get(models.WardrobeItem, item_id)
    if not item:
        raise HTTPException(404, "Item not found")
    for k, v in payload.model_dump(exclude_unset=True).items():
        setattr(item, k, v)
    db.commit()
    return {"ok": True}


@router.post("/{item_id}/delete")
def delete_item(item_id: int, db: Session = Depends(get_db)):
    item = db.get(models.WardrobeItem, item_id)
    if not item:
        raise HTTPException(404, "Item not found")
    db.delete(item)
    db.commit()
    return RedirectResponse(url="/wardrobe", status_code=303)
