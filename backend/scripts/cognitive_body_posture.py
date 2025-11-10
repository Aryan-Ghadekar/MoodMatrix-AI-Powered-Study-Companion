# Main code for cognitive body posture analysis in a classroom setting

import cv2
import numpy as np
from collections import deque
from ultralytics import YOLO
import mediapipe as mp

# -------------------------------
# Initialize YOLOv8 (person detection)
# -------------------------------
model = YOLO("yolov8n.pt") 

# -------------------------------
# Initialize MediaPipe Pose
# -------------------------------
mp_pose = mp.solutions.pose
mp_drawing = mp.solutions.drawing_utils
pose = mp_pose.Pose(min_detection_confidence=0.5, min_tracking_confidence=0.5)

# -------------------------------
# Helper function
# -------------------------------
def distance(a, b):
    return np.linalg.norm(np.array([a.x, a.y]) - np.array([b.x, b.y]))

# -------------------------------
# Robust Centroid Tracker
# -------------------------------
class CentroidTracker:
    def __init__(self, max_distance=50, max_disappeared=15):
        self.next_id = 0
        self.objects = {}
        self.disappeared = {}
        self.max_distance = max_distance
        self.max_disappeared = max_disappeared
        
    def update(self, boxes):
        new_objects = {}
        input_centroids = [(int((x1+x2)/2), int((y1+y2)/2)) for x1,y1,x2,y2 in boxes]

        if len(self.objects) == 0:
            for centroid in input_centroids:
                new_objects[self.next_id] = centroid
                self.disappeared[self.next_id] = 0
                self.next_id += 1
            self.objects = new_objects
            return list(self.objects.keys())

        object_ids = list(self.objects.keys())
        object_centroids = list(self.objects.values())

        used_rows, used_cols = set(), set()  # always define these

        if input_centroids:
            D = np.linalg.norm(np.array(object_centroids)[:, None] - np.array(input_centroids)[None, :], axis=2)
            rows = D.min(axis=1).argsort()
            cols = D.argmin(axis=1)[rows]

            for row, col in zip(rows, cols):
                if row in used_rows or col in used_cols:
                    continue
                if D[row, col] > self.max_distance:
                    continue
                obj_id = object_ids[row]
                new_objects[obj_id] = input_centroids[col]
                self.disappeared[obj_id] = 0
                used_rows.add(row)
                used_cols.add(col)

            for i, centroid in enumerate(input_centroids):
                if i not in used_cols:
                    new_objects[self.next_id] = centroid
                    self.disappeared[self.next_id] = 0
                    self.next_id += 1

        # Handle disappeared objects
        for i, obj_id in enumerate(object_ids):
            if i not in used_rows:
                self.disappeared[obj_id] += 1
                if self.disappeared[obj_id] <= self.max_disappeared:
                    new_objects[obj_id] = self.objects[obj_id]

        self.objects = new_objects
        return list(self.objects.keys())


tracker = CentroidTracker()

# -------------------------------
# Per-student data
# -------------------------------
student_data = {}  
SMOOTHING_ALPHA = 0.08  
WINDOW_SIZE = 10        

# -------------------------------
# Kalman Filter
# -------------------------------
A = np.array([[1,1],[0,1]])
H = np.array([[1,0]])
Q = np.array([[1e-5,0],[0,1e-4]])
R = np.array([[1e-2]])

def kalman_init():
    return np.array([[0.5],[0.0]]), np.eye(2)

def kalman_update(x,P,measurement):
    x_pred = A @ x
    P_pred = A @ P @ A.T + Q
    y = measurement - H @ x_pred
    S = H @ P_pred @ H.T + R
    K = P_pred @ H.T @ np.linalg.inv(S)
    x_new = x_pred + K @ y
    P_new = (np.eye(2)-K@H)@P_pred
    return x_new, P_new, float(x_new[0])

# -------------------------------
# Cognitive load estimation
# -------------------------------
def estimate_cognitive_load(landmarks, history):
    reasons = []

    L_sh = landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER]
    R_sh = landmarks[mp_pose.PoseLandmark.RIGHT_SHOULDER]
    L_hip = landmarks[mp_pose.PoseLandmark.LEFT_HIP]
    R_hip = landmarks[mp_pose.PoseLandmark.RIGHT_HIP]
    nose = landmarks[mp_pose.PoseLandmark.NOSE]
    L_wrist = landmarks[mp_pose.PoseLandmark.LEFT_WRIST]
    R_wrist = landmarks[mp_pose.PoseLandmark.RIGHT_WRIST]

    shoulder_mid = np.array([(L_sh.x + R_sh.x)/2, (L_sh.y + R_sh.y)/2])
    hip_mid = np.array([(L_hip.x + R_hip.x)/2, (L_hip.y + R_hip.y)/2])
    torso_vector = hip_mid - shoulder_mid
    torso_length = np.linalg.norm(torso_vector) + 1e-6

    slope = (hip_mid[0]-shoulder_mid[0])/torso_length
    slouch_score = np.tanh(abs(slope)/0.15)
    if slouch_score>0.5: reasons.append("Slouching")

    hand_dist_norm = min(distance(L_wrist,nose), distance(R_wrist,nose))/torso_length
    hand_score = np.tanh((0.2-hand_dist_norm)/0.05)
    if hand_score>0.5: reasons.append("Hand near head")

    hand_pos = np.array([L_wrist.x,L_wrist.y,R_wrist.x,R_wrist.y])
    velocity = 0
    if history["hand_history"]:
        velocity = np.linalg.norm(hand_pos - history["hand_history"][-1])
    history["hand_history"].append(hand_pos)
    fidget_score = np.tanh(velocity/0.05)
    if fidget_score>0.5: reasons.append("Fidgeting")

    cl_raw = 0.3*slouch_score + 0.35*hand_score + 0.35*fidget_score
    cl_percent = 100/(1+np.exp(-5*cl_raw))

    prev_smooth = history.get("smoothed_score", cl_percent)
    exp_smooth = SMOOTHING_ALPHA*cl_percent + (1-SMOOTHING_ALPHA)*prev_smooth
    history["smoothed_score"] = exp_smooth

    if "kalman" not in history:
        history["kalman"] = {}
        history["kalman"]["x"], history["kalman"]["P"] = kalman_init()
    x, P = history["kalman"]["x"], history["kalman"]["P"]
    x, P, kalman_smooth = kalman_update(x,P,exp_smooth)
    history["kalman"]["x"], history["kalman"]["P"] = x, P

    if "history" not in history:
        history["history"] = deque(maxlen=WINDOW_SIZE)
    history["history"].append(kalman_smooth)
    final_score = np.mean(history["history"])

    return max(0,min(100,final_score)), reasons

# -------------------------------
# Video capture loop
# -------------------------------
cap = cv2.VideoCapture(0)

while True:
    ret, frame = cap.read()
    if not ret:
        continue  # don't break, keep trying

    results = model.predict(frame)[0]
    boxes = [(int(det.xyxy[0][0]), int(det.xyxy[0][1]), int(det.xyxy[0][2]), int(det.xyxy[0][3]))
             for det in results.boxes if int(det.cls[0])==0]

    student_ids = tracker.update(boxes)
    cl_scores = []

    for i, box in enumerate(boxes):
        student_id = student_ids[i]
        x1,y1,x2,y2 = box
        crop = frame[y1:y2, x1:x2]
        crop_rgb = cv2.cvtColor(crop, cv2.COLOR_BGR2RGB)
        res = pose.process(crop_rgb)

        if res.pose_landmarks:
            if student_id not in student_data:
                student_data[student_id] = {"hand_history": deque(maxlen=30)}

            score, reasons = estimate_cognitive_load(res.pose_landmarks.landmark, student_data[student_id])
            displayed_score = student_data[student_id].get("displayed_score", score)
            displayed_score += 0.05*(score - displayed_score)
            student_data[student_id]["displayed_score"] = displayed_score
            cl_scores.append(displayed_score)

            for lm in res.pose_landmarks.landmark:
                cx = int(lm.x*(x2-x1)+x1)
                cy = int(lm.y*(y2-y1)+y1)
                cv2.circle(frame,(cx,cy),3,(0,255,0),-1)

            reason_text = ", ".join(reasons) if reasons else "Neutral"
            cv2.putText(frame,f"Student {student_id}: {int(displayed_score)}% - {reason_text}",
                        (x1,y1-10),cv2.FONT_HERSHEY_SIMPLEX,1.0,(0,255,0),2)
            cv2.rectangle(frame,(x1,y1),(x2,y2),(255,0,0),2)

    # Overall classroom CL
    if cl_scores:
        overall_cl = int(np.mean(cl_scores))
        color = (0,255,0) if overall_cl<40 else (0,255,255) if overall_cl<70 else (0,0,255)
        cv2.putText(frame,f"Overall Classroom CL: {overall_cl}%",
                    (50,50),cv2.FONT_HERSHEY_SIMPLEX,1.2,color,3)
    else:
        cv2.putText(frame,"No students detected",(50,50),cv2.FONT_HERSHEY_SIMPLEX,1.2,(0,0,255),3)

    cv2.imshow("Classroom Cognitive Load", frame)
    if cv2.waitKey(1) & 0xFF==ord('q'):
        break

cap.release()
cv2.destroyAllWindows()