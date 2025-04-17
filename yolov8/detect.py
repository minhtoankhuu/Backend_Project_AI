from ultralytics import YOLO
import cv2
import os
from datetime import datetime
import numpy as np
from yolov8.shared_state import latest_stats
from yolov8.tracker import Tracker

model = YOLO("weights/best.pt")
tracker = Tracker()

VIDEO_PATHS = {
    1: "videos/video1.mp4",
    2: "videos/video2.mp4",
    3: "videos/video3.mp4",
    4: "videos/video4.mp4",
    5: 0
}

CLASS_NAMES = ["Person", "Safety", "No-Safety"]

# dict theo dõi vi phạm mỗi người
violation_timers = {}

def update_map_cv(positions, colors, cam_id=1):
    width, height = 400, 400

    # Ảnh nền theo camera ID
    map_path = f"static/map/2dmap_cam{cam_id}.png"

    if os.path.exists(map_path):
        img = cv2.imread(map_path)
        img = cv2.resize(img, (width, height))  # Resize nếu cần
    else:
        img = np.ones((height, width, 3), dtype=np.uint8) * 255  # fallback nền trắng

    # Vẽ các chấm vị trí
    for (x, y), color in zip(positions, colors):
        px = int(x * width)
        py = int((1 - y) * height)  # Tọa độ top-left → bottom-left

        bgr = {
            "blue": (0, 255, 0),     # Safe
            "red": (0, 0, 255),      # No-safety
            "yellow": (0, 255, 255)  # Optional
        }.get(color, (255, 255, 255))

        cv2.circle(img, (px, py), 6, bgr, -1)  # 🔴 nhỏ hơn

    # Đảm bảo folder tồn tại
    os.makedirs("static/map", exist_ok=True)

    # Lưu bản đồ riêng cho camera
    cv2.imwrite(f"static/map/2d_map_cam{cam_id}.png", img)


def calculate_position(box, frame_width, frame_height):
    CAMERA_HEIGHT = 6
    CAMERA_ANGLE = 45
    ANGLE_RAD = np.radians(CAMERA_ANGLE)

    x1, y1, x2, y2 = box
    center_x = (x1 + x2) / 2 / frame_width
    bottom_y = y2 / frame_height
    depth = CAMERA_HEIGHT * np.tan(ANGLE_RAD) * (1 - bottom_y)
    norm_depth = max(0, min(1, depth / (CAMERA_HEIGHT * np.tan(ANGLE_RAD))))
    return center_x, norm_depth


def run_detection_frame(frame, cam_id=0):
    frame_height, frame_width = frame.shape[:2]
    start_time = datetime.now()
    result = model.predict(source=frame, conf=0.25, verbose=False)[0]
    boxes = result.boxes
    classes = boxes.cls.cpu().numpy()
    coords = boxes.xyxy.cpu().numpy()

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

    bbox_list = list(persons.keys())
    track_results = tracker.update(bbox_list, frame_id=int(datetime.now().timestamp() * 1000))

    positions, colors = [], []
    safety, no_safety, total = 0, 0, len(persons)

    now = datetime.now()

    for p_box, status in persons.items():
        x1, y1, x2, y2 = p_box
        track_id = None

        # tìm track_id theo bbox match
        for tid, t_box in track_results.items():
            if np.linalg.norm(np.array(p_box) - np.array(t_box)) < 10:
                track_id = tid
                break

        if not track_id:
            continue

        color = (255, 255, 0)
        tag = "yellow"
        if status["no_safety"]:
            color = (0, 0, 255)
            tag = "red"
            no_safety += 1
        elif status["safety"]:
            color = (0, 255, 0)
            tag = "blue"
            safety += 1

        cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
        cv2.putText(frame, "Person", (x1, y1 - 10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)

        pos = calculate_position((x1, y1, x2, y2), frame_width, frame_height)
        positions.append(pos)
        colors.append(tag)

        # === Violation check ===
        if tag == "red":
            timer = violation_timers.get(track_id)
            if timer is None:
                violation_timers[track_id] = {"start": now, "last_saved": None}
            else:
                delta = (now - timer["start"]).total_seconds()
                if delta >= 3:
                    last_saved = timer["last_saved"]
                    if not last_saved or (now - last_saved).total_seconds() >= 3:
                        os.makedirs("static/violations", exist_ok=True)
                        cam_folder = f"static/violations/cam{cam_id}"
                        os.makedirs(cam_folder, exist_ok=True)
                        pad = 30
                        h, w = frame.shape[:2]
                        x1_pad = max(x1 - pad, 0)
                        y1_pad = max(y1 - pad, 0)
                        x2_pad = min(x2 + pad, w)
                        y2_pad = min(y2 + pad, h)

                        person_crop = frame[y1_pad:y2_pad, x1_pad:x2_pad]
                        filename = os.path.join(cam_folder, f"person_{now.strftime('%H%M%S')}.jpg")
                        cv2.imwrite(filename, person_crop)

                        # === Lưu vào bảng SavedImage ===
                        from db.database import SessionLocal
                        from db import models

                        db = SessionLocal()
                        saved_image = models.SavedImage(
                            camera_id=cam_id,
                            label="No-Safety",
                            image_path = os.path.relpath(filename, "static")
                        )
                        db.add(saved_image)
                        db.commit()
                        db.close()

                        timer["last_saved"] = now
                        # Optional: insert vào database tại đây
        else:
            violation_timers.pop(track_id, None)

    for box in safeties + no_safeties:
        x1, y1, x2, y2 = map(int, box)
        color = (0, 255, 0) if box in safeties else (0, 0, 255)
        cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)

    update_map_cv(positions, colors, cam_id)

    elapsed = (datetime.now() - start_time).total_seconds()
    fps = 1 / elapsed if elapsed > 0 else 0

    latest_stats.update({
        "total": total,
        "safety": safety,
        "no_safety": no_safety,
        "fps": round(fps, 2)
    })

    return frame

    elapsed = (datetime.now() - start_time).total_seconds()
    fps = 1 / elapsed if elapsed > 0 else 0

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
    if not os.path.exists(video_path) and not isinstance(video_path, int):
        return None, f"File not found: {video_path}"

    cap = cv2.VideoCapture(video_path)
    ret, frame = cap.read()
    cap.release()

    if not ret:
        return None, "Unable to read video"

    run_detection_frame(frame, cam_id)
    return "static/map/2d_map.png", None
