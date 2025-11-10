from deepface import DeepFace
import cv2
import numpy as np

# --- Model Parameters ---
# Pre-assigned focus weights
W = np.array([0.2, 0.4, 0.6, 0.5, -0.6, -0.1, 0.0])
# Emotion order in DeepFace output
EMOTION_KEYS = ['happy', 'sad', 'angry', 'fear', 'disgust', 'surprise', 'neutral']

# Constants
alpha1 = 0.8      # sensitivity to focus
alpha2 = 1.2      # sensitivity to effort
beta = 0.85       # smoothing constant for focus

# Initialize previous focus values for up to 30 students
prev_focus = [0.5 for _ in range(30)]  # starting moderate focus

cap = cv2.VideoCapture(0)

while True:
    ret, frame = cap.read()
    if not ret:
        break

    try:
        # Analyze emotions for all detected faces
        results = DeepFace.analyze(frame, actions=['emotion'], enforce_detection=False)

        # Normalize to list
        if not isinstance(results, list):
            results = [results]

        for idx, result in enumerate(results[:30]):  # limit to 30 students
            x, y, w, h = result['region']['x'], result['region']['y'], result['region']['w'], result['region']['h']

            # --- 1. Get emotion probability vector ---
            emotions = result['emotion']
            E = np.array([emotions.get(k, 0) for k in EMOTION_KEYS]) / 100.0  # convert % to 0–1 scale

            # --- 2. Calculate Focus (dot product) ---
            F = np.dot(E, W)
            F = np.clip(F, 0, 1)  # ensure within range

            # --- 3. Smooth Focus using Exponential Moving Average ---
            smoothed_F = beta * prev_focus[idx] + (1 - beta) * F
            prev_focus[idx] = smoothed_F  # update history

            # --- 4. Compute Effort (e') ---
            e_dash = (W[3] * E[3]) + (W[2] * E[2]) + (W[1] * E[1])  # fear, angry, sad

            # --- 5. Cognitive Load Calculation ---
            CL = 1 - np.exp(-alpha1 * (1 - smoothed_F) - alpha2 * e_dash)
            CL = np.clip(CL, 0, 1)

            # --- 6. Display Results ---
            emotion = result['dominant_emotion']
            cognitive_load_percent = round(CL * 100, 2)

            # Bounding box
            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
            # Emotion + Cognitive Load
            cv2.putText(frame, f"{emotion} | CL: {cognitive_load_percent}%",
                        (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX,
                        0.7, (0, 255, 0), 2)

    except Exception as e:
        print(f"Error in emotion detection: {e}")

    cv2.imshow('MoodMatrix Cognitive Load', frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
