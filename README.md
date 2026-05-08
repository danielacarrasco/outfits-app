# Seam Wardrobe

A personal wardrobe planner. Upload garments, classify them with vision AI,
build outfits, get LLM-powered suggestions, and learn what you actually wear.

## Stack

- **Backend:** FastAPI + SQLAlchemy
- **Frontend:** Server-rendered Jinja templates + a sliver of vanilla JS
- **DB:** SQLite for MVP (models written so Postgres is a swap of the URL)
- **AI:** OpenAI vision + Structured Outputs (JSON Schema) for classification,
  outfit planning, gap analysis, and style-profile summarisation.

## Quickstart

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # add your OPENAI_API_KEY
bash run.sh
```

Open http://localhost:8000.

## Layout

```
app/
  main.py            FastAPI app + Jinja config
  db.py              SQLAlchemy engine/session
  models.py          ORM models
  schemas.py         Pydantic request/response models
  config.py          Settings via pydantic-settings
  seed.py            Default style preferences
  ai/
    client.py        OpenAI client factory
    classify.py      classify_item(image) -> structured JSON
    planner.py       suggest_outfits(...)
    gaps.py          analyse_gaps(...)
    profile.py       update_style_profile(...)
  routes/
    pages.py         HTML routes
    items.py         /api/items
    outfits.py       /api/outfits
    gaps_api.py      /api/gaps
    preferences.py   /api/preferences
  templates/         Jinja templates
  static/            CSS, JS, served from /static
```

## Notes

- AI never writes directly to the DB. Every classification is shown on a
  review screen for user correction; both the AI guess and final values
  are stored in `ai_classification_logs`.
- All vision/LLM responses are validated against JSON schemas (Structured
  Outputs).
- Default style preferences are seeded for a Melbourne, polished-creative,
  earthy-palette wearer; edit them in `/preferences`.
