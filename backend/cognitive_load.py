import cv2
import mediapipe as mp
import numpy as np
from mediapipe.tasks import python
from mediapipe.tasks.python import vision
from mediapipe.framework.formats import landmark_pb2  

# Initialize MediaPipe drawing utils
mp_drawing = mp.solutions.drawing_utils
mp_drawing_styles = mp.solutions.drawing_styles

# Function to create Pose Landmarker
def create_pose_landmarker():
    base_options = python.BaseOptions(model_asset_path='models/pose_landmarker_heavy.task')
    options = vision.PoseLandmarkerOptions(
        base_options=base_options,
        running_mode=vision.RunningMode.VIDEO,
        num_poses=20,
        min_pose_detection_confidence=0.5,
        min_pose_presence_confidence=0.5,
        min_tracking_confidence=0.5
    )
    return vision.PoseLandmarker.create_from_options(options)

# Function to create Face Landmarker
def create_face_landmarker():
    base_options = python.BaseOptions(model_asset_path='models/face_landmarker.task')
    options = vision.FaceLandmarkerOptions(
        base_options=base_options,
        running_mode=vision.RunningMode.VIDEO,
        num_faces=30,
        min_face_detection_confidence=0.5,
        min_face_presence_confidence=0.5,
        min_tracking_confidence=0.5
    )
    return vision.FaceLandmarker.create_from_options(options)

# Euclidean distance helper
def get_distance(point1, point2):
    return np.linalg.norm(np.array(point1) - np.array(point2))

# Pose score: Slouch detection (inverse of spine length)
def pose_load_score(pose_landmarks):
    if len(pose_landmarks) < 25:  # must have shoulders/hips
        return 0
    left_shoulder = pose_landmarks[11]
    right_shoulder = pose_landmarks[12]
    left_hip = pose_landmarks[23]
    right_hip = pose_landmarks[24]

    shoulder_mid = [(left_shoulder.x + right_shoulder.x) / 2,
                    (left_shoulder.y + right_shoulder.y) / 2]
    hip_mid = [(left_hip.x + right_hip.x) / 2,
               (left_hip.y + right_hip.y) / 2]
    spine_length = get_distance(shoulder_mid, hip_mid)
    return 1 - np.clip(spine_length, 0, 0.5) * 2  # Higher score = more slouch

# Facial emotion score: Eyebrow distance (furrowed brows)
def facial_emotion_score(face_landmarks):
    if len(face_landmarks) < 337: 
        return 0
    left_brow = face_landmarks[107]
    right_brow = face_landmarks[336]
    dist = get_distance((left_brow.x, left_brow.y), (right_brow.x, right_brow.y))
    return 1 - np.clip(dist, 0, 0.05) * 20  # Higher score = more furrow

# Distraction score: Head deviation (nose distance from the center)
def distraction_score(pose_landmarks):
    if len(pose_landmarks) < 1:
        return 0
    nose = pose_landmarks[0]
    deviation = abs(nose.x - 0.5)
    return np.clip(deviation * 10, 0, 1)

# Composite cognitive load (weighted average)
def cognitive_load(pose_landmarks, face_landmarks):
    p_score = pose_load_score(pose_landmarks)
    f_score = facial_emotion_score(face_landmarks)
    d_score = distraction_score(pose_landmarks)
    return 0.4 * p_score + 0.3 * f_score + 0.3 * d_score

def main():
    cap = cv2.VideoCapture(0)
    pose_detector = create_pose_landmarker()
    face_detector = create_face_landmarker()
    timestamp_ms = 0

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        # Convert to MediaPipe Image
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB,
                            data=cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))

        # Detect poses and faces
        pose_result = pose_detector.detect_for_video(mp_image, timestamp_ms)
        face_result = face_detector.detect_for_video(mp_image, timestamp_ms)
        timestamp_ms += 33  # ~30 fps

        annotated_image = frame.copy()

        # Draw poses (convert to protobuf)
        for pose_landmarks in pose_result.pose_landmarks:
            pose_proto = landmark_pb2.NormalizedLandmarkList()
            pose_proto.landmark.extend([
                landmark_pb2.NormalizedLandmark(x=lm.x, y=lm.y, z=lm.z,
                                                visibility=lm.visibility, presence=lm.presence)
                for lm in pose_landmarks
            ])
            mp_drawing.draw_landmarks(
                annotated_image, pose_proto, mp.solutions.pose.POSE_CONNECTIONS,
                landmark_drawing_spec=mp_drawing_styles.get_default_pose_landmarks_style())

        # Draw faces (convert to protobuf)
        for face_landmarks in face_result.face_landmarks:
            face_proto = landmark_pb2.NormalizedLandmarkList()
            face_proto.landmark.extend([
                landmark_pb2.NormalizedLandmark(x=lm.x, y=lm.y, z=lm.z)
                for lm in face_landmarks
            ])
            mp_drawing.draw_landmarks(
                annotated_image, face_proto, mp.solutions.face_mesh.FACEMESH_TESSELATION,
                landmark_drawing_spec=mp_drawing_styles.get_default_face_mesh_tesselation_style())

        # Compute cognitive load for matched students
        num_students = min(len(pose_result.pose_landmarks), len(face_result.face_landmarks))
        for i in range(num_students):
            load = cognitive_load(pose_result.pose_landmarks[i], face_result.face_landmarks[i])
            nose = pose_result.pose_landmarks[i][0]  # first point = nose
            print(f"Student {i+1}: Pose={pose_load_score(pose_result.pose_landmarks[i]):.2f}, "
                  f"Emotion={facial_emotion_score(face_result.face_landmarks[i]):.2f}, "
                  f"Distraction={distraction_score(pose_result.pose_landmarks[i]):.2f}, "
                  f"CognitiveLoad={load:.2f}")

            cv2.putText(annotated_image, f'Student {i+1}: {load:.2f}',
                        (int(nose.x * frame.shape[1]), int(nose.y * frame.shape[0]) - 20),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1, cv2.LINE_AA)

        cv2.imshow('Cognitive Load Estimation (Multi-Student)', annotated_image)
        if cv2.waitKey(5) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()

if __name__ == '__main__':
    main()
