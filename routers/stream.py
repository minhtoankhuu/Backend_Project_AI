from fastapi import APIRouter
import cv2
from fastapi.responses import StreamingResponse
import time
from yolov8.detect import run_detection_frame, VIDEO_PATHS

router = APIRouter()

# Hàm tạo video stream
def generate_stream(cam_id: int):
    video_path = VIDEO_PATHS.get(cam_id)  # Đảm bảo video source đúng
    cap = cv2.VideoCapture(video_path)

    if not cap.isOpened():
        print(f"Không mở được video source: {video_path}")
        return

    fps = cap.get(cv2.CAP_PROP_FPS) or 25
    delay = 1 / fps

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            cap.set(cv2.CAP_PROP_POS_FRAMES, 0)  # Tua lại video khi hết
            continue

        frame = run_detection_frame(frame)  # Áp dụng YOLO detect
        _, buffer = cv2.imencode('.jpg', frame)
        frame_bytes = buffer.tobytes()

        yield (
            b"--frame\r\n"
            b"Content-Type: image/jpeg\r\n\r\n" + frame_bytes + b"\r\n"
        )

        time.sleep(delay)

    cap.release()

@router.get("/stream")
def stream_video(cam_id: int = 1):
    return StreamingResponse(generate_stream(cam_id), media_type="multipart/x-mixed-replace; boundary=frame")
