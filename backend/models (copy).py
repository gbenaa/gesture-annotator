from sqlalchemy import Column, Integer, String, Text, TIMESTAMP, ForeignKey, JSON, create_engine
from sqlalchemy.orm import declarative_base, relationship, sessionmaker
from sqlalchemy.sql import func
from pgvector.sqlalchemy import Vector

import os

DATABASE_URL = os.environ.get("DATABASE_URL")
engine = create_engine(DATABASE_URL, echo=True)  # echo=True for debug; set False in prod

SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()

# ==============================
class Image(Base):
    __tablename__ = "images"

    id = Column(Integer, primary_key=True)
    filename = Column(Text, nullable=False)
    source = Column(Text)
    location = Column(Text)
    upload_timestamp = Column(TIMESTAMP, server_default=func.now())

    gesture_instances = relationship("GestureInstance", back_populates="image", cascade="all, delete-orphan")

# ==============================
class Gesture(Base):
    __tablename__ = "gestures"

    id = Column(Integer, primary_key=True)
    name = Column(Text, unique=True, nullable=False)
    description = Column(Text)

    gesture_instances = relationship("GestureInstance", back_populates="gesture")
    classification_systems = relationship(
        "ClassificationSystemGesture", back_populates="gesture", cascade="all, delete-orphan"
    )

# ==============================
class ClassificationSystem(Base):
    __tablename__ = "classification_systems"

    id = Column(Integer, primary_key=True)
    name = Column(Text, unique=True, nullable=False)
    description = Column(Text)

    gestures = relationship(
        "ClassificationSystemGesture", back_populates="classification_system", cascade="all, delete-orphan"
    )

# ==============================
class ClassificationSystemGesture(Base):
    __tablename__ = "classification_system_gestures"

    id = Column(Integer, primary_key=True)
    classification_system_id = Column(Integer, ForeignKey("classification_systems.id", ondelete="CASCADE"))
    gesture_id = Column(Integer, ForeignKey("gestures.id", ondelete="CASCADE"))
    label = Column(Text)

    classification_system = relationship("ClassificationSystem", back_populates="gestures")
    gesture = relationship("Gesture", back_populates="classification_systems")

# ==============================
class GestureInstance(Base):
    __tablename__ = "gesture_instances"

    id = Column(Integer, primary_key=True)
    image_id = Column(Integer, ForeignKey("images.id", ondelete="CASCADE"))
    gesture_id = Column(Integer, ForeignKey("gestures.id", ondelete="SET NULL"))
    region_coordinates = Column(JSON)
    cropped_image_path = Column(Text)
    notes = Column(Text)
    embedding = Column(Vector(768))

    image = relationship("Image", back_populates="gesture_instances")
    gesture = relationship("Gesture", back_populates="gesture_instances")
