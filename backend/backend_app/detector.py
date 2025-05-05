# detector.py
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

from backend_app.models import EntryEvent, SeatDetection, Camera, Seat
from backend_app.face_recognition import process_face_recognition, detector as face_detector, recognizer as face_recognizer, recognition_threshold

# === Thread Control ===
detection_thread = None
running = False

# === Redis and YOLO model ===
redis_client = redis.Redis(host='localhost', port=6379, decode_responses=True)
model = YOLO("D:/Kuliah/Tugas Akhir/TheTugasFinal/models/detection_models/best.pt")

# Get from Redis



# === Parameters ===
CONFIDENCE_THRESHOLD = 0.2
IOU_OCCUPIED_THRESHOLD = 0.5
OCCUPANCY_TIME_THRESHOLD = 40
COOLDOWN_FRAME_THRESHOLD = 5
PROXIMITY_PADDING = 20
line_pts = [(1690, 864), (1164, 1018)]

active_detections = {}

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

    cafe_id = redis_client.get("active_cafe_id")
    source_type = redis_client.get("source_type") or "camera"

    from backend_app.models import UserCafe, Floor

    if source_type == "sample":
        stream_url = redis_client.get("sample_video_path") or "D:/default_sample.mp4"

        # Fallback cafe
        cafe = UserCafe.objects.filter(id=cafe_id).first()
        if not cafe:
            print("[ERROR] Cafe not found.")
            return

        # Try to get or create a Camera for video source
        selected_camera, _ = Camera.objects.get_or_create(
            cafe=cafe,
            ip_address="127.0.0.1",  # Fake IP
            channel="video",
            defaults={
                "status": "active",
                "location": "Sample Video",
                "admin_name": "sample",
                "admin_password": "sample",
                "floor": Floor.objects.filter(cafe=cafe).first()  # Use any floor from this cafe
            }
        )
    else:
        selected_ids = json.loads(redis_client.get("selected_camera_ids") or "[]")
        selected_camera = Camera.objects.filter(id__in=selected_ids, cafe_id=cafe_id, status="active").first()
        if not selected_camera:
            print(f"[ERROR] No active camera found for cafe {cafe_id}.")
            return
        stream_url = f"rtsp://{selected_camera.admin_name}:{selected_camera.admin_password}@{selected_camera.ip_address}/{selected_camera.channel}stream2"

    print(f"[INFO] Source Type: {source_type}")
    print(f"[INFO] Stream URL: {stream_url}")



    cap = cv2.VideoCapture(stream_url)
    if not cap.isOpened():
        print(f"[ERROR] Failed to open stream: {stream_url}")
        return

    frame_count = 0
    registered_chairs = {}
    person_memory = {}
    next_chair_id = 0

    cached = redis_client.get(f"cached_chair_positions:cafe:{cafe_id}")
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
            break

        ret, frame = cap.read()
        if not ret:
            cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
            continue

        frame_count += 1
        current_time = time.time()
        results = model.track(frame, persist=True)[0]
        detected_persons = []

        face_results = process_face_recognition(frame)
        for (x, y, w, h), label in face_results:
            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
            cv2.putText(frame, label, (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)

        if results and results.boxes is not None:
            for box in results.boxes:
                cls_id = int(box.cls[0])
                conf = float(box.conf[0])
                x1, y1, x2, y2 = map(int, box.xyxy[0])

                if cls_id == 0 and frame_count <= 3:
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
                    track_id = int(box.id[0])
                    person_box = (x1, y1, x2, y2)
                    detected_persons.append(person_box)
                    cx, cy = (x1 + x2) // 2, (y1 + y2) // 2
                    current_side = get_side_of_line(line_pts[0], line_pts[1], (cx, cy))
                    prev_side = person_memory.get(track_id)
                    if prev_side is not None:
                        if prev_side < 0 and current_side >= 0:
                            EntryEvent.objects.create(event_type="enter", track_id=track_id, camera=selected_camera)
                        elif prev_side > 0 and current_side <= 0:
                            EntryEvent.objects.create(event_type="exit", track_id=track_id, camera=selected_camera)
                    person_memory[track_id] = current_side

        for chair_id, state in registered_chairs.items():
            chair_box = state['box']
            seated = any(
                (is_center_inside(p, chair_box) or is_person_near_chair(p, chair_box)) and is_vertically_aligned(chair_box, p)
                for p in detected_persons
            )

            if seated:
                state['cooldown'] = 0
                if state['start_time'] is None:
                    state['start_time'] = current_time
                elif not state['occupied'] and (current_time - state['start_time']) >= OCCUPANCY_TIME_THRESHOLD:
                    state['occupied'] = True
                    seat_obj, created = Seat.objects.get_or_create(
                        cafe_id=cafe_id,
                        chair_index=chair_id,
                        defaults={
                            "x1": chair_box[0],
                            "y1": chair_box[1],
                            "x2": chair_box[2],
                            "y2": chair_box[3],
                        }
                    )
                    if not created:
                        seat_obj.x1 = chair_box[0]
                        seat_obj.y1 = chair_box[1]
                        seat_obj.x2 = chair_box[2]
                        seat_obj.y2 = chair_box[3]
                        seat_obj.save()

                    
                    cx = (chair_box[0] + chair_box[2]) // 2
                    cy = (chair_box[1] + chair_box[3]) // 2
                    detection = SeatDetection.objects.create(
                        camera=selected_camera,
                        seat=seat_obj,
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

        resized_frame = cv2.resize(frame, (640, 480))

        # Scale factor
        scale_x = 640 / frame.shape[1]
        scale_y = 480 / frame.shape[0]

        # Draw chair boxes
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

        # Draw persons
        if results and results.boxes is not None:
            for box in results.boxes:
                cls_id = int(box.cls[0])
                if cls_id != 2:  # Only draw persons
                    continue
                x1, y1, x2, y2 = map(int, box.xyxy[0])
                x1 = int(x1 * scale_x)
                y1 = int(y1 * scale_y)
                x2 = int(x2 * scale_x)
                y2 = int(y2 * scale_y)
                cv2.rectangle(resized_frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                cv2.putText(resized_frame, "Person", (x1, y1 - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)

                redis_client.set(f"chair_occupancy:cafe:{cafe_id}", json.dumps({
                    "chairs": {
                        str(chair_id): {
                            "status": "occupied" if state["occupied"] else "available",
                            "box": list(state["box"]),
                            "start_time": state.get("start_time")
                        } for chair_id, state in registered_chairs.items()
                    },
                    "timestamp": current_time
                }))

                time.sleep(0.01)

        with shared_video.video_lock:
            shared_video.latest_frame = resized_frame.copy()
            
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