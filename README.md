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

## Deploy to Render

The repo ships with a `render.yaml` Blueprint that provisions a Starter
web service plus a 1 GB persistent disk so SQLite and uploaded images
survive restarts and redeploys.

> Cost: roughly USD ~$8/month (Starter web $7 + 1 GB disk $1). The free
> web tier doesn't support disks; if you'd rather use it, see the
> ephemeral note below.

### One-time setup

1. Push this repo to GitHub (already done if you're reading this in the
   GitHub UI).
2. Sign in to [Render](https://render.com) and click **New +** →
   **Blueprint**.
3. Connect the GitHub repo. Render reads `render.yaml` and shows the
   service it will create. Click **Apply**.
4. When prompted, paste your `OPENAI_API_KEY` (the `sync: false` flag
   keeps it out of the repo). All other env vars come from the Blueprint.
5. Wait for the first build to finish. Render gives you a URL like
   `https://seam-wardrobe.onrender.com`.

### Deploys after that

`autoDeploy: true` is set, so any push to `main` triggers a redeploy.
Schema migrations run automatically because `init_db()` calls
`create_all()` on startup. For destructive schema changes you'd want a
proper migration tool (Alembic) — out of scope for the MVP.

### Local development still works

`.env` is read first; if `DATABASE_URL` and `UPLOAD_DIR` aren't set, the
app falls back to `./data/seam.db` and `./uploads/`.

### Free-tier alternative (ephemeral)

If you don't want to pay for a disk, drop the `disk:` block and the two
env vars that point at `/var/data` from `render.yaml`, switch
`plan: starter` to `plan: free`, and accept that your DB and uploads
reset on every redeploy. Only useful for kicking the tyres.
