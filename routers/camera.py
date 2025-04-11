import base64
from fastapi import APIRouter
from fastapi.responses import JSONResponse

router = APIRouter()

@router.get("/map")
def get_map():
    try:
        with open("static/map/2d_map.png", "rb") as f:
            encoded = base64.b64encode(f.read()).decode()
            return JSONResponse(content={"image": encoded})
    except Exception:
        with open("static/map/no_video.png", "rb") as f:
            fallback = base64.b64encode(f.read()).decode()
            return JSONResponse(content={"image": fallback})