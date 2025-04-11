from fastapi import APIRouter
from db.database import SessionLocal
from db import models

router = APIRouter()

@router.get("/violations")
def get_saved_images():
    db = SessionLocal()
    images = db.query(models.SavedImage).order_by(models.SavedImage.saved_at.desc()).all()
    db.close()

    return [
        {
            "id": img.id,
            "camera_id": img.camera_id,
            "image_path": img.image_path,
            "label": img.label,
            "saved_at": img.saved_at,
        } for img in images
    ]
