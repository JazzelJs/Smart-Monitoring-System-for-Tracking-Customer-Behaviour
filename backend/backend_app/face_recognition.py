import cv2 as cv
import numpy as np
import redis
import pickle
from backend_app.models import Customer, UserCafe
from django.utils import timezone
import time

# === Redis Setup ===
redis_client = redis.StrictRedis(host='localhost', port=6379, decode_responses=False)

# === Load Models ===
face_detection_model = "D:/Kuliah/Tugas Akhir/TheTugasFinal/models/face_detection_models/face_detection_yunet_2023mar.onnx"
face_recognition_model = "D:/Kuliah/Tugas Akhir/TheTugasFinal/models/face_detection_models/face_recognition_sface_2021dec.onnx"

detector = cv.FaceDetectorYN.create(face_detection_model, "", (320, 320), score_threshold=0.9, nms_threshold=0.3, top_k=5000)
recognizer = cv.FaceRecognizerSF.create(face_recognition_model, "")

recognition_threshold = 0.5
detection_delay = 3
new_customers = {}

# === Redis Embeddings ===
def store_embedding_in_redis(name, feature):
    redis_client.hset("face_embeddings", name, pickle.dumps(feature))

def load_known_faces():
    known = {}
    for name, feature in redis_client.hgetall("face_embeddings").items():
        try:
            known[name.decode()] = pickle.loads(feature)
        except:
            pass
    return known

def store_face_image_in_redis(name, image):
    _, buffer = cv.imencode(".jpg", image, [cv.IMWRITE_JPEG_QUALITY, 70])
    redis_client.hset("face_images", name, buffer.tobytes())

# === Core Logic ===
def recognize_face(face_feature):
    best_match, best_score = "Unknown", 0.0
    for name, stored_feature in load_known_faces().items():
        score = recognizer.match(face_feature, stored_feature, cv.FaceRecognizerSF_FR_COSINE)
        if score > best_score:
            best_score, best_match = score, name

    if best_match != "Unknown" and best_score >= recognition_threshold:
        try:
            customer = Customer.objects.get(face_id=best_match)
            customer.visit_count += 1
            customer.last_visit = timezone.now()
            customer.status = 'returning'
            customer.save()
        except Customer.DoesNotExist:
            pass

    return best_match, best_score

def save_new_customer(frame, coords):
    x, y, w, h = coords
    crop = frame[y:y+h, x:x+w]
    if crop.size == 0: return

    count = redis_client.hlen("face_images")
    face_id = f"customer_{count + 1}"

    store_face_image_in_redis(face_id, crop)
    resized = cv.resize(crop, (320, 320))
    detector.setInputSize((320, 320))
    faces = detector.detect(resized)
    if faces[1] is not None:
        aligned = recognizer.alignCrop(resized, faces[1][0])
        feature = recognizer.feature(aligned)
        store_embedding_in_redis(face_id, feature)

    cafe_id = redis_client.get("active_cafe_id")
    assigned_cafe = UserCafe.objects.get(id=int(cafe_id)) if cafe_id else UserCafe.objects.first()


    Customer.objects.create(
        face_id=face_id,
        cafe=assigned_cafe,
        first_visit=timezone.now(),
        visit_count=1,
        last_visit=timezone.now(),
        average_stay=0.0,
        status='new'
    )

def process_face_recognition(frame):
    results = []
    detector.setInputSize((frame.shape[1], frame.shape[0]))
    faces = detector.detect(frame)
    if faces[1] is not None:
        for idx, face in enumerate(faces[1]):
            x, y, w, h = face[:4].astype(int)
            coords = (x, y, w, h)
            aligned = recognizer.alignCrop(frame, face)
            feature = recognizer.feature(aligned)
            name, score = recognize_face(feature)

            if score < recognition_threshold:
                name = "New Customer"

            if name == "New Customer":
                if idx not in new_customers:
                    new_customers[idx] = time.time()
                elif time.time() - new_customers[idx] >= detection_delay:
                    save_new_customer(frame, coords)
                    del new_customers[idx]

            results.append((coords, name))
    return results
