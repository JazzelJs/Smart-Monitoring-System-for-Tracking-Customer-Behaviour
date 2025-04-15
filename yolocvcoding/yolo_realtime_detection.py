from ultralytics import YOLO
import cv2
import time
import redis
import json
import requests
import os

# === Redis Setup ===
redis_client = redis.StrictRedis(host='localhost', port=6379, db=0, decode_responses=True)

# === Load YOLOv8 model ===
model = YOLO("run300epoch/weights/best.pt")

# Class config
CLASS_NAMES = {0: 'kursi', 2: 'orang'}
CLASS_COLORS = {
    0: (0, 165, 255),  # kursi: orange
    2: (0, 255, 0)     # orang: green
}

# Parameters
CONFIDENCE_THRESHOLD = 0.4
IOU_OCCUPIED_THRESHOLD = 0.2
OCCUPANCY_TIME_THRESHOLD = 2.0  # seconds
COOLDOWN_FRAME_THRESHOLD = 5
PROXIMITY_PADDING = 20
SEND_INTERVAL = 2.0  # seconds

# === Get camera stream from Django (optional) ===
def get_camera_stream():
    access_token = os.getenv("ACCESS_TOKEN")  # Or set manually
    try:
        res = requests.get(
            "http://localhost:8000/api/analytics/get-streams/",
            headers={"Authorization": f"Bearer {access_token}"}
        )
        data = res.json()
        if data.get("streams"):
            return data["streams"][0]["stream_url"]
    except Exception as e:
        print("Failed to fetch camera stream:", e)
    return None

# === Choose source (camera or video) ===
USE_CAMERA_STREAM = False  # Set to True to use camera model stream

if USE_CAMERA_STREAM:
    video_source = get_camera_stream()
    if not video_source:
        print("No camera stream found, exiting.")
        exit()
else:
    video_source = "D:/Kuliah/Tugas Akhir/Coding Udemy/Testing Faces/cctv_vids/vid.mp4"

cap = cv2.VideoCapture(video_source)
fps = cap.get(cv2.CAP_PROP_FPS) or 30
width, height = int(cap.get(3)), int(cap.get(4))
out = cv2.VideoWriter("chair_occupancy_filtered2.mp4", cv2.VideoWriter_fourcc(*'mp4v'), int(fps), (width, height))

# === Helper Functions ===
def calculate_iou(boxA, boxB):
    xA = max(boxA[0], boxB[0])
    yA = max(boxA[1], boxB[1])
    xB = min(boxA[2], boxB[2])
    yB = min(boxA[3], boxB[3])
    interArea = max(0, xB - xA) * max(0, yB - yA)
    boxAArea = (boxA[2] - boxA[0]) * (boxA[3] - boxA[1])
    boxBArea = (boxB[2] - boxB[0]) * (boxB[3] - boxB[1])
    return interArea / float(boxAArea + boxBArea - interArea + 1e-6)

def is_person_near_chair(person_box, chair_box, padding=20):
    px = (person_box[0] + person_box[2]) // 2
    py = (person_box[1] + person_box[3]) // 2
    cx1 = chair_box[0] - padding
    cy1 = chair_box[1] - padding
    cx2 = chair_box[2] + padding
    cy2 = chair_box[3] + padding
    return cx1 <= px <= cx2 and cy1 <= py <= cy2

def is_center_inside(person_box, chair_box):
    cx = (person_box[0] + person_box[2]) // 2
    cy = (person_box[1] + person_box[3]) // 2
    return chair_box[0] <= cx <= chair_box[2] and chair_box[1] <= cy <= chair_box[3]

def is_vertically_aligned(chair_box, person_box):
    _, y1_chair, _, y2_chair = chair_box
    _, y1_person, _, y2_person = person_box
    return y1_person < y2_chair and y2_person > y1_chair

def is_valid_seated_position(chair_box, person_box):
    center_hit = is_center_inside(person_box, chair_box)
    vertical_check = is_vertically_aligned(chair_box, person_box)
    proximity_hit = is_person_near_chair(person_box, chair_box, PROXIMITY_PADDING)
    iou = calculate_iou(chair_box, person_box)
    return ((center_hit or proximity_hit) and vertical_check) or (iou > IOU_OCCUPIED_THRESHOLD and vertical_check)

# === Tracking ===
registered_chairs = {}
next_chair_id = 0
frame_count = 0
last_sent_time = 0

while True:
    ret, frame = cap.read()
    if not ret:
        break

    current_time = time.time()
    frame_count += 1
    annotated_frame = frame.copy()

    if frame_count == 1:
        results = model.track(frame, persist=True)[0]
        if results and results.boxes is not None:
            for box in results.boxes:
                if int(box.cls[0]) == 0 and float(box.conf[0]) >= CONFIDENCE_THRESHOLD:
                    x1, y1, x2, y2 = map(int, box.xyxy[0])
                    new_box = (x1, y1, x2, y2)
                    duplicate = False
                    for c in registered_chairs.values():
                        if calculate_iou(c['box'], new_box) > 0.8:
                            duplicate = True
                            break
                    if not duplicate:
                        registered_chairs[next_chair_id] = {
                            'box': new_box,
                            'occupied': False,
                            'start_time': None,
                            'cooldown': 0
                        }
                        next_chair_id += 1
    else:
        results = model.predict(frame)[0]
        detected_persons = []

        if results and results.boxes is not None:
            for box in results.boxes:
                if int(box.cls[0]) == 2 and float(box.conf[0]) >= CONFIDENCE_THRESHOLD:
                    x1, y1, x2, y2 = map(int, box.xyxy[0])
                    detected_persons.append((x1, y1, x2, y2))

        for chair_id, state in registered_chairs.items():
            chair_box = state['box']
            seated_detected = False

            for person_box in detected_persons:
                if is_valid_seated_position(chair_box, person_box):
                    seated_detected = True
                    break

            if seated_detected:
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

    occupied_chairs = sum(1 for c in registered_chairs.values() if c['occupied'])
    available_chairs = len(registered_chairs) - occupied_chairs

    if current_time - last_sent_time >= SEND_INTERVAL:
        redis_client.set("seat_occupancy", json.dumps({
            "occupied": occupied_chairs,
            "available": available_chairs,
            "timestamp": current_time
        }))
        last_sent_time = current_time

    for chair_id, state in registered_chairs.items():
        x1, y1, x2, y2 = state['box']
        color = (0, 0, 255) if state['occupied'] else (0, 255, 0)
        label = "Occupied" if state['occupied'] else "Available"
        cv2.rectangle(annotated_frame, (x1, y1), (x2, y2), color, 3)
        cv2.putText(annotated_frame, label, (x1, y1 - 10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)

    cv2.putText(annotated_frame, f"Occupied Chairs: {occupied_chairs}", (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
    cv2.putText(annotated_frame, f"Available Chairs: {available_chairs}", (10, 70),
                cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

    cv2.imshow("Chair Occupancy Filtered", annotated_frame)
    out.write(annotated_frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
out.release()
cv2.destroyAllWindows()
