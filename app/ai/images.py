"""Shared helpers for turning images into data URLs for the vision API."""

import base64
import mimetypes
from pathlib import Path


def image_path_to_data_url(image_path: str) -> str:
    p = Path(image_path)
    mime, _ = mimetypes.guess_type(p.name)
    mime = mime or "image/jpeg"
    data = base64.b64encode(p.read_bytes()).decode("ascii")
    return f"data:{mime};base64,{data}"


def bytes_to_data_url(raw: bytes, mime: str = "image/jpeg") -> str:
    data = base64.b64encode(raw).decode("ascii")
    return f"data:{mime or 'image/jpeg'};base64,{data}"
