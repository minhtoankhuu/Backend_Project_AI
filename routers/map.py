# routers/map.py
from fastapi import APIRouter
from fastapi.responses import JSONResponse
import base64
import os
from pathlib import Path

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
    except:
        return JSONResponse(content={"error": "failed to load"}, status_code=500)
