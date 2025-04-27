import threading
import time
import redis
import json
import cv2
from ultralytics import YOLO
import django
import os
import sys
from datetime import datetime
from django.utils.timezone import make_aware
import backend_app.shared_video as shared_video
import pickle

# === Django setup ===
sys.path.append("D:/Kuliah/Tugas Akhir/TheTugasFinal/backend")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend.settings")
django.setup()
from backend_app.models import EntryEvent, SeatDetection, Camera
from backend_app.face_recognition import process_face_recognition, detector as face_detector, recognizer as face_recognizer, recognition_threshold

CAMERA_ID = 11
try:
    selected_camera = Camera.objects.get(id=CAMERA_ID)
except Camera.DoesNotExist:
    print(f"[ERROR] Camera with ID {CAMERA_ID} not found.")
    selected_camera = None

# === Thread Control ===
detection_thread = None
running = False

# === Redis and YOLO model ===
redis_client = redis.Redis(host='localhost', port=6379, decode_responses=True)
model = YOLO("D:/Kuliah/Tugas Akhir/TheTugasFinal/models/detection_models/best.pt")

# === Parameters ===
CONFIDENCE_THRESHOLD = 0.2
IOU_OCCUPIED_THRESHOLD = 0.5
OCCUPANCY_TIME_THRESHOLD = 40
COOLDOWN_FRAME_THRESHOLD = 5
PROXIMITY_PADDING = 20
line_pts = [(1690, 864), (1164, 1018)]

active_detections = {}
selected_camera = Camera.objects.first()  # Update this if using dynamic camera assignment

# === Utility Functions ===
def calculate_iou(boxA, boxB):
    xA = max(boxA[0], boxB[0])
    yA = max(boxA[1], boxB[1])
    xB = min(boxA[2], boxB[2])
    yB = min(boxA[3], boxB[3])
    interArea = max(0, xB - xA) * max(0, yB - yA)
    boxAArea = (boxA[2] - boxA[0]) * (boxA[3] - boxA[1])
    boxBArea = (boxB[2] - boxB[0]) * (boxB[3] - boxB[1])
    return interArea / float(boxAArea + boxBArea - interArea + 1e-6)

def is_center_inside(person_box, chair_box):
    cx = (person_box[0] + person_box[2]) // 2
    cy = (person_box[1] + person_box[3]) // 2
    return chair_box[0] <= cx <= chair_box[2] and chair_box[1] <= cy <= chair_box[3]

def is_vertically_aligned(chair_box, person_box):
    _, y1_chair, _, y2_chair = chair_box
    _, y1_person, _, y2_person = person_box
    return y1_person < y2_chair and y2_person > y1_chair

def is_person_near_chair(person_box, chair_box, padding=PROXIMITY_PADDING):
    px = (person_box[0] + person_box[2]) // 2
    py = (person_box[1] + person_box[3]) // 2
    cx1 = chair_box[0] - padding
    cy1 = chair_box[1] - padding
    cx2 = chair_box[2] + padding
    cy2 = chair_box[3] + padding
    return cx1 <= px <= cx2 and cy1 <= py <= cy2

def get_side_of_line(p1, p2, point):
    return (p2[0] - p1[0]) * (point[1] - p1[1]) - (p2[1] - p1[1]) * (point[0] - p1[0])

# === Detection Logic ===
def run_detection():
    global running, active_detections
    running = True
    cap = cv2.VideoCapture("D:/Kuliah/Tugas Akhir/Coding Udemy/Testing Faces/cctv_vids/vid5.mp4")
    frame_count = 0
    registered_chairs = {}
    person_memory = {}
    next_chair_id = 0

    cached = redis_client.get("cached_chair_positions")
    if cached:
        try:
            data = json.loads(cached)
            registered_chairs = {
                int(cid): {
                    "box": tuple(c["box"]),
                    "occupied": c["occupied"],
                    "start_time": c["start_time"],
                    "cooldown": c["cooldown"]
                } for cid, c in data["registered_chairs"].items()
            }
            next_chair_id = data["next_chair_id"]
        except:
            pass

    while True:
        if not running:
            print("[YOLO] Stop signal received, exiting detection loop.")
            break

        ret, frame = cap.read()
        if not ret:
            cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
            continue

        frame_count += 1
        current_time = time.time()
        timestamp_iso = datetime.utcnow().isoformat()
        results = model.track(frame, persist=True)[0]
        detected_persons = []

        # === Face Recognition (Refactored) ===
        face_results = process_face_recognition(frame)
        for (x, y, w, h), label in face_results:
            cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)
            cv2.putText(frame, label, (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)


        if results and results.boxes is not None:
            for box in results.boxes:
                cls_id = int(box.cls[0])
                conf = float(box.conf[0])
                if cls_id == 0 and frame_count <= 3:
                    x1, y1, x2, y2 = map(int, box.xyxy[0])
                    new_box = (x1, y1, x2, y2)
                    if not any(calculate_iou(c['box'], new_box) > 0.8 for c in registered_chairs.values()):
                        registered_chairs[next_chair_id] = {
                            'box': new_box,
                            'occupied': False,
                            'start_time': None,
                            'cooldown': 0
                        }
                        next_chair_id += 1
                elif cls_id == 2 and conf >= CONFIDENCE_THRESHOLD and box.id is not None:
                    x1, y1, x2, y2 = map(int, box.xyxy[0])
                    track_id = int(box.id[0])
                    detected_persons.append((x1, y1, x2, y2))
                    cx, cy = (x1 + x2) // 2, (y1 + y2) // 2
                    current_side = get_side_of_line(line_pts[0], line_pts[1], (cx, cy))
                    prev_side = person_memory.get(track_id)
                    if prev_side is not None:
                        if prev_side < 0 and current_side >= 0:
                            EntryEvent.objects.create(event_type="enter", track_id=track_id)
                        elif prev_side > 0 and current_side <= 0:
                            EntryEvent.objects.create(event_type="exit", track_id=track_id)
                    person_memory[track_id] = current_side

        for chair_id, state in registered_chairs.items():
            chair_box = state['box']
            seated = False
            for person_box in detected_persons:
                if (is_center_inside(person_box, chair_box) or is_person_near_chair(person_box, chair_box)) and is_vertically_aligned(chair_box, person_box):
                    seated = True
                    break
                elif calculate_iou(chair_box, person_box) > IOU_OCCUPIED_THRESHOLD and is_vertically_aligned(chair_box, person_box):
                    seated = True
                    break

            if seated:
                state['cooldown'] = 0
                if state['start_time'] is None:
                    state['start_time'] = current_time
                elif not state['occupied'] and (current_time - state['start_time']) >= OCCUPANCY_TIME_THRESHOLD:
                    state['occupied'] = True
                    detection = SeatDetection.objects.create(
                        camera=selected_camera,
                        chair_id=chair_id,
                        time_start=make_aware(datetime.utcfromtimestamp(state['start_time']))
                    )
                    active_detections[chair_id] = detection
            else:
                state['cooldown'] += 1
                if state['cooldown'] >= COOLDOWN_FRAME_THRESHOLD:
                    if state['occupied']:
                        detection = active_detections.get(chair_id)
                        if detection:
                            detection.time_end = make_aware(datetime.utcfromtimestamp(current_time))
                            detection.save()
                            del active_detections[chair_id]
                    state['start_time'] = None
                    state['occupied'] = False

        redis_client.set("chair_occupancy", json.dumps({
            "chairs": {
                str(chair_id): {
                    "status": "occupied" if state["occupied"] else "available",
                    "box": list(state["box"]),
                    "start_time": state.get("start_time")
                } for chair_id, state in registered_chairs.items()
            },
            "timestamp": current_time
        }))

        # === Draw Output ===
        resized_frame = cv2.resize(frame, (640, 480))
        scale_x = 640 / frame.shape[1]
        scale_y = 480 / frame.shape[0]

        # Draw entry/exit line
        scaled_line_pts = [(int(x * scale_x), int(y * scale_y)) for (x, y) in line_pts]
        cv2.line(resized_frame, scaled_line_pts[0], scaled_line_pts[1], (0, 0, 255), 2)

        if results and results.boxes is not None:
            for box in results.boxes:
                cls_id = int(box.cls[0])
                x1, y1, x2, y2 = map(int, box.xyxy[0])
                x1 = int(x1 * scale_x)
                y1 = int(y1 * scale_y)
                x2 = int(x2 * scale_x)
                y2 = int(y2 * scale_y)

                label = "Person" if cls_id == 2 else "Meja" if cls_id == 1 else f"Class {cls_id}"
                color = (0, 255, 0) if cls_id == 2 else (255, 0, 0) if cls_id == 1 else (128, 128, 128)
                cv2.rectangle(resized_frame, (x1, y1), (x2, y2), color, 2)
                cv2.putText(resized_frame, label, (x1, y1 - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)

        # Draw chairs with occupancy status
        for chair_id, state in registered_chairs.items():
            x1, y1, x2, y2 = state["box"]
            x1 = int(x1 * scale_x)
            y1 = int(y1 * scale_y)
            x2 = int(x2 * scale_x)
            y2 = int(y2 * scale_y)
            color = (0, 0, 255) if state["occupied"] else (0, 255, 255)
            label = f"Chair {chair_id}: {'Occupied' if state['occupied'] else 'Available'}"
            cv2.rectangle(resized_frame, (x1, y1), (x2, y2), color, 2)
            cv2.putText(resized_frame, label, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.4, color, 1)

        with shared_video.video_lock:
            shared_video.latest_frame = resized_frame.copy()
        time.sleep(1)

    cap.release()
    print("[YOLO] Detection loop stopped cleanly.")

# === Control Functions ===
def start_detection():
    global detection_thread, running
    if detection_thread is None or not detection_thread.is_alive():
        detection_thread = threading.Thread(target=run_detection, daemon=True)
        detection_thread.start()
        
        return True
    return False

def stop_detection():
    global running, detection_thread
    running = False
    if detection_thread and detection_thread.is_alive():
        detection_thread.join(timeout=5)
    return True
