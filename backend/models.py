"""
models.py – SQLAlchemy models for Gesture-Annotator + Icon-catalogue
-------------------------------------------------------------------
• Defines engine, SessionLocal, Base      (no global db_session)
• Includes the original gesture tables
• Includes the new icon-catalogue tables
• Supplies `get_session()` for context-managed work.
"""

from __future__ import annotations

import os
from typing import List

from sqlalchemy import (
    ARRAY,
    Column,
    ForeignKey,
    Integer,
    JSON,
    String,
    Text,
    TIMESTAMP,
    create_engine,
)
from sqlalchemy.orm import declarative_base, relationship, sessionmaker
from sqlalchemy.sql import func
from pgvector.sqlalchemy import Vector

# ------------------------------------------------------------------ #
# Engine / Session factory                                           #
# ------------------------------------------------------------------ #

DATABASE_URL = os.environ.get("DATABASE_URL")
if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL environment variable is not set.")

engine = create_engine(DATABASE_URL, echo=False, future=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)

Base = declarative_base()

# ------------------------------------------------------------------ #
# Core gesture-annotator tables                                      #
# ------------------------------------------------------------------ #


class Image(Base):
    __tablename__ = "images"

    id = Column(Integer, primary_key=True)
    filename = Column(String, nullable=False)
    source = Column(String)
    location = Column(String)
    upload_timestamp = Column(TIMESTAMP, server_default=func.now())

    gesture_instances = relationship(
        "GestureInstance", back_populates="image", cascade="all, delete-orphan"
    )


class Gesture(Base):
    __tablename__ = "gestures"

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False, unique=True)
    description = Column(Text)

    gesture_instances = relationship("GestureInstance", back_populates="gesture")


class GestureInstance(Base):
    __tablename__ = "gesture_instances"

    id = Column(Integer, primary_key=True)
    image_id = Column(Integer, ForeignKey("images.id", ondelete="CASCADE"))
    gesture_id = Column(Integer, ForeignKey("gestures.id"), nullable=True)
    region_coordinates = Column(JSON, nullable=False)
    cropped_image_path = Column(Text)
    notes = Column(Text)

    embedding = Column(Vector(768))  # optional CLIP embedding

    image = relationship("Image", back_populates="gesture_instances")
    gesture = relationship("Gesture", back_populates="gesture_instances")


# ------------------------------------------------------------------ #
# Icon-catalogue hierarchy                                           #
# ------------------------------------------------------------------ #


class IconographicType(Base):
    __tablename__ = "iconographic_types"

    id = Column(Integer, primary_key=True)
    title = Column(Text, nullable=False)
    description = Column(Text)
    feast_association = Column(Text)
    notes = Column(Text)
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())

    variants = relationship(
        "IconographicVariant",
        back_populates="iconographic_type",
        cascade="all, delete-orphan",
    )


class IconographicVariant(Base):
    __tablename__ = "iconographic_variants"

    id = Column(Integer, primary_key=True)
    iconographic_type_id = Column(
        Integer, ForeignKey("iconographic_types.id", ondelete="CASCADE")
    )
    title = Column(Text, nullable=False)
    description = Column(Text)
    regional_school = Column(Text)
    date_range = Column(Text)
    composition_notes = Column(Text)
    feast_association = Column(Text)
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())

    iconographic_type = relationship("IconographicType", back_populates="variants")
    icons = relationship(
        "Icon", back_populates="iconographic_variant", cascade="all, delete-orphan"
    )


class Icon(Base):
    __tablename__ = "icons"

    id = Column(Integer, primary_key=True)
    iconographic_variant_id = Column(
        Integer, ForeignKey("iconographic_variants.id", ondelete="CASCADE")
    )
    title = Column(Text, nullable=False)
    object_type = Column(Text, default="icon")
    museum_collection_number = Column(Text)
    culture_period = Column(Text)
    date_approx = Column(Text)
    place_of_creation = Column(Text)
    current_location = Column(Text)
    acquisition_method = Column(Text)
    acquisition_source = Column(Text)
    acquisition_date = Column(Text)
    materials = Column(ARRAY(Text))
    techniques = Column(ARRAY(Text))
    dimensions_mm = Column(Text)
    image_url = Column(Text)
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())
    condition_report = Column(Text)

    iconographic_variant = relationship("IconographicVariant", back_populates="icons")
    images = relationship(
        "IconImage", back_populates="icon", cascade="all, delete-orphan"
    )
    inscriptions = relationship(
        "IconInscription", back_populates="icon", cascade="all, delete-orphan"
    )


class IconImage(Base):
    __tablename__ = "icon_images"

    id = Column(Integer, primary_key=True)
    icon_id = Column(Integer, ForeignKey("icons.id", ondelete="CASCADE"))
    image_url = Column(Text, nullable=False)
    photographer = Column(Text)
    copyright_holder = Column(Text)
    date_taken = Column(Text)
    resolution = Column(Text)
    lighting_notes = Column(Text)
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())

    icon = relationship("Icon", back_populates="images")


class IconInscription(Base):
    __tablename__ = "icon_inscriptions"

    id = Column(Integer, primary_key=True)
    icon_id = Column(Integer, ForeignKey("icons.id", ondelete="CASCADE"))
    language = Column(Text)
    text = Column(Text)
    location_on_icon = Column(Text)
    script_type = Column(Text)
    translation = Column(Text)

    icon = relationship("Icon", back_populates="inscriptions")


# ------------------------------------------------------------------ #
# Classification system (optional)                                   #
# ------------------------------------------------------------------ #


class ClassificationSystem(Base):
    __tablename__ = "classification_systems"

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False, unique=True)
    description = Column(Text)

    gestures = relationship("ClassificationSystemGesture", back_populates="system")


class ClassificationSystemGesture(Base):
    __tablename__ = "classification_system_gestures"

    id = Column(Integer, primary_key=True)
    classification_system_id = Column(
        Integer, ForeignKey("classification_systems.id", ondelete="CASCADE")
    )
    gesture_id = Column(Integer, ForeignKey("gestures.id", ondelete="CASCADE"))
    label = Column(Text)

    system = relationship("ClassificationSystem", back_populates="gestures")
    gesture = relationship("Gesture")


# ------------------------------------------------------------------ #
# Convenience helper                                                 #
# ------------------------------------------------------------------ #


def get_session():
    """Return a new SQLAlchemy session (use with ``with get_session() as s: ...``)."""
    return SessionLocal()
