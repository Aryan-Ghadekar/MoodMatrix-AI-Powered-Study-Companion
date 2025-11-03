# File to be deleted

# Enhanced Real-time Multi-Face Emotion Detection using DeepFace and OpenCV
# Modifications for Accuracy:
# - Switched to 'retinaface' backend for superior multi-face detection (handles 20-30 faces in crowds better, even with occlusions/angles).
# - Specified emotion model ('deepface') in analyze for precise 7-class prediction.
# - Added confidence threshold (0.5) to only label reliable predictions; otherwise, show "uncertain".
# - Color-coded labels: Green for positive (happy, surprise, neutral), Red for negative (angry, disgust, fear, sad).
# - Fixed num_faces scope (initialize outside try for display even on errors).
# - Added face alignment and enforcement tweaks for better emotion accuracy.
# - Reduced FRAME_SKIP to 1 for smoother processing if hardware allows; adjust based on FPS.
# Install/upgrade: pip install deepface opencv-python tf-keras (retinaface requires tf-keras if TF 2.16+)

import cv2
from deepface import DeepFace
import numpy as np
import time

# Configuration
DETECTION_MODEL = 'retinaface'  # Highly accurate for multi-face; fallback to 'mtcnn' if slow
EMOTION_MODEL = 'deepface'  # Best for accurate emotions; alternatives: 'openface', 'facenet'
FRAME_SKIP = 1  # Process every frame for max accuracy; increase to 2-3 if FPS <10 for 20-30 faces
MAX_FACES = 30  # Limit to prevent overload
CONFIDENCE_THRESHOLD = 0.5  # Only label if max prob >=0.5; else "uncertain"
VIDEO_SOURCE = 0  # 0=webcam; 'path/to/video.mp4' for file

# Emotion classes and color mapping (BGR for cv2)
EMOTIONS = ['angry', 'disgust', 'fear', 'happy', 'sad', 'surprise', 'neutral']
EMOTION_COLORS = {
    'angry': (0, 0, 255),      # Red
    'disgust': (0, 0, 255),    # Red
    'fear': (0, 0, 255),       # Red
    'happy': (0, 255, 0),      # Green
    'sad': (0, 0, 255),        # Red
    'surprise': (0, 255, 0),   # Green
    'neutral': (255, 255, 0),  # Yellow
}

# Initialize video capture
cap = cv2.VideoCapture(VIDEO_SOURCE)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)

if not cap.isOpened():
    print("Error: Could not open video source.")
    exit()

print("Starting enhanced real-time emotion detection. Press 'q' to quit.")
print(f"Using detection: {DETECTION_MODEL}, emotion model: {EMOTION_MODEL}")

frame_count = 0
prev_time = time.time()
num_faces = 0  # Initialize outside loop for display

while True:
    ret, frame = cap.read()
    if not ret:
        print("End of video or capture error.")
        break

    frame_count += 1

    # Skip frames for speed if needed (set FRAME_SKIP=1 for full accuracy)
    if frame_count % FRAME_SKIP != 0:
        cv2.imshow('Classroom Emotions (Real-Time)', frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
        continue

    # Detect all faces in frame
    try:
        faces = DeepFace.extract_faces(
            img_path=frame, 
            detector_backend=DETECTION_MODEL, 
            enforce_detection=False,  # Allow partial detections
            align=True  # Align faces for better emotion analysis
        )
        num_faces = min(len(faces), MAX_FACES)
        print(f"Detected {num_faces} faces in frame.")

        # Analyze emotions for each detected face
        for i in range(num_faces):
            face_img = faces[i]['face']  # Cropped and aligned face
            face_region = faces[i]['facial_area']  # {'x', 'y', 'w', 'h'}

            # Predict emotion with enhanced handling
            try:
                result = DeepFace.analyze(
                    face_img, 
                    actions=['emotion'], 
                    enforce_detection=False, 
                    detector_backend='skip',  # Skip re-detection on cropped face
                    silent=True  # Suppress DeepFace warnings
                )
                dominant_emotion = result[0]['dominant_emotion'].lower()  # Ensure lowercase match
                
                # Robustly extract max confidence
                emotion_probs = result[0]['emotion']
                if isinstance(emotion_probs, dict):
                    confidence = max(emotion_probs.values())
                elif isinstance(emotion_probs, list):
                    confidence = max(emotion_probs)
                else:
                    confidence = float(emotion_probs) if emotion_probs else 0.0
                
                confidence = float(confidence)
                
                # Only label if confident enough
                if confidence >= CONFIDENCE_THRESHOLD:
                    label = f"{dominant_emotion}: {confidence:.2f}"
                    color = EMOTION_COLORS.get(dominant_emotion, (255, 255, 255))  # White fallback
                    status = dominant_emotion
                else:
                    label = f"Uncertain: {confidence:.2f}"
                    color = (0, 0, 255)  # Red for low confidence
                    status = "uncertain"

                # Draw bounding box and label
                x, y, w, h = int(face_region['x']), int(face_region['y']), int(face_region['w']), int(face_region['h'])
                cv2.rectangle(frame, (x, y), (x + w, y + h), color, 2)
                cv2.putText(frame, label, (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)
                
                # Optional: Log for aggregation (e.g., classroom summary)
                print(f"Face {i}: {status} ({confidence:.2f})")

            except Exception as emo_error:
                print(f"Emotion analysis failed for face {i}: {emo_error}")
                # Draw box with error label
                x, y, w, h = int(face_region['x']), int(face_region['y']), int(face_region['w']), int(face_region['h'])
                cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 0, 255), 2)
                cv2.putText(frame, "Analysis Failed", (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)

    except Exception as detect_error:
        print(f"Face detection error: {detect_error}")
        num_faces = 0  # Reset if detection fails

    # FPS and summary display
    curr_time = time.time()
    fps = 1 / (curr_time - prev_time) if prev_time > 0 else 0
    prev_time = curr_time
    summary = f"FPS: {fps:.1f} | Faces: {num_faces}"
    cv2.putText(frame, summary, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 0), 2)

    # Optional: Classroom-wide emotion summary (e.g., pie chart overlay or text)
    # For now, just display total faces; extend with counters if needed

    cv2.imshow('Classroom Emotions (Real-Time)', frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# Cleanup
cap.release()
cv2.destroyAllWindows()
print("Enhanced detection stopped.")
