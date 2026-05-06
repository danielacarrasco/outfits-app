from datetime import datetime
from sqlalchemy import (
    Boolean, Column, DateTime, Float, ForeignKey, Integer, JSON, String, Table, Text,
)
from sqlalchemy.orm import relationship

from .db import Base


outfit_items = Table(
    "outfit_items",
    Base.metadata,
    Column("outfit_id", Integer, ForeignKey("outfits.id", ondelete="CASCADE"), primary_key=True),
    Column("item_id", Integer, ForeignKey("wardrobe_items.id", ondelete="CASCADE"), primary_key=True),
)


class WardrobeItem(Base):
    __tablename__ = "wardrobe_items"

    id = Column(Integer, primary_key=True)
    name = Column(String(200), nullable=False, default="Untitled item")
    image_path = Column(String(500), nullable=False)

    category = Column(String(40), nullable=False, default="other")
    subcategory = Column(String(80), default="")
    colour_family = Column(String(40), default="")
    exact_colours = Column(JSON, default=list)
    fabric_guess = Column(String(40), default="unknown")
    fabric_texture = Column(String(40), default="")
    silhouette = Column(String(40), default="")

    warmth_level = Column(Integer, default=3)
    formality_level = Column(Integer, default=3)
    work_appropriate = Column(Boolean, default=True)
    weekend_appropriate = Column(Boolean, default=True)
    season = Column(String(20), default="transeasonal")

    notes = Column(Text, default="")
    ai_confidence_score = Column(Float, default=0.0)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    outfits = relationship("Outfit", secondary=outfit_items, back_populates="items")


class Outfit(Base):
    __tablename__ = "outfits"

    id = Column(Integer, primary_key=True)
    name = Column(String(200), nullable=False, default="Untitled outfit")
    image_path = Column(String(500), default="")
    occasion = Column(String(40), default="work")
    weather = Column(String(40), default="variable")
    user_rating = Column(Integer, default=0)  # -1 dislike, 0 neutral, 1 like, 2 love
    worn_count = Column(Integer, default=0)
    last_worn_at = Column(DateTime, nullable=True)
    notes = Column(Text, default="")
    ai_reasoning_summary = Column(Text, default="")
    created_at = Column(DateTime, default=datetime.utcnow)

    items = relationship("WardrobeItem", secondary=outfit_items, back_populates="outfits")
    feedback = relationship("OutfitFeedback", back_populates="outfit", cascade="all, delete-orphan")


class OutfitFeedback(Base):
    __tablename__ = "outfit_feedback"

    id = Column(Integer, primary_key=True)
    outfit_id = Column(Integer, ForeignKey("outfits.id", ondelete="CASCADE"), nullable=False)
    # tag is one of: like, love, dislike, wore, confident, too_formal, too_casual,
    # too_boring, too_exposed, too_cold, too_warm
    tag = Column(String(40), nullable=False)
    note = Column(Text, default="")
    created_at = Column(DateTime, default=datetime.utcnow)

    outfit = relationship("Outfit", back_populates="feedback")


class UserPreference(Base):
    __tablename__ = "user_preferences"

    id = Column(Integer, primary_key=True)
    preferred_colours = Column(JSON, default=list)
    avoided_colours = Column(JSON, default=list)
    preferred_silhouettes = Column(JSON, default=list)
    avoided_silhouettes = Column(JSON, default=list)
    preferred_fabrics = Column(JSON, default=list)
    avoided_fabrics = Column(JSON, default=list)
    style_keywords = Column(JSON, default=list)
    work_constraints = Column(Text, default="")
    climate_constraints = Column(Text, default="")
    allergy_constraints = Column(Text, default="")
    notes = Column(Text, default="")
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class StyleProfileSnapshot(Base):
    __tablename__ = "style_profile_snapshots"

    id = Column(Integer, primary_key=True)
    summary = Column(JSON, default=dict)
    created_at = Column(DateTime, default=datetime.utcnow)


class AiClassificationLog(Base):
    __tablename__ = "ai_classification_logs"

    id = Column(Integer, primary_key=True)
    item_id = Column(Integer, ForeignKey("wardrobe_items.id", ondelete="SET NULL"), nullable=True)
    model = Column(String(80), default="")
    raw_response = Column(JSON, default=dict)
    final_values = Column(JSON, default=dict)
    user_corrected = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
