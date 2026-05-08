import os

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from .config import settings
from .db import SessionLocal, init_db
from .seed import seed_default_preferences
from .routes import pages, items, outfits, gaps_api, preferences


def create_app() -> FastAPI:
    app = FastAPI(title="Seam Wardrobe", docs_url="/api/docs")

    init_db()
    db = SessionLocal()
    try:
        seed_default_preferences(db)
    finally:
        db.close()

    os.makedirs(settings.upload_dir, exist_ok=True)
    os.makedirs("app/static", exist_ok=True)
    app.mount("/static", StaticFiles(directory="app/static"), name="static")
    app.mount("/uploads", StaticFiles(directory=settings.upload_dir), name="uploads")

    app.include_router(pages.router)
    app.include_router(items.router)
    app.include_router(outfits.router)
    app.include_router(gaps_api.router)
    app.include_router(preferences.router)

    return app


app = create_app()
