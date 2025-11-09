# Main code for the real-time cognitive load calculation 

import cv2
import numpy as np
import time
from deepface import DeepFace
from collections import deque
import json
import joblib  

# -----------------------------
# LOAD TRAINED WEIGHTS & SCALER
# -----------------------------
with open("emotion_weights.json", "r") as f:
    model_data = json.load(f)

EMOTION_KEYS = ['happy', 'sad', 'angry', 'fear', 'disgust', 'surprise', 'neutral']
W = np.array([model_data[e] for e in EMOTION_KEYS])
INTERCEPT = model_data["intercept"]

# Load the same scaler used during training
scaler = joblib.load("emotion_scaler.pkl")

# -----------------------------
# MODEL PARAMETERS
# -----------------------------
alpha1 = 0.8
alpha2 = 1.2
beta = 0.95
WINDOW_DURATION = 5
FPS_ESTIMATE = 10

prev_focus = [0.5 for _ in range(30)]
load_history = [deque(maxlen=WINDOW_DURATION * FPS_ESTIMATE) for _ in range(30)]

cap = cv2.VideoCapture(0)
start_time = time.time()

print("[INFO] Real-time Cognitive Load Monitor Initialized")

while True:
    ret, frame = cap.read()
    if not ret:
        break

    try:
        results = DeepFace.analyze(frame, actions=['emotion'], enforce_detection=False)
        if not isinstance(results, list):
            results = [results]

        for idx, result in enumerate(results[:30]):
            x, y, w, h = result['region']['x'], result['region']['y'], result['region']['w'], result['region']['h']
            emotions = result['emotion']

            # Emotion vector (0–1)
            E = np.array([emotions.get(k, 0) for k in EMOTION_KEYS]) / 100.0
            E_scaled = scaler.transform(E.reshape(1, -1))[0] 

            # ---- Focus computation ----
            F = np.dot(E_scaled, W) + INTERCEPT
            F = np.clip(F, 0, 1)

            smoothed_F = beta * prev_focus[idx] + (1 - beta) * F
            prev_focus[idx] = smoothed_F

            # Effort (emotional strain)
            e_dash = (W[2] * E[2]) + (W[1] * E[1]) + (W[3] * E[3])

            # ---- Cognitive Load computation ----
            CL_instant = 1 - np.exp(-alpha1 * (1 - smoothed_F) - alpha2 * e_dash)
            CL_instant = np.clip(CL_instant, 0, 1)

            load_history[idx].append(CL_instant)
            CL_avg = np.mean(load_history[idx])

            if time.time() - start_time > WINDOW_DURATION:
                emotion = result['dominant_emotion']
                cognitive_load_percent = round(CL_avg * 100, 2)

                cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
                cv2.putText(frame, f"{emotion} | CL: {cognitive_load_percent}%",
                            (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)

    except Exception as e:
        print(f"[WARNING] {e}")

    cv2.imshow("MoodMatrix Cognitive Load (Calibrated)", frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
