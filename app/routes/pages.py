from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import desc
from sqlalchemy.orm import Session

from .. import models
from ..db import get_db
from ..ai.profile import compute_style_profile


router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


def render(request: Request, name: str, **ctx):
    """Render with the modern Starlette signature: (request, name, context)."""
    return templates.TemplateResponse(request, name, ctx)


@router.get("/", response_class=HTMLResponse)
def home(request: Request, db: Session = Depends(get_db)):
    item_count = db.query(models.WardrobeItem).count()
    outfit_count = db.query(models.Outfit).count()
    recently_worn = (
        db.query(models.Outfit)
        .filter(models.Outfit.last_worn_at.isnot(None))
        .order_by(desc(models.Outfit.last_worn_at))
        .limit(6)
        .all()
    )
    items = db.query(models.WardrobeItem).all()
    underused = [i for i in items if not i.outfits][:6]
    return render(
        request,
        "home.html",
        item_count=item_count,
        outfit_count=outfit_count,
        recently_worn=recently_worn,
        underused=underused,
    )


@router.get("/wardrobe", response_class=HTMLResponse)
def wardrobe(
    request: Request,
    category: Optional[str] = None,
    colour: Optional[str] = None,
    fabric: Optional[str] = None,
    season: Optional[str] = None,
    work: Optional[str] = None,
    condition: Optional[str] = None,
    db: Session = Depends(get_db),
):
    q = db.query(models.WardrobeItem)
    if category:
        q = q.filter(models.WardrobeItem.category == category)
    if colour:
        q = q.filter(models.WardrobeItem.colour_family == colour)
    if fabric:
        q = q.filter(models.WardrobeItem.fabric_guess == fabric)
    if season:
        q = q.filter(models.WardrobeItem.season == season)
    if work == "yes":
        q = q.filter(models.WardrobeItem.work_appropriate.is_(True))
    if work == "weekend":
        q = q.filter(models.WardrobeItem.weekend_appropriate.is_(True))
    if condition:
        q = q.filter(models.WardrobeItem.condition == condition)
    items = q.order_by(desc(models.WardrobeItem.created_at)).all()

    all_items = db.query(models.WardrobeItem).all()
    facets = {
        "categories": sorted({i.category for i in all_items if i.category}),
        "colours": sorted({i.colour_family for i in all_items if i.colour_family}),
        "fabrics": sorted({i.fabric_guess for i in all_items if i.fabric_guess}),
        "seasons": sorted({i.season for i in all_items if i.season}),
    }
    return render(
        request,
        "wardrobe.html",
        items=items,
        facets=facets,
        active={"category": category, "colour": colour, "fabric": fabric,
                "season": season, "work": work, "condition": condition},
    )


@router.get("/items/new", response_class=HTMLResponse)
def item_new(request: Request):
    return render(request, "item_new.html")


@router.get("/items/{item_id}", response_class=HTMLResponse)
def item_detail(request: Request, item_id: int, db: Session = Depends(get_db)):
    item = db.get(models.WardrobeItem, item_id)
    if not item:
        raise HTTPException(404)
    return render(request, "item_detail.html", item=item, outfits=item.outfits)


@router.get("/planner", response_class=HTMLResponse)
def planner(request: Request, must_include: Optional[int] = None, db: Session = Depends(get_db)):
    item = db.get(models.WardrobeItem, must_include) if must_include else None
    return render(request, "planner.html", must_include_item=item)


@router.get("/outfits", response_class=HTMLResponse)
def outfits_index(
    request: Request,
    occasion: Optional[str] = None,
    rating: Optional[str] = None,
    db: Session = Depends(get_db),
):
    q = db.query(models.Outfit)
    if occasion:
        q = q.filter(models.Outfit.occasion == occasion)
    if rating == "liked":
        q = q.filter(models.Outfit.user_rating >= 1)
    elif rating == "loved":
        q = q.filter(models.Outfit.user_rating >= 2)
    elif rating == "recent":
        q = q.filter(models.Outfit.last_worn_at.isnot(None))
    outfits = q.order_by(desc(models.Outfit.created_at)).all()
    return render(
        request, "outfits.html",
        outfits=outfits,
        active={"occasion": occasion, "rating": rating},
    )


@router.get("/outfits/new", response_class=HTMLResponse)
def outfit_new(request: Request, db: Session = Depends(get_db)):
    items = db.query(models.WardrobeItem).order_by(models.WardrobeItem.category).all()
    return render(request, "outfit_new.html", items=items)


@router.get("/outfits/{outfit_id}", response_class=HTMLResponse)
def outfit_detail(request: Request, outfit_id: int, db: Session = Depends(get_db)):
    outfit = db.get(models.Outfit, outfit_id)
    if not outfit:
        raise HTTPException(404)
    return render(request, "outfit_detail.html", outfit=outfit)


@router.get("/gaps", response_class=HTMLResponse)
def gaps_page(request: Request):
    return render(request, "gaps.html")


@router.get("/preferences", response_class=HTMLResponse)
def preferences_page(request: Request, db: Session = Depends(get_db)):
    pref = db.query(models.UserPreference).first()
    profile = compute_style_profile(db)
    return render(request, "preferences.html", pref=pref, profile=profile)
