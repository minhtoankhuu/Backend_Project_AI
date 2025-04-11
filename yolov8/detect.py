from ultralytics import YOLO
import cv2
import os
from datetime import datetime
import numpy as np
from yolov8.shared_state import latest_stats

model = YOLO("weights/best.pt")

VIDEO_PATHS = {
    1: "videos/video1.mp4",
    2: "videos/video2.mp4",
    3: "videos/video3.mp4",
    4: "videos/video4.mp4",
    5: 0  # Webcam
    # 5: "rtsp://admin:your_password@192.168.1.100:554/stream1"
}

CLASS_NAMES = ["Person", "Safety", "No-Safety"]


def update_map_cv(positions, colors):
    width, height = 400, 400
    img = np.ones((height, width, 3), dtype=np.uint8) * 255

    for i in range(0, width, 80):
        cv2.line(img, (i, 0), (i, height), (200, 200, 200), 1)
    for i in range(0, height, 80):
        cv2.line(img, (0, i), (width, i), (200, 200, 200), 1)

    for (x, y), color in zip(positions, colors):
        px = int(x * width)
        py = int((1 - y) * height)
        if color == "blue":
            bgr = (0, 255, 0)
        elif color == "red":
            bgr = (0, 0, 255)
        else:
            bgr = (0, 255, 255)
        cv2.circle(img, (px, py), 10, bgr, -1)

    os.makedirs("static/map", exist_ok=True)
    cv2.imwrite("static/map/2d_map.png", img)


def calculate_position(box, frame_width, frame_height):
    CAMERA_HEIGHT = 8.5
    CAMERA_ANGLE = 50
    ANGLE_RAD = np.radians(CAMERA_ANGLE)

    x1, y1, x2, y2 = box
    center_x = (x1 + x2) / 2 / frame_width
    bottom_y = y2 / frame_height
    depth = CAMERA_HEIGHT * np.tan(ANGLE_RAD) * (1 - bottom_y)
    norm_depth = max(0, min(1, depth / (CAMERA_HEIGHT * np.tan(ANGLE_RAD))))
    return center_x, norm_depth


def run_detection_frame(frame):
    start_time = datetime.now()
    result = model.predict(source=frame, conf=0.3, verbose=False)[0]
    boxes = result.boxes
    classes = boxes.cls.cpu().numpy()
    coords = boxes.xyxy.cpu().numpy()
    frame_height, frame_width = frame.shape[:2]

    persons = {}
    safeties = []
    no_safeties = []

    for i, class_id in enumerate(classes):
        box = coords[i]
        x1, y1, x2, y2 = map(int, box)
        label = CLASS_NAMES[int(class_id)]

        if label == "Person":
            persons[(x1, y1, x2, y2)] = {"safety": False, "no_safety": False}
        elif label == "Safety":
            safeties.append((x1, y1, x2, y2))
        elif label == "No-Safety":
            no_safeties.append((x1, y1, x2, y2))

    for s_box in safeties:
        for p_box in persons:
            if s_box[0] >= p_box[0] and s_box[1] >= p_box[1] and s_box[2] <= p_box[2] and s_box[3] <= p_box[3]:
                persons[p_box]["safety"] = True

    for ns_box in no_safeties:
        for p_box in persons:
            if ns_box[0] >= p_box[0] and ns_box[1] >= p_box[1] and ns_box[2] <= p_box[2] and ns_box[3] <= p_box[3]:
                persons[p_box]["no_safety"] = True

    positions, colors = [], []
    safety = 0
    no_safety = 0

    for p_box, status in persons.items():
        x1, y1, x2, y2 = p_box

        if status["no_safety"]:
            color = (0, 0, 255)
            colors.append("red")
            no_safety += 1
        elif status["safety"]:
            color = (0, 255, 0)
            colors.append("blue")
            safety += 1
        else:
            color = (0, 255, 255)
            colors.append("yellow")

        cv2.rectangle(frame, (x1, y1), (x2, y2), color, 3)
        cv2.putText(frame, "Person", (x1, y1 - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)

        pos = calculate_position((x1, y1, x2, y2), frame_width, frame_height)
        positions.append(pos)

    for box in safeties + no_safeties:
        x1, y1, x2, y2 = map(int, box)
        color = (0, 255, 0) if box in safeties else (0, 0, 255)
        cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)

    update_map_cv(positions, colors)

    end_time = datetime.now()
    elapsed = (end_time - start_time).total_seconds()
    fps = 1 / elapsed if elapsed > 0 else 0
    total = len(persons)

    latest_stats.update({
        "total": total,
        "safety": safety,
        "no_safety": no_safety,
        "fps": round(fps, 2)
    })

    return frame


def run_detection(cam_id: int):
    if cam_id not in VIDEO_PATHS:
        return None, "Invalid cam_id"

    video_path = VIDEO_PATHS[cam_id]
    if not os.path.exists(video_path) and cam_id != 5:
        return None, f"File not found: {video_path}"

    cap = cv2.VideoCapture(video_path)
    ret, frame = cap.read()
    cap.release()

    if not ret:
        return None, "Unable to read video"

    run_detection_frame(frame)
    return "static/map/2d_map.png", None
