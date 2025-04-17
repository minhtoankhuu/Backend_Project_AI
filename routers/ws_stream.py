from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from yolov8.detect import run_detection_frame, VIDEO_PATHS
import cv2
import base64
import asyncio

router = APIRouter()

@router.websocket("/ws/stream/{cam_id}")
async def websocket_stream(websocket: WebSocket, cam_id: int):
    await websocket.accept()
    print(f"WebSocket nhận kết nối từ camera {cam_id}")

    video_path = VIDEO_PATHS.get(cam_id)
    cap = cv2.VideoCapture(video_path)
    fps = cap.get(cv2.CAP_PROP_FPS) or 25
    delay = max(1 / fps, 0.04)

    try:
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                print("Đặt lại video về đầu...")
                cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                continue

            frame = run_detection_frame(frame, cam_id)
            _, buffer = cv2.imencode('.jpg', frame)
            b64 = base64.b64encode(buffer).decode('utf-8')

            try:
                await websocket.send_text(b64)
            except WebSocketDisconnect:
                print(f"WebSocket ngắt kết nối (camera {cam_id})")
                break

            await asyncio.sleep(delay)

    finally:
        cap.release()
        print(f"Đã dừng stream camera {cam_id}")

