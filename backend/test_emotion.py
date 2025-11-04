# Added Mathematical Part in the code to calculate Cognitive Load based on the Emotions

from deepface import DeepFace
import cv2
import numpy as np
import time
from collections import deque

# --- Model Parameters ---
W = np.array([0.2, 0.4, 0.6, 0.5, -0.6, -0.1, 1.0])
EMOTION_KEYS = ['happy', 'sad', 'angry', 'fear', 'disgust', 'surprise', 'neutral']

# Constants
alpha1 = 0.8      # sensitivity to focus
alpha2 = 1.2      # sensitivity to effort
beta = 0.85       # smoothing constant for focus
WINDOW_DURATION = 5   # seconds for averaging window
FPS_ESTIMATE = 10      # approx frames per second

# Initialize focus and load histories
prev_focus = [0.5 for _ in range(30)]
load_history = [deque(maxlen=WINDOW_DURATION * FPS_ESTIMATE) for _ in range(30)]

cap = cv2.VideoCapture(0)

start_time = time.time()

while True:
    ret, frame = cap.read()
    if not ret:
        break

    try:
        results = DeepFace.analyze(frame, actions=['emotion'], enforce_detection=False)

        if not isinstance(results, list):
            results = [results]

        for idx, result in enumerate(results[:30]):  # max 30 students
            x, y, w, h = result['region']['x'], result['region']['y'], result['region']['w'], result['region']['h']
            emotions = result['emotion']
            E = np.array([emotions.get(k, 0) for k in EMOTION_KEYS]) / 100.0

            # 1️⃣ Calculate Focus
            F = np.dot(E, W)
            F = np.clip(F, 0, 1)

            # 2️⃣ Smooth Focus using EMA
            smoothed_F = beta * prev_focus[idx] + (1 - beta) * F
            prev_focus[idx] = smoothed_F

            # 3️⃣ Effort (e')
            e_dash = (W[3] * E[3]) + (W[2] * E[2]) + (W[1] * E[1])

            # 4️⃣ Instantaneous Cognitive Load
            CL_instant = 1 - np.exp(-alpha1 * (1 - smoothed_F) - alpha2 * e_dash)
            CL_instant = np.clip(CL_instant, 0, 1)

            # 5️⃣ Rolling Average over Time Window
            load_history[idx].append(CL_instant)
            CL_avg = np.mean(load_history[idx]) if len(load_history[idx]) > 0 else CL_instant

            # 6️⃣ Display every few seconds (more realistic behavior)
            elapsed = time.time() - start_time
            if elapsed > WINDOW_DURATION:
                emotion = result['dominant_emotion']
                cognitive_load_percent = round(CL_avg * 100, 2)

                # Bounding box
                cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
                cv2.putText(frame, f"{emotion} | CL: {cognitive_load_percent}%",
                            (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX,
                            0.7, (0, 255, 0), 2)

    except Exception as e:
        print(f"Error in emotion detection: {e}")

    cv2.imshow('MoodMatrix Cognitive Load (Smoothed)', frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
