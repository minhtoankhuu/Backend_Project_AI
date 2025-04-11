from sqlalchemy import Column, Integer, String, Float, DateTime
from sqlalchemy.sql import func
from .database import Base

class Detection(Base):
    __tablename__ = "detections"

    id = Column(Integer, primary_key=True, index=True)
    camera_id = Column(Integer)
    label = Column(String(50))
    confidence = Column(Float)
    timestamp = Column(DateTime, default=func.now())
    image_path = Column(String(255))

class Alert(Base):
    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True, index=True)
    camera_id = Column(Integer)
    message = Column(String(255))
    timestamp = Column(DateTime, default=func.now())

class SavedImage(Base):
    __tablename__ = "saved_images"

    id = Column(Integer, primary_key=True, index=True)
    camera_id = Column(Integer)
    label = Column(String(50))
    image_path = Column(String(255))
    saved_at = Column(DateTime, default=func.now())
