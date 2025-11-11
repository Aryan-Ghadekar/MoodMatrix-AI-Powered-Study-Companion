# Main code for hybrid cognitive load analysis (emotion + body posture) in a classroom setting

import cv2
import numpy as np
from collections import deque
from ultralytics import YOLO
import mediapipe as mp
from deepface import DeepFace
import json
import joblib
import os
from sklearn.ensemble import RandomForestRegressor, RandomForestClassifier

# ===========================================================
# CONFIGURATION
# ===========================================================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_DIR = os.path.join(BASE_DIR, "models")

# Load emotion weights
with open(os.path.join(BASE_DIR, "emotion_importance.json"), "r") as f:
    model_data = json.load(f)
EMOTION_KEYS = ['happy', 'sad', 'angry', 'fear', 'disgust', 'surprise', 'neutral']
W = np.array([model_data[e] for e in EMOTION_KEYS])
W = W / np.sum(np.abs(W))
INTERCEPT = model_data.get("intercept", 0.0)

# Load scaler and ML model
SCALER_FILE = os.path.join(MODEL_DIR, "emotion_scaler.pkl")
MODEL_FILE = os.path.join(MODEL_DIR, "rf_cognitive_load_model.pkl")
scaler = joblib.load(SCALER_FILE) if os.path.exists(SCALER_FILE) else None
model = joblib.load(MODEL_FILE) if os.path.exists(MODEL_FILE) else None

# ===========================================================
# PARAMETERS
# ===========================================================
BETA = 0.9
alpha1 = 0.8
alpha2 = 1.2
WINDOW_SIZE_BODY = 10
SMOOTHING_ALPHA = 0.08

# Add this global variable
last_send_time = 0
SEND_INTERVAL = 5  # Send every 5 seconds

emotion_smoother = {k: deque(maxlen=5) for k in EMOTION_KEYS}
prev_focus = 0.5
prev_CL_emotion = 0.5

# Graceful handling variables
missing_person_frames = 0
MISSING_THRESHOLD = 10  # number of frames before resetting to 0

# ===========================================================
# KALMAN FILTER SETUP
# ===========================================================
A = np.array([[1, 1], [0, 1]])
H = np.array([[1, 0]])
Q = np.array([[1e-5, 0], [0, 1e-4]])
R = np.array([[1e-2]])

x_emotion = np.array([[0.0], [0.0]])
P_emotion = np.eye(2)

def kalman_update_emotion(measurement):
    global x_emotion, P_emotion
    x_pred = A @ x_emotion
    P_pred = A @ P_emotion @ A.T + Q
    y = measurement - (H @ x_pred)
    S = H @ P_pred @ H.T + R
    K = P_pred @ H.T @ np.linalg.inv(S)
    x_emotion = x_pred + K @ y
    P_emotion = (np.eye(2) - (K @ H)) @ P_pred
    return float(x_emotion[0])

def kalman_reset_emotion():
    global x_emotion, P_emotion
    x_emotion = np.array([[0.0], [0.0]])
    P_emotion = np.eye(2)

def kalman_init():
    return np.array([[0.5], [0.0]]), np.eye(2)

def kalman_update_body(x, P, measurement):
    x_pred = A @ x
    P_pred = A @ P @ A.T + Q
    y = measurement - (H @ x_pred)
    S = H @ P_pred @ H.T + R
    K = P_pred @ H.T @ np.linalg.inv(S)
    x_new = x_pred + K @ y
    P_new = (np.eye(2) - K @ H) @ P_pred
    return x_new, P_new, float(x_new[0])

# ===========================================================
# BODY POSTURE SETUP
# ===========================================================
mp_pose = mp.solutions.pose
pose = mp_pose.Pose(min_detection_confidence=0.5, min_tracking_confidence=0.5)

def distance(a, b):
    return np.linalg.norm(np.array([a.x, a.y]) - np.array([b.x, b.y]))

class CentroidTracker:
    def __init__(self, max_distance=50, max_disappeared=15):
        self.next_id = 0
        self.objects = {}
        self.disappeared = {}
        self.max_distance = max_distance
        self.max_disappeared = max_disappeared

    def update(self, boxes):
        new_objects = {}
        input_centroids = [(int((x1+x2)/2), int((y1+y2)/2)) for x1, y1, x2, y2 in boxes]

        if len(self.objects) == 0:
            for c in input_centroids:
                new_objects[self.next_id] = c
                self.disappeared[self.next_id] = 0
                self.next_id += 1
            self.objects = new_objects
            return list(self.objects.keys())

        object_ids = list(self.objects.keys())
        object_centroids = list(self.objects.values())
        used_rows, used_cols = set(), set()

        if input_centroids:
            D = np.linalg.norm(np.array(object_centroids)[:, None] - np.array(input_centroids)[None, :], axis=2)
            rows = D.min(axis=1).argsort()
            cols = D.argmin(axis=1)[rows]

            for row, col in zip(rows, cols):
                if row in used_rows or col in used_cols: continue
                if D[row, col] > self.max_distance: continue
                obj_id = object_ids[row]
                new_objects[obj_id] = input_centroids[col]
                self.disappeared[obj_id] = 0
                used_rows.add(row)
                used_cols.add(col)

            for i, c in enumerate(input_centroids):
                if i not in used_cols:
                    new_objects[self.next_id] = c
                    self.disappeared[self.next_id] = 0
                    self.next_id += 1

        for i, obj_id in enumerate(object_ids):
            if i not in used_rows:
                self.disappeared[obj_id] += 1
                if self.disappeared[obj_id] <= self.max_disappeared:
                    new_objects[obj_id] = self.objects[obj_id]

        self.objects = new_objects
        return list(self.objects.keys())

tracker = CentroidTracker()
student_data = {}

def estimate_body_cl(landmarks, history):
    reasons = []
    L_sh = landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER]
    R_sh = landmarks[mp_pose.PoseLandmark.RIGHT_SHOULDER]
    L_hip = landmarks[mp_pose.PoseLandmark.LEFT_HIP]
    R_hip = landmarks[mp_pose.PoseLandmark.RIGHT_HIP]
    nose = landmarks[mp_pose.PoseLandmark.NOSE]
    L_wrist = landmarks[mp_pose.PoseLandmark.LEFT_WRIST]
    R_wrist = landmarks[mp_pose.PoseLandmark.RIGHT_WRIST]

    shoulder_mid = np.array([(L_sh.x+R_sh.x)/2, (L_sh.y+R_sh.y)/2])
    hip_mid = np.array([(L_hip.x+R_hip.x)/2, (L_hip.y+R_hip.y)/2])
    torso_vector = hip_mid - shoulder_mid
    torso_length = np.linalg.norm(torso_vector) + 1e-6

    slope = (hip_mid[0] - shoulder_mid[0]) / torso_length
    slouch_score = np.tanh(abs(slope) / 0.15)
    if slouch_score > 0.5: reasons.append("Slouching")

    hand_dist_norm = min(distance(L_wrist, nose), distance(R_wrist, nose)) / torso_length
    hand_score = np.tanh((0.2 - hand_dist_norm)/0.05)
    if hand_score > 0.5: reasons.append("Hand near head")

    hand_pos = np.array([L_wrist.x, L_wrist.y, R_wrist.x, R_wrist.y])
    velocity = 0
    if history["hand_history"]:
        velocity = np.linalg.norm(hand_pos - history["hand_history"][-1])
    history["hand_history"].append(hand_pos)
    fidget_score = np.tanh(velocity/0.05)
    if fidget_score > 0.5: reasons.append("Fidgeting")

    cl_raw = 0.3*slouch_score + 0.35*hand_score + 0.35*fidget_score
    cl_percent = 100 / (1 + np.exp(-5*cl_raw))

    prev_smooth = history.get("smoothed_score", cl_percent)
    exp_smooth = SMOOTHING_ALPHA*cl_percent + (1 - SMOOTHING_ALPHA)*prev_smooth
    history["smoothed_score"] = exp_smooth

    if "kalman" not in history:
        history["kalman"] = {}
        history["kalman"]["x"], history["kalman"]["P"] = kalman_init()
    x, P = history["kalman"]["x"], history["kalman"]["P"]
    x, P, kalman_smooth = kalman_update_body(x, P, exp_smooth)
    history["kalman"]["x"], history["kalman"]["P"] = x, P

    if "history" not in history: history["history"] = deque(maxlen=WINDOW_SIZE_BODY)
    history["history"].append(kalman_smooth)
    final_score = np.mean(history["history"])
    return max(0, min(100, final_score)), reasons


################################################################### 
import requests
import time
import threading

# Add this function to send data to FastAPI
def send_cognitive_data_to_api(emotion_cl_avg, body_cl_avg, final_cl):
    """Send cognitive load data to FastAPI backend"""
    try:
        data = {
            "current_load": final_cl,
            "emotion_load": emotion_cl_avg,
            "body_load": body_cl_avg,
            "status": "high" if final_cl > 50 else "low",
            "timestamp": time.time()
        }
        
        response = requests.post(
            "http://localhost:8000/cognitive-load/update-data",
            json=data,
            timeout=5
        )
        
        if response.status_code == 200:
            print(f"[API] Data sent successfully: {final_cl:.1f}%")
        else:
            print(f"[API] Failed to send data: {response.status_code}")
            
    except Exception as e:
        print(f"[API] Error sending data: {e}")


###################################################################

# ===========================================================
# VIDEO LOOP
# ===========================================================
yolo_model = YOLO("yolov8n.pt")
cap = cv2.VideoCapture(0)

while True:
    ret, frame = cap.read()
    if not ret:
        continue

    # ----------------- YOLO PERSON DETECTION -----------------
    results_yolo = yolo_model.predict(frame)[0]
    boxes = [(int(det.xyxy[0][0]), int(det.xyxy[0][1]), int(det.xyxy[0][2]), int(det.xyxy[0][3]))
             for det in results_yolo.boxes if int(det.cls[0]) == 0]

    # ----------------- EMOTION COGNITIVE LOAD -----------------
    try:
        if boxes:
            missing_person_frames = 0
            results = DeepFace.analyze(frame, actions=['emotion'], enforce_detection=False)
            if not isinstance(results, list):
                results = [results]

            faces_detected = [res for res in results if res.get('region') and res['region']['w'] > 0 and res['region']['h'] > 0]

            emotion_cl_list = []
            if faces_detected:
                for res in faces_detected:
                    emotions = res['emotion']
                    for k in EMOTION_KEYS:
                        emotion_smoother[k].append(emotions.get(k, 0))
                    E_raw = np.array([np.mean(emotion_smoother[k]) for k in EMOTION_KEYS]) / 100.0
                    E_scaled = scaler.transform(E_raw.reshape(1, -1))[0] if scaler else E_raw
                    F = np.dot(E_scaled, W) + INTERCEPT
                    F = np.clip(F, 0, 1)
                    smoothed_F = BETA * prev_focus + (1 - BETA) * F
                    prev_focus = smoothed_F
                    e_dash = (W[2]*E_raw[2]) + (W[1]*E_raw[1]) + (W[3]*E_raw[3])
                    CL_math = 1 - np.exp(-alpha1*(1-smoothed_F) - alpha2*e_dash)
                    CL_math = np.clip(CL_math, 0, 1)

                    if isinstance(model, RandomForestRegressor):
                        CL_ml = model.predict(E_scaled.reshape(1, -1))[0]
                    elif isinstance(model, RandomForestClassifier):
                        CL_ml = model.predict_proba(E_scaled.reshape(1, -1))[0][1]
                    else:
                        CL_ml = F
                    CL_ml = np.clip(CL_ml, 0, 1)

                    CL_fused = 0.6 * CL_math + 0.4 * CL_ml
                    smoothed_CL = BETA * prev_CL_emotion + (1 - BETA) * CL_fused
                    prev_CL_emotion = smoothed_CL
                    kalman_CL = kalman_update_emotion(smoothed_CL)
                    emotion_cl_list.append(kalman_CL * 100)

                emotion_cl_avg = np.mean(emotion_cl_list)
            else:
                emotion_cl_avg = prev_CL_emotion * 100

        else:
            missing_person_frames += 1
            if missing_person_frames >= MISSING_THRESHOLD:
                emotion_cl_avg = 0
                kalman_reset_emotion()
            else:
                emotion_cl_avg = prev_CL_emotion * 100

    except Exception as e:
        print("[WARN]", e)
        missing_person_frames += 1
        if missing_person_frames >= MISSING_THRESHOLD:
            emotion_cl_avg = 0
            kalman_reset_emotion()
        else:
            emotion_cl_avg = prev_CL_emotion * 100

    # ----------------- BODY POSTURE COGNITIVE LOAD -----------------
    student_ids = tracker.update(boxes)
    body_cl_list = []
    for i, box in enumerate(boxes):
        student_id = student_ids[i]
        x1, y1, x2, y2 = box
        crop = frame[y1:y2, x1:x2]
        crop_rgb = cv2.cvtColor(crop, cv2.COLOR_BGR2RGB)
        res_pose = pose.process(crop_rgb)
        if res_pose.pose_landmarks:
            if student_id not in student_data:
                student_data[student_id] = {"hand_history": deque(maxlen=30)}
            score, _ = estimate_body_cl(res_pose.pose_landmarks.landmark, student_data[student_id])
            student_data[student_id]["displayed_score"] = score
            body_cl_list.append(score)
    body_cl_avg = np.mean(body_cl_list) if body_cl_list else 0

    # # ----------------- FUSED FINAL CL -----------------
    # if body_cl_avg > 0 and emotion_cl_avg > 0:
    #     final_cl = (emotion_cl_avg + body_cl_avg) / 2
    # elif body_cl_avg > 0:
    #     final_cl = body_cl_avg
    # elif emotion_cl_avg > 0:
    #     final_cl = emotion_cl_avg
    # else:
    #     final_cl = 0



    # ----------------- FUSED FINAL CL -----------------
    # Normalize CLs to 0-1
    emotion_norm = emotion_cl_avg / 100.0
    body_norm = body_cl_avg / 100.0

    # Conditions for weight adjustment
    if emotion_norm > 0.52 and body_norm < 0.45:
        # High emotional, low body CL => give more weight to emotional
        w_emotion = 0.95
        w_body = 0.05
    else:
        # Both high or body high => equal weight
        w_emotion = 0.5
        w_body = 0.5

    final_cl = (w_emotion * emotion_cl_avg) + (w_body * body_cl_avg)
    
        # ----------------- SEND TO FASTAPI EVERY 5 SECONDS -----------------
    current_time = time.time()
    if current_time - last_send_time >= SEND_INTERVAL:
        # Run in a separate thread to avoid blocking the video loop
        threading.Thread(
            target=send_cognitive_data_to_api,
            args=(emotion_cl_avg, body_cl_avg, final_cl),
            daemon=True
        ).start()
        last_send_time = current_time





    # ----------------- DISPLAY -----------------
    cl_status_emotion = "Low" if emotion_cl_avg < 50 else "High"
    cl_status_body = "Low" if body_cl_avg < 55 else "High"
    cl_status_final = "Low" if final_cl < 52.5 else "High"

    cv2.putText(frame, f"Emotion CL: {emotion_cl_avg:.1f}% [{cl_status_emotion}]", (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
    cv2.putText(frame, f"Body CL: {body_cl_avg:.1f}% [{cl_status_body}]", (10, 60),
                cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 0, 0), 2)
    cv2.putText(frame, f"Final CL: {final_cl:.1f}% [{cl_status_final}]", (10, 90),
                cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)

    cv2.imshow("Hybrid Cognitive Load (Emotion + Posture)", frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()