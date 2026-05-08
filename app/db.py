import os
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker, Session

from .config import settings

# Make sure the sqlite directory exists for the default URL.
if settings.database_url.startswith("sqlite:///"):
    db_path = settings.database_url.replace("sqlite:///", "", 1)
    db_dir = os.path.dirname(db_path) or "."
    os.makedirs(db_dir, exist_ok=True)

connect_args = {"check_same_thread": False} if settings.database_url.startswith("sqlite") else {}

engine = create_engine(settings.database_url, connect_args=connect_args, future=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)


class Base(DeclarativeBase):
    pass


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    # Import models so they're registered on Base.metadata before create_all.
    from . import models  # noqa: F401
    Base.metadata.create_all(bind=engine)
    _migrate_add_missing_columns()


# Tiny forward-only schema patcher. SQLAlchemy's create_all won't add columns
# to an existing table; for an MVP without Alembic this is enough to keep
# deployed databases in sync with the model.
_REQUIRED_COLUMNS: dict[str, list[tuple[str, str]]] = {
    "wardrobe_items": [
        ("condition", "VARCHAR(20) DEFAULT 'good'"),
    ],
}


def _migrate_add_missing_columns() -> None:
    from sqlalchemy import inspect, text
    inspector = inspect(engine)
    with engine.begin() as conn:
        for table, cols in _REQUIRED_COLUMNS.items():
            if not inspector.has_table(table):
                continue
            existing = {c["name"] for c in inspector.get_columns(table)}
            for col_name, col_def in cols:
                if col_name not in existing:
                    conn.execute(text(f"ALTER TABLE {table} ADD COLUMN {col_name} {col_def}"))
