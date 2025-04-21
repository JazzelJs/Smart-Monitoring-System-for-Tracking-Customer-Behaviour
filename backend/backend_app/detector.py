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
import backend_app.shared_video as shared_video



# === Django setup ===
sys.path.append("D:/Kuliah/Tugas Akhir/TheTugasFinal/backend")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend.settings")
django.setup()
from backend_app.models import EntryEvent

# === Thread Control ===
detection_thread = None
running = False

# === Redis and YOLO model ===
redis_client = redis.Redis(host='localhost', port=6379, decode_responses=True)
model = YOLO("D:/Kuliah/Tugas Akhir/TheTugasFinal/models/detection_models/best.pt")

# === Parameters ===
CONFIDENCE_THRESHOLD = 0.2
IOU_OCCUPIED_THRESHOLD = 0.5
OCCUPANCY_TIME_THRESHOLD = 10.0
COOLDOWN_FRAME_THRESHOLD = 5
PROXIMITY_PADDING = 20
line_pts = [(1690, 864), (1164, 1018)]  # entry/exit line

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
    global running
    print("[YOLO] Detection thread started")
    running = True

    cap = cv2.VideoCapture("D:/Kuliah/Tugas Akhir/Coding Udemy/Testing Faces/cctv_vids/vid1.mp4")
    frame_count = 0
    registered_chairs = {}
    person_memory = {}
    next_chair_id = 0

    # Load cached chairs
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

    while running:
        ret, frame = cap.read()
        print(f"[DEBUG] Frame read: {ret}")
        if not running:
            print("[YOLO] Stopping loop mid-frame")
            break

        if not ret:
            cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
            continue

        frame_count += 1
        current_time = time.time()
        timestamp_iso = datetime.utcnow().isoformat()
        results = model.track(frame, persist=True)[0]
        detected_persons = []

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

                    # Entry/Exit detection
                    cx, cy = (x1 + x2) // 2, (y1 + y2) // 2
                    current_side = get_side_of_line(line_pts[0], line_pts[1], (cx, cy))
                    prev_side = person_memory.get(track_id)

                    if prev_side is not None:
                        if prev_side < 0 and current_side >= 0:
                            EntryEvent.objects.create(event_type="enter", track_id=track_id)
                            redis_client.set("entry_state", json.dumps({
                                "last_event": "enter", "track_id": track_id, "timestamp": timestamp_iso
                            }))
                        elif prev_side > 0 and current_side <= 0:
                            EntryEvent.objects.create(event_type="exit", track_id=track_id)
                            redis_client.set("entry_state", json.dumps({
                                "last_event": "exit", "track_id": track_id, "timestamp": timestamp_iso
                            }))
                    person_memory[track_id] = current_side

        # === Chair Occupancy Detection ===
        for chair_id, state in registered_chairs.items():
            chair_box = state['box']
            seated = False

            for person_box in detected_persons:
                iou = calculate_iou(chair_box, person_box)
                center_hit = is_center_inside(person_box, chair_box)
                vertical_check = is_vertically_aligned(chair_box, person_box)
                proximity_hit = is_person_near_chair(person_box, chair_box)

                if (center_hit or proximity_hit) and vertical_check:
                    seated = True
                    break
                elif iou > IOU_OCCUPIED_THRESHOLD and vertical_check:
                    seated = True
                    break

            if seated:
                state['cooldown'] = 0
                if state['start_time'] is None:
                    state['start_time'] = current_time
                elif not state['occupied'] and (current_time - state['start_time']) >= OCCUPANCY_TIME_THRESHOLD:
                    state['occupied'] = True
            else:
                state['cooldown'] += 1
                if state['cooldown'] >= COOLDOWN_FRAME_THRESHOLD:
                    state['start_time'] = None
                    state['occupied'] = False

        # === Update Redis ===
        chair_data = {
            "chairs": {
                str(chair_id): {
                    "status": "occupied" if state["occupied"] else "available",
                    "box": list(state["box"])
                }
                for chair_id, state in registered_chairs.items()
            },
            "timestamp": current_time
        }
        redis_client.set("chair_occupancy", json.dumps(chair_data))

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
            print("[DEBUG] latest_frame UPDATED")
        print(f"[YOLO] Frame {frame_count} processed.")
        time.sleep(1)

    # Cache before shutdown
    cache_to_save = {
        "registered_chairs": {
            str(cid): {
                "box": list(state["box"]),
                "occupied": state["occupied"],
                "start_time": state["start_time"],
                "cooldown": state["cooldown"]
            }
            for cid, state in registered_chairs.items()
        },
        "next_chair_id": next_chair_id
    }
    redis_client.set("cached_chair_positions", json.dumps(cache_to_save))
    cap.release()

    print("[YOLO] Detection loop stopped cleanly.")


# === Control Functions ===
def start_detection():
    global detection_thread, running
    if detection_thread is None or not detection_thread.is_alive():
        print("[YOLO] Starting new detection thread.")
        detection_thread = threading.Thread(target=run_detection, daemon=True)
        detection_thread.start()
        return True
    print("[YOLO] Detection already running.")
    return False

def stop_detection():
    global running
    print("[YOLO] Stop signal received.")
    running = False
    return True
