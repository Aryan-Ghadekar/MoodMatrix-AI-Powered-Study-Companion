#  Main code for the real-time cognitive load calculation using Random Forest weights and Kalman Filter

import cv2
import numpy as np
import time
from deepface import DeepFace
from collections import deque
import json
import joblib
import os
from sklearn.ensemble import RandomForestRegressor, RandomForestClassifier

# ===========================================================
# CONFIGURATION
# ===========================================================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_DIR = os.path.join(BASE_DIR, "models")

# --- Load Emotion Weights ---
with open(os.path.join(BASE_DIR, "emotion_importance.json"), "r") as f:
    model_data = json.load(f)

EMOTION_KEYS = ['happy', 'sad', 'angry', 'fear', 'disgust', 'surprise', 'neutral']
W = np.array([model_data[e] for e in EMOTION_KEYS])
W = W / np.sum(np.abs(W))  # normalize weights
INTERCEPT = model_data.get("intercept", 0.0)

# --- Load Scaler & Model ---
SCALER_FILE = os.path.join(MODEL_DIR, "emotion_scaler1.pkl")
MODEL_FILE = os.path.join(MODEL_DIR, "rf_cognitive_load_model1.pkl")

scaler = joblib.load(SCALER_FILE) if os.path.exists(SCALER_FILE) else None
print(f"[INFO] Scaler loaded: {bool(scaler)}")

model = joblib.load(MODEL_FILE) if os.path.exists(MODEL_FILE) else None
print(f"[INFO] Model loaded: {bool(model)}")

# ===========================================================
# PARAMETERS
# ===========================================================
BETA = 0.9       # exponential smoothing for continuity
alpha1 = 0.8      # weight for focus term
alpha2 = 1.2      # weight for emotional strain
WINDOW_SIZE = 5
FPS = 10

emotion_smoother = {k: deque(maxlen=5) for k in EMOTION_KEYS}
prev_focus = 0.5
prev_CL = 0.5
load_history = deque(maxlen=WINDOW_SIZE * FPS)

# ===========================================================
# KALMAN FILTER INITIALIZATION
# ===========================================================
A = np.array([[1, 1],
              [0, 1]])  # state transition
H = np.array([[1, 0]])  # measurement mapping
Q = np.array([[1e-5, 0],
              [0, 1e-4]])  # process noise
R = np.array([[1e-2]])  # measurement noise
x = np.array([[0.5], [0]])  # initial state (CL=0.5, rate=0)
P = np.eye(2)  # initial covariance

def kalman_update(measurement):
    """Simple Kalman filter update for smooth CL estimation"""
    global x, P
    # Prediction step
    x_pred = A @ x
    P_pred = A @ P @ A.T + Q

    # Update step
    y = measurement - (H @ x_pred)
    S = H @ P_pred @ H.T + R
    K = P_pred @ H.T @ np.linalg.inv(S)
    x = x_pred + (K @ y)
    P = (np.eye(2) - (K @ H)) @ P_pred
    return float(x[0])

# ===========================================================
# MAIN LOOP
# ===========================================================
cap = cv2.VideoCapture(0)
print("[INFO] MoodMatrix Cognitive Load Analyzer Started")

while True:
    ret, frame = cap.read()
    if not ret:
        break

    try:
        results = DeepFace.analyze(frame, actions=['emotion'], enforce_detection=False)
        if not isinstance(results, list):
            results = [results]

        for result in results:
            x1, y1, w, h = result['region']['x'], result['region']['y'], result['region']['w'], result['region']['h']
            emotions = result['emotion']

            # --- Smooth emotion signals ---
            for k in EMOTION_KEYS:
                emotion_smoother[k].append(emotions.get(k, 0))
            E_raw = np.array([np.mean(emotion_smoother[k]) for k in EMOTION_KEYS]) / 100.0
            E_scaled = scaler.transform(E_raw.reshape(1, -1))[0] if scaler else E_raw

            # --- Focus (Linear Component) ---
            F = np.dot(E_scaled, W) + INTERCEPT
            F = np.clip(F, 0, 1)
            smoothed_F = BETA * prev_focus + (1 - BETA) * F
            prev_focus = smoothed_F

            # --- Emotional Strain (Effort) ---
            e_dash = (W[2] * E_raw[2]) + (W[1] * E_raw[1]) + (W[3] * E_raw[3])  # angry, sad, fear

            # --- Mathematical Cognitive Load (Base Model) ---
            CL_math = 1 - np.exp(-alpha1 * (1 - smoothed_F) - alpha2 * e_dash)
            CL_math = np.clip(CL_math, 0, 1)

            # --- ML-based Cognitive Load ---
            if isinstance(model, RandomForestRegressor):
                CL_ml = model.predict(E_scaled.reshape(1, -1))[0]
            elif isinstance(model, RandomForestClassifier):
                CL_ml = model.predict_proba(E_scaled.reshape(1, -1))[0][1]
            else:
                CL_ml = F  # fallback

            CL_ml = np.clip(CL_ml, 0, 1)

            # --- Fusion (Combine Mathematical + ML) ---
            CL_fused = 0.6 * CL_math + 0.4 * CL_ml

            # --- Exponential smoothing ---
            smoothed_CL = BETA * prev_CL + (1 - BETA) * CL_fused
            prev_CL = smoothed_CL

            # --- Kalman filter ---
            kalman_CL = kalman_update(smoothed_CL)

            # --- Moving average (extra stability) ---
            load_history.append(kalman_CL)
            CL_avg = np.mean(load_history)

            # --- Display ---
            emotion = result['dominant_emotion']
            CL_percent = round(CL_avg * 100, 2)
            cv2.rectangle(frame, (x1, y1), (x1 + w, y1 + h), (0, 255, 0), 2)
            cv2.putText(frame, f"{emotion} | CL: {CL_percent}%", (x1, y1 - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)

    except Exception as e:
        print(f"[WARN] {e}")

    cv2.imshow("MoodMatrix - Cognitive Load (Hybrid Kalman Fusion)", frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
