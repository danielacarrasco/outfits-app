"""Classify a wardrobe item from an image using OpenAI vision + Structured Outputs."""

from ..config import settings
from ..schemas import GarmentClassification
from .client import require_client
from .images import image_path_to_data_url


CLASSIFY_PROMPT = (
    "Classify this wardrobe item from the image. Return only JSON matching the "
    "schema. Be conservative if uncertain. Identify garment category, "
    "subcategory, colours, fabric guess, texture, silhouette, formality, "
    "warmth, and outfit compatibility. Do not invent brand or exact fabric "
    "unless visible or supplied. Use Australian English.\n\n"
    "Also estimate the garment's condition using exactly one of these values: "
    "'new' (looks unworn, tags possibly visible), "
    "'like_new' (no visible wear), "
    "'good' (light wear, fully intact), "
    "'worn' (visible signs of wear: pilling, fading, stretching, scuffs), "
    "'tired' (clearly worn out, may need repair or replacement). "
    "If you can't tell from the photo, default to 'good'."
)


def classify_item(image_path: str) -> GarmentClassification:
    """Send the local image to OpenAI's vision model and parse a structured result."""
    client = require_client()
    data_url = image_path_to_data_url(image_path)

    # Use the Responses API with structured output parsing.
    response = client.responses.parse(
        model=settings.openai_vision_model,
        input=[
            {
                "role": "system",
                "content": (
                    "You are a meticulous wardrobe stylist tagging garments for "
                    "a personal wardrobe app. Be precise and conservative."
                ),
            },
            {
                "role": "user",
                "content": [
                    {"type": "input_text", "text": CLASSIFY_PROMPT},
                    {"type": "input_image", "image_url": data_url},
                ],
            },
        ],
        text_format=GarmentClassification,
    )
    parsed = response.output_parsed
    if parsed is None:
        raise RuntimeError("OpenAI returned no parsed classification.")
    return parsed
