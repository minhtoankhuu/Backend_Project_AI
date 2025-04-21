from fastapi import APIRouter
from db.database import SessionLocal
from db import models
import os
import logging

# Cấu hình logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter()

@router.get("/violations")
def get_saved_images(camera_id: int = None):
    logger.info(f"Fetching saved images. Camera ID: {camera_id}")
    db = SessionLocal()
    query = db.query(models.SavedImage).order_by(models.SavedImage.saved_at.desc())
    if camera_id:
        query = query.filter(models.SavedImage.camera_id == camera_id)
    images = query.all()
    db.close()

    logger.info(f"Fetched {len(images)} images for Camera ID: {camera_id}")
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
    logger.info("Starting cleanup of missing images.")
    db = SessionLocal()
    images = db.query(models.SavedImage).all()
    removed = 0

    for img in images:
        full_path = os.path.join("static", img.image_path)
        if not os.path.exists(full_path):
            logger.warning(f"Image not found: {full_path}. Deleting record ID: {img.id}")
            db.delete(img)
            removed += 1

    db.commit()
    db.close()
    logger.info(f"Cleanup completed. Total removed: {removed}")
    return {"status": "done", "removed": removed}