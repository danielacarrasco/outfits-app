from functools import lru_cache
from typing import Optional

from ..config import settings


class AIUnavailable(RuntimeError):
    """Raised when an OpenAI call cannot be made (no key, transport error, etc.)."""


@lru_cache(maxsize=1)
def get_client():
    """Return a cached OpenAI client, or None if no API key is configured."""
    if not settings.openai_api_key:
        return None
    try:
        from openai import OpenAI
        return OpenAI(api_key=settings.openai_api_key)
    except Exception:
        return None


def require_client():
    client = get_client()
    if client is None:
        raise AIUnavailable(
            "OpenAI API key is not configured. Set OPENAI_API_KEY in .env to enable AI features."
        )
    return client
