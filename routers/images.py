from fastapi import APIRouter
from db.database import SessionLocal
from db import models
import os
router = APIRouter()

@router.get("/violations")
def get_saved_images(camera_id: int = None):
    db = SessionLocal()
    query = db.query(models.SavedImage).order_by(models.SavedImage.saved_at.desc())
    if camera_id:
        query = query.filter(models.SavedImage.camera_id == camera_id)
    images = query.all()
    db.close()

    return [
        {
            "id": img.id,
            "camera_id": img.camera_id,
            "image_path": img.image_path,
            "label": img.label,
            "saved_at": img.saved_at.isoformat(),
        } for img in images
    ]
@router.post("/cleanup")
def cleanup_missing_images():
    """
    Xóa bản ghi vi phạm nếu file ảnh không còn tồn tại trong static/
    """
    db = SessionLocal()
    images = db.query(models.SavedImage).all()
    removed = 0

    for img in images:
        full_path = os.path.join("static", img.image_path)
        if not os.path.exists(full_path):
            db.delete(img)
            removed += 1

    db.commit()
    db.close()
    return {"status": "done", "removed": removed}
