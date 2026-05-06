from sqlalchemy.orm import Session

from . import models


DEFAULT_PREFERENCES = dict(
    preferred_colours=[
        "olive", "brown", "cream", "rust", "terracotta",
        "chocolate", "navy", "hot pink (accent)",
    ],
    avoided_colours=["delicate bridal white", "neon yellow"],
    preferred_silhouettes=[
        "waist-defined", "cropped boxy", "structured shoulder",
        "wide-leg trouser", "bias skirt",
    ],
    avoided_silhouettes=["overly boxy long layers", "frilly", "boho"],
    preferred_fabrics=["cotton", "viscose", "silk", "denim", "leather"],
    avoided_fabrics=["wool against skin", "sweaty synthetic"],
    style_keywords=[
        "structured", "modern", "polished", "creative",
        "slightly architectural", "editorial",
    ],
    work_constraints="Polished but not provocative; not too corporate, not too casual.",
    climate_constraints="Melbourne — needs office layering for variable temps.",
    allergy_constraints="Cannot tolerate wool against skin (coats are fine).",
    notes=(
        "Likes shoulder pads and shoulder structure. "
        "Hot pink as a confident accent. "
        "Avoid overly delicate or bridal-looking white."
    ),
)


def seed_default_preferences(db: Session) -> models.UserPreference:
    pref = db.query(models.UserPreference).first()
    if pref:
        return pref
    pref = models.UserPreference(**DEFAULT_PREFERENCES)
    db.add(pref)
    db.commit()
    db.refresh(pref)
    return pref
