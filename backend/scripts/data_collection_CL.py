# This code is used to collect cognitive load data and save it in CSV format to be used for weight calculation

import cv2
import os
import time
import csv
from deepface import DeepFace


# SETTINGS
DATA_DIR = "cognitive_load_dataset_csv"
FPS = 10  # approximate frames per second
SESSION_DURATION = 60  # seconds per session
EMOTION_KEYS = ['happy','sad','angry','fear','disgust','surprise','neutral']


# CREATE FOLDER
os.makedirs(DATA_DIR, exist_ok=True)


# FUNCTION TO COLLECT DATA

def collect_session_data_csv(participant_id, cognitive_load_label, environment_info=""):
    """
    participant_id: unique identifier for the participant
    cognitive_load_label: 'high' or 'low'
    environment_info: string describing lighting, environment etc.
    """
    timestamp = int(time.time())
    csv_file = os.path.join(DATA_DIR, f"{participant_id}_{cognitive_load_label}_{timestamp}.csv")

    cap = cv2.VideoCapture(0)
    start_time = time.time()
    frame_count = 0

    print(f"[INFO] Starting session for {participant_id} ({cognitive_load_label})")

    with open(csv_file, mode='w', newline='') as f:
        writer = csv.writer(f)
        # Write header
        header = ['participant_id', 'frame_id', 'cognitive_load_label', 'environment_info'] + EMOTION_KEYS
        writer.writerow(header)

        while time.time() - start_time < SESSION_DURATION:
            ret, frame = cap.read()
            if not ret:
                continue

            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

            try:
                result = DeepFace.analyze(frame_rgb, actions=['emotion'], enforce_detection=False)
                if not isinstance(result, list):
                    result = [result]

                for r in result[:1]:  # take first face detected
                    emotions = [r['emotion'].get(k, 0)/100.0 for k in EMOTION_KEYS]

                    row = [participant_id, frame_count, cognitive_load_label, environment_info] + emotions
                    writer.writerow(row)

            except Exception as e:
                print(f"[WARNING] Emotion detection error: {e}")

            frame_count += 1
            # Display frame
            cv2.putText(frame, f"Participant: {participant_id} | CL: {cognitive_load_label}",
                        (10,30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0,255,0), 2)
            cv2.imshow("Data Collection CSV", frame)

            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

    cap.release()
    cv2.destroyAllWindows()
    print(f"[INFO] Session saved as CSV: {csv_file} ({frame_count} frames)")

# -----------------------------
# EXAMPLE USAGE
# -----------------------------
# Collect 1 minute of high cognitive load for participant 1 in bright lighting
collect_session_data_csv(participant_id="P01", cognitive_load_label="low", environment_info="dim_light_classroom")
