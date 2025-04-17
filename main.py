from fastapi import FastAPI
from db import models, database
from routers import camera, images, stats
from fastapi.staticfiles import StaticFiles
from routers import ws_stream
from fastapi.middleware.cors import CORSMiddleware
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.mount("/static", StaticFiles(directory="static"), name="static")
# Tạo bảng nếu chưa có
models.Base.metadata.create_all(bind=database.engine)
# Gắn các router
app.include_router(ws_stream.router)
app.include_router(camera.router, prefix="/api/camera", tags=["Camera"])
app.include_router(images.router, prefix="/api/images", tags=["Images"])
app.include_router(stats.router, prefix="/api", tags=["Stats"])

@app.get("/")
def root():
    return {"message": "Safety Monitoring API"}