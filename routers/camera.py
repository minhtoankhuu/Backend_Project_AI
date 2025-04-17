import base64
from fastapi import APIRouter, Query
from fastapi.responses import JSONResponse
import os

router = APIRouter()

@router.get("/map")
def get_map(cam_id: int = 1):
    path = f"static/map/2d_map_cam{cam_id}.png"

    if not os.path.exists(path):
        path = "static/map/no_video.png"

    try:
        with open(path, "rb") as f:
            encoded = base64.b64encode(f.read()).decode()
        return JSONResponse(content={"image": encoded})
    except Exception:
        return JSONResponse(content={"error": "Lỗi khi đọc ảnh"}, status_code=500)
