from sqlalchemy import Column, Integer, String, Text, TIMESTAMP, ForeignKey, JSON, create_engine
from sqlalchemy.orm import declarative_base, sessionmaker, relationship
from sqlalchemy.sql import func
from pgvector.sqlalchemy import Vector
import os

DATABASE_URL = os.environ.get("DATABASE_URL")

Base = declarative_base()

class Image(Base):
    __tablename__ = 'images'
    id = Column(Integer, primary_key=True)
    filename = Column(String, nullable=False)
    source = Column(String)
    location = Column(String)
    upload_timestamp = Column(TIMESTAMP, server_default=func.now())

    gesture_instances = relationship("GestureInstance", back_populates="image")

class Gesture(Base):
    __tablename__ = 'gestures'
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    description = Column(Text)

    gesture_instances = relationship("GestureInstance", back_populates="gesture")

class GestureInstance(Base):
    __tablename__ = 'gesture_instances'
    id = Column(Integer, primary_key=True)
    image_id = Column(Integer, ForeignKey('images.id'))
    gesture_id = Column(Integer, ForeignKey('gestures.id'), nullable=True)
    region_coordinates = Column(JSON, nullable=False)
    cropped_image_path = Column(Text)
    notes = Column(Text)

    image = relationship("Image", back_populates="gesture_instances")
    gesture = relationship("Gesture", back_populates="gesture_instances")

class ClassificationSystem(Base):
    __tablename__ = 'classification_systems'
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    description = Column(Text)

class ClassificationSystemGesture(Base):
    __tablename__ = 'classification_system_gestures'
    id = Column(Integer, primary_key=True)
    classification_system_id = Column(Integer, ForeignKey('classification_systems.id'))
    gesture_id = Column(Integer, ForeignKey('gestures.id'))
    label = Column(Text)

# Database setup
engine = create_engine(DATABASE_URL, echo=True)
SessionLocal = sessionmaker(bind=engine)
db_session = SessionLocal()
