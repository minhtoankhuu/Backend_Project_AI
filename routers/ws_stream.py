from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from yolov8.detect import run_detection_frame, VIDEO_PATHS
from yolov8.shared_state import latest_stats

import cv2
import base64
import asyncio
import json
from pathlib import Path

router = APIRouter()

@router.websocket("/ws/stream/{cam_id}")
async def websocket_stream(websocket: WebSocket, cam_id: int):
    await websocket.accept()
    print(f"WebSocket nhận kết nối từ camera {cam_id}")

    video_path = VIDEO_PATHS.get(cam_id)
    cap = cv2.VideoCapture(video_path)
    fps = cap.get(cv2.CAP_PROP_FPS) or 25
    delay = max(1 / fps, 0.04)

 # Đường dẫn tới file bản đồ
    map_path = Path(f"static/map/2d_map_cam{cam_id}.png")
    if not map_path.exists():
        map_path = Path("static/map/no_video.png")
        
    try:
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                print("Đặt lại video về đầu...")
                cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                continue

            frame, show_warning = run_detection_frame(frame, cam_id)

            _, buffer = cv2.imencode('.jpg', frame)
            b64 = base64.b64encode(buffer).decode('utf-8')

 # Lấy dữ liệu bản đồ
            try:
                with open(map_path, "rb") as f:
                    b64_map = base64.b64encode(f.read()).decode('utf-8')
            except Exception as e:
                b64_map = None
                print(f"Lỗi khi đọc bản đồ: {e}")

            # Lấy dữ liệu thống kê
            stats = {
                "total": latest_stats.get("total", 0),
                "safety": latest_stats.get("safety", 0),
                "no_safety": latest_stats.get("no_safety", 0),
                "machinery": latest_stats.get("machinery", 0),
                "fps": latest_stats.get("fps", 0)
            }

            try:
                await websocket.send_json({
                    "image": b64,
                    "map": b64_map,
                    "stats": stats,
                    "warning": show_warning
                })
            except WebSocketDisconnect:
                print(f"WebSocket ngắt kết nối (camera {cam_id})")
                break

            await asyncio.sleep(delay)

    finally:
        cap.release()
        print(f"Đã dừng stream camera {cam_id}")
