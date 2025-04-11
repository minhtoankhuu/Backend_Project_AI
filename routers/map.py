# routers/map.py
from fastapi import APIRouter
from fastapi.responses import JSONResponse
import base64
from pathlib import Path

router = APIRouter()

@router.get("/map")
def get_map_image():
    map_path = Path("static/map/2d_map.png")
    if not map_path.exists():
        map_path = Path("static/map/no_video.png")

    try:
        with open(map_path, "rb") as f:
            image_data = base64.b64encode(f.read()).decode("utf-8")
        return JSONResponse(content={"image": image_data})
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)
