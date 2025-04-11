from fastapi import APIRouter
from yolov8.shared_state import latest_stats

router = APIRouter()

@router.get("/camera/stats")
def get_stats():
    return {
        "total": latest_stats["total"],
        "safety": latest_stats["safety"],
        "no_safety": latest_stats["no_safety"],
        "fps": latest_stats["fps"]
    }