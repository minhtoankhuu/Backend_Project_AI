# tracker.py
from collections import deque
import numpy as np
import cv2

class Track:
    def __init__(self, track_id, bbox, frame_id):
        self.track_id = track_id
        self.bbox = bbox
        self.last_seen = frame_id
        self.history = deque(maxlen=30)

class Tracker:
    def __init__(self, iou_threshold=0.3, max_lost=30):
        self.next_id = 0
        self.tracks = {}
        self.iou_threshold = iou_threshold
        self.max_lost = max_lost

    def update(self, detections, frame_id):
        updated_tracks = {}
        unmatched_dets = set(range(len(detections)))
        unmatched_tracks = list(self.tracks.keys())

        for track_id in unmatched_tracks:
            track = self.tracks[track_id]
            best_iou = 0
            best_det_idx = -1
            for det_idx in unmatched_dets:
                iou = self.compute_iou(track.bbox, detections[det_idx])
                if iou > best_iou:
                    best_iou = iou
                    best_det_idx = det_idx

            if best_iou > self.iou_threshold:
                new_bbox = detections[best_det_idx]
                track.bbox = new_bbox
                track.last_seen = frame_id
                track.history.append(new_bbox)
                updated_tracks[track_id] = track
                unmatched_dets.remove(best_det_idx)
            else:
                if frame_id - track.last_seen < self.max_lost:
                    updated_tracks[track_id] = track  # vẫn giữ nếu chưa mất lâu

        # tạo track mới cho các detection chưa gán
        for det_idx in unmatched_dets:
            new_track = Track(self.next_id, detections[det_idx], frame_id)
            updated_tracks[self.next_id] = new_track
            self.next_id += 1

        self.tracks = updated_tracks
        return {tid: track.bbox for tid, track in self.tracks.items()}

    @staticmethod
    def compute_iou(boxA, boxB):
        xA = max(boxA[0], boxB[0])
        yA = max(boxA[1], boxB[1])
        xB = min(boxA[2], boxB[2])
        yB = min(boxA[3], boxB[3])

        interArea = max(0, xB - xA) * max(0, yB - yA)
        boxAArea = (boxA[2] - boxA[0]) * (boxA[3] - boxA[1])
        boxBArea = (boxB[2] - boxB[0]) * (boxB[3] - boxB[1])

        iou = interArea / float(boxAArea + boxBArea - interArea + 1e-6)
        return iou
