# File to be deleted

from ultralytics import YOLO
import cv2
from retinaface import RetinaFace
import numpy as np


def crop_face(frame, face_coords):
    # Yet to be implemented
    pass

def predict_emotion(face_crop):
    # Yet to be implemented
    pass

def temporal_smoothing(emotion_sequence):
   # Yet to be implemented
    pass


# Load YOLO model
yolo_model = YOLO("yolov8n.pt") # We can use yolov8s/yolov8m for better accuracy (heavier models)
PERSON_CLASS_ID = 0
cap = cv2.VideoCapture(0)

# To store recent emotion predictions per person ID
emotion_history_per_id = {}

while True:
    ret, frame = cap.read()
    if not ret:
        break

    # YOLO person detection + tracking
    results = yolo_model.track(frame, persist=True) 
    if results:
        tracked_objects = results[0].boxes  
        for box in tracked_objects:
            cls_id = int(box.cls[0])
            track_id = int(box.id[0])  # unique person ID
            if cls_id != PERSON_CLASS_ID:
                continue

            x1, y1, x2, y2 = map(int, box.xyxy[0])
            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
            cv2.putText(frame, f"Person {track_id}", (x1, y1-10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0,255,0), 2)

            # RetinaFace detection
            person_crop = frame[y1:y2, x1:x2]
            faces = RetinaFace.detect_faces(person_crop)
            if isinstance(faces, dict):
                for key in faces.keys():
                    face = faces[key]
                    fx1, fy1, fx2, fy2 = map(int, face["facial_area"])
                    fx1 += x1
                    fy1 += y1
                    fx2 += x1
                    fy2 += y1

                    # Draw face bounding box
                    cv2.rectangle(frame, (fx1, fy1), (fx2, fy2), (0, 0, 255), 2)
                    cv2.putText(frame, f"Face {track_id}", (fx1, fy1-10), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0,0,255), 2)

                    # Emotion Recognition Pipeline 
                    face_crop_img = crop_face(frame, (fx1, fy1, fx2, fy2))
                    emotion = predict_emotion(face_crop_img)

                    # Track emotion per person ID
                    if track_id not in emotion_history_per_id:
                        emotion_history_per_id[track_id] = []
                    emotion_history_per_id[track_id].append(emotion)
                    stable_emotion = temporal_smoothing(emotion_history_per_id[track_id])

                    # Display stable emotion
                    cv2.putText(frame, str(stable_emotion), (fx1, fy2+25), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255,0,0), 2)

    cv2.imshow("YOLO + RetinaFace + Emotion + Tracking", frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()


