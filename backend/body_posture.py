# import cv2
# import mediapipe as mp
# from mediapipe.tasks import python
# from mediapipe.tasks.python import vision
# import math
# import numpy as np
# from collections import deque
# import time

# class PostureAnalyzer:
#     def __init__(self):
#         # Posture thresholds
#         self.TORSO_ANGLE_THRESHOLD = 15  # degrees from vertical
#         self.SHOULDER_ANGLE_THRESHOLD = 10  # degrees from horizontal
#         self.HEAD_POSITION_THRESHOLD = 0.15  # ratio of frame height
#         self.NECK_ANGLE_THRESHOLD = 20  # degrees from vertical
        
#         # Smoothing
#         self.angle_history = deque(maxlen=10)
#         self.posture_history = deque(maxlen=30)
        
#         # Timing
#         self.last_alert_time = 0
#         self.alert_cooldown = 5  # seconds
        
#         # Posture states
#         self.good_posture_count = 0
#         self.bad_posture_count = 0
        
#     def calculate_torso_angle(self, mid_shoulder, mid_hip):
#         """Calculate torso angle relative to vertical"""
#         dx = mid_hip[0] - mid_shoulder[0]
#         dy = mid_hip[1] - mid_shoulder[1]
#         if dy == 0:
#             return 90.0
#         angle = math.degrees(math.atan2(abs(dx), abs(dy)))
#         return angle
    
#     def calculate_shoulder_angle(self, left_shoulder, right_shoulder):
#         """Calculate shoulder angle relative to horizontal"""
#         dy = right_shoulder[1] - left_shoulder[1]
#         dx = right_shoulder[0] - left_shoulder[0]
#         if dx == 0:
#             return 90.0
#         angle = math.degrees(math.atan2(abs(dy), abs(dx)))
#         return angle
    
#     def calculate_neck_angle(self, nose, mid_shoulder):
#         """Calculate neck angle (head position relative to shoulders)"""
#         dx = nose[0] - mid_shoulder[0]
#         dy = nose[1] - mid_shoulder[1]
#         if dy == 0:
#             return 90.0
#         angle = math.degrees(math.atan2(abs(dx), abs(dy)))
#         return angle
    
#     def detect_forward_head(self, nose, mid_shoulder, frame_height):
#         """Detect forward head posture"""
#         vertical_distance = abs(nose[1] - mid_shoulder[1])
#         threshold = frame_height * self.HEAD_POSITION_THRESHOLD
#         return vertical_distance > threshold
    
#     def analyze_posture_quality(self, landmarks, frame_shape):
#         """Comprehensive posture analysis"""
#         h, w = frame_shape
        
#         # Extract key points
#         left_shoulder = (landmarks[11].x * w, landmarks[11].y * h)
#         right_shoulder = (landmarks[12].x * w, landmarks[12].y * h)
#         left_hip = (landmarks[23].x * w, landmarks[23].y * h)
#         right_hip = (landmarks[24].x * w, landmarks[24].y * h)
#         nose = (landmarks[0].x * w, landmarks[0].y * h)
        
#         # Calculate midpoints
#         mid_shoulder = ((left_shoulder[0] + right_shoulder[0]) / 2,
#                         (left_shoulder[1] + right_shoulder[1]) / 2)
#         mid_hip = ((left_hip[0] + right_hip[0]) / 2,
#                    (left_hip[1] + right_hip[1]) / 2)
        
#         # Calculate angles
#         torso_angle = self.calculate_torso_angle(mid_shoulder, mid_hip)
#         shoulder_angle = self.calculate_shoulder_angle(left_shoulder, right_shoulder)
#         neck_angle = self.calculate_neck_angle(nose, mid_shoulder)
        
#         # Detect issues
#         torso_issue = torso_angle > self.TORSO_ANGLE_THRESHOLD
#         shoulder_issue = shoulder_angle > self.SHOULDER_ANGLE_THRESHOLD
#         neck_issue = neck_angle > self.NECK_ANGLE_THRESHOLD
#         forward_head = self.detect_forward_head(nose, mid_shoulder, h)
        
#         # Overall posture assessment
#         issues = [torso_issue, shoulder_issue, neck_issue, forward_head]
#         issue_count = sum(issues)
        
#         if issue_count == 0:
#             posture_quality = "Excellent"
#             color = (0, 255, 0)  # Green
#         elif issue_count == 1:
#             posture_quality = "Good"
#             color = (0, 200, 255)  # Yellow
#         elif issue_count == 2:
#             posture_quality = "Fair"
#             color = (0, 140, 255)  # Orange
#         else:
#             posture_quality = "Poor"
#             color = (0, 0, 255)  # Red
        
#         # Update history
#         self.angle_history.append(torso_angle)
#         self.posture_history.append(issue_count)
        
#         return {
#             'points': {
#                 'left_shoulder': left_shoulder,
#                 'right_shoulder': right_shoulder,
#                 'left_hip': left_hip,
#                 'right_hip': right_hip,
#                 'nose': nose,
#                 'mid_shoulder': mid_shoulder,
#                 'mid_hip': mid_hip
#             },
#             'angles': {
#                 'torso': torso_angle,
#                 'shoulder': shoulder_angle,
#                 'neck': neck_angle
#             },
#             'issues': {
#                 'torso_lean': torso_issue,
#                 'uneven_shoulders': shoulder_issue,
#                 'neck_bend': neck_issue,
#                 'forward_head': forward_head
#             },
#             'quality': posture_quality,
#             'color': color,
#             'issue_count': issue_count
#         }

# class PostureVisualizer:
#     def __init__(self):
#         self.colors = {
#             'excellent': (0, 255, 0),
#             'good': (0, 200, 255),
#             'fair': (0, 140, 255),
#             'poor': (0, 0, 255),
#             'skeleton': (0, 255, 255),
#             'text': (255, 255, 255)
#         }
    
#     def draw_skeleton(self, image, points):
#         """Draw complete posture skeleton"""
#         ls = tuple(map(int, points['left_shoulder']))
#         rs = tuple(map(int, points['right_shoulder']))
#         lh = tuple(map(int, points['left_hip']))
#         rh = tuple(map(int, points['right_hip']))
#         ms = tuple(map(int, points['mid_shoulder']))
#         mh = tuple(map(int, points['mid_hip']))
#         nose = tuple(map(int, points['nose']))
        
#         # Draw main torso line
#         cv2.line(image, ms, mh, self.colors['skeleton'], 3)
        
#         # Draw shoulder line
#         cv2.line(image, ls, rs, self.colors['skeleton'], 2)
        
#         # Draw hip line
#         cv2.line(image, lh, rh, self.colors['skeleton'], 2)
        
#         # Draw neck line
#         cv2.line(image, ms, nose, self.colors['skeleton'], 2)
        
#         # Draw points
#         for point in [ls, rs, lh, rh, nose]:
#             cv2.circle(image, point, 5, self.colors['skeleton'], -1)
    
#     def draw_analysis_info(self, image, analysis_result, student_id):
#         """Draw comprehensive analysis information"""
#         h, w = image.shape[:2]
#         points = analysis_result['points']
#         angles = analysis_result['angles']
#         issues = analysis_result['issues']
#         quality = analysis_result['quality']
#         color = analysis_result['color']
        
#         # Main posture quality indicator
#         cv2.putText(image, f"Student {student_id}: {quality} Posture",
#                    (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)
        
#         # Angle information
#         y_offset = 60
#         cv2.putText(image, f"Torso: {angles['torso']:.1f}°",
#                    (10, y_offset), cv2.FONT_HERSHEY_SIMPLEX, 0.5, self.colors['text'], 1)
#         cv2.putText(image, f"Shoulders: {angles['shoulder']:.1f}°",
#                    (10, y_offset + 20), cv2.FONT_HERSHEY_SIMPLEX, 0.5, self.colors['text'], 1)
#         cv2.putText(image, f"Neck: {angles['neck']:.1f}°",
#                    (10, y_offset + 40), cv2.FONT_HERSHEY_SIMPLEX, 0.5, self.colors['text'], 1)
        
#         # Issue indicators
#         issue_y = y_offset + 70
#         issue_count = 0
        
#         for issue_name, is_issue in issues.items():
#             if is_issue:
#                 issue_count += 1
#                 issue_text = issue_name.replace('_', ' ').title()
#                 cv2.putText(image, f"! {issue_text}",
#                            (10, issue_y), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 1)
#                 issue_y += 20
        
#         if issue_count == 0:
#             cv2.putText(image, "✓ All postures correct",
#                        (10, issue_y), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
        
#         # Draw visual guides
#         self.draw_visual_guides(image, points, analysis_result['quality'])

#     def draw_visual_guides(self, image, points, quality):
#         """Draw visual guides for proper posture"""
#         ms = tuple(map(int, points['mid_shoulder']))
#         mh = tuple(map(int, points['mid_hip']))
#         nose = tuple(map(int, points['nose']))
        
#         # Draw vertical reference line
#         cv2.line(image, (ms[0], ms[1] - 100), (ms[0], mh[1] + 50), 
#                 (255, 255, 255), 1, cv2.LINE_AA)
        
#         # Draw quality indicator circle
#         circle_color = self.colors[quality.lower()]
#         cv2.circle(image, (image.shape[1] - 30, 30), 15, circle_color, -1)

# def main():
#     MODEL_PATH = 'models/pose_landmarker_full.task'
    
#     # Configuration
#     BaseOptions = mp.tasks.BaseOptions
#     PoseLandmarker = mp.tasks.vision.PoseLandmarker
#     PoseLandmarkerOptions = mp.tasks.vision.PoseLandmarkerOptions
#     VisionRunningMode = mp.tasks.vision.RunningMode

#     options = PoseLandmarkerOptions(
#         base_options=BaseOptions(model_asset_path=MODEL_PATH),
#         running_mode=VisionRunningMode.VIDEO,
#         num_poses=10,  # Reduced for better performance
#         min_pose_detection_confidence=0.7,
#         min_pose_presence_confidence=0.7,
#         min_tracking_confidence=0.7,
#         output_segmentation_masks=False
#     )

#     # Initialize components
#     posture_analyzer = PostureAnalyzer()
#     visualizer = PostureVisualizer()
    
#     # Statistics
#     session_start_time = time.time()
#     posture_stats = {i: {'good': 0, 'total': 0} for i in range(10)}

#     with PoseLandmarker.create_from_options(options) as landmarker:
#         cap = cv2.VideoCapture(0)
#         frame_counter = 0
        
#         # Set camera resolution for better accuracy
#         cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
#         cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
        
#         print("Starting robust posture detection...")
#         print("Posture Quality Indicators:")
#         print("• Excellent (Green): No issues detected")
#         print("• Good (Yellow): 1 minor issue")
#         print("• Fair (Orange): 2 issues")
#         print("• Poor (Red): 3+ issues")
#         print("Press 'q' to quit")

#         while cap.isOpened():
#             success, frame = cap.read()
#             if not success:
#                 print("Ignoring empty camera frame.")
#                 continue

#             rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
#             mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_frame)

#             timestamp_ms = frame_counter * 33  # ~30 FPS
#             result = landmarker.detect_for_video(mp_image, timestamp_ms)
#             frame_counter += 1

#             annotated_image = frame.copy()
            
#             if result.pose_landmarks:
#                 for idx, landmarks in enumerate(result.pose_landmarks):
#                     # Analyze posture
#                     analysis = posture_analyzer.analyze_posture_quality(landmarks, frame.shape[:2])
                    
#                     # Update statistics
#                     posture_stats[idx]['total'] += 1
#                     if analysis['issue_count'] <= 1:  # Excellent or Good
#                         posture_stats[idx]['good'] += 1
                    
#                     # Visualize
#                     visualizer.draw_skeleton(annotated_image, analysis['points'])
#                     visualizer.draw_analysis_info(annotated_image, analysis, idx + 1)
                    
#                     # Display statistics
#                     if posture_stats[idx]['total'] > 0:
#                         good_percentage = (posture_stats[idx]['good'] / posture_stats[idx]['total']) * 100
#                         stats_text = f"Good: {good_percentage:.1f}%"
#                         cv2.putText(annotated_image, stats_text,
#                                   (10, frame.shape[0] - 10 - (idx * 25)),
#                                   cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 255), 1)
            
#             # Display overall session statistics
#             session_duration = time.time() - session_start_time
#             total_students = sum(1 for stats in posture_stats.values() if stats['total'] > 0)
#             if total_students > 0:
#                 overall_good = sum(stats['good'] for stats in posture_stats.values())
#                 overall_total = sum(stats['total'] for stats in posture_stats.values())
#                 overall_percentage = (overall_good / overall_total) * 100
                
#                 cv2.putText(annotated_image, 
#                           f"Session: {session_duration:.0f}s | Overall Good: {overall_percentage:.1f}%",
#                           (frame.shape[1] - 400, 30),
#                           cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)

#             cv2.imshow('Robust Posture Detection', annotated_image)

#             if cv2.waitKey(5) & 0xFF == ord('q'):
#                 break

#         # Final statistics
#         print("\nSession Summary:")
#         for idx, stats in posture_stats.items():
#             if stats['total'] > 0:
#                 percentage = (stats['good'] / stats['total']) * 100
#                 print(f"Student {idx + 1}: {percentage:.1f}% good posture")

#     cap.release()
#     cv2.destroyAllWindows()

# if __name__ == "__main__":
#     main()


# -------------------------------------------------------------------------
# Alternate Solution for cognitive load calculation based on body posture
# -------------------------------------------------------------------------

import cv2
import numpy as np
import mediapipe as mp
import time

mp_drawing = mp.solutions.drawing_utils
mp_pose = mp.solutions.pose


class MoodMatrixPose:
    def __init__(self, smoothing_factor=0.95):
        self.prev_CL = 0.5  # start with moderate load
        self.beta = smoothing_factor
        self.posture_history = []

    def analyze_posture_quality(self, results):
        landmarks = results.pose_landmarks.landmark

        # --- Extract important points ---
        shoulder_left = landmarks[11]
        shoulder_right = landmarks[12]
        hip_left = landmarks[23]
        hip_right = landmarks[24]
        nose = landmarks[0]

        # --- 1. Spine angle ---
        shoulder_mid_y = (shoulder_left.y + shoulder_right.y) / 2
        hip_mid_y = (hip_left.y + hip_right.y) / 2
        torso_angle = abs(shoulder_mid_y - hip_mid_y) * 100  # normalized approx

        # --- 2. Head tilt ---
        neck_angle = abs(nose.x - ((shoulder_left.x + shoulder_right.x) / 2)) * 100

        # --- 3. Store for fidget detection ---
        self.posture_history.append(torso_angle)
        if len(self.posture_history) > 30:  # keep last 30 frames (~1 sec)
            self.posture_history.pop(0)

        # --- 4. Posture issue detection ---
        issue_count = 0
        issues = {
            "Slouching": torso_angle > 25,
            "Head Tilt": neck_angle > 20
        }
        issue_count += sum(issues.values())

        # --- 5. Posture quality ---
        if issue_count == 0:
            posture_quality = "Good"
            color = (0, 255, 0)
        elif issue_count == 1:
            posture_quality = "Moderate"
            color = (0, 255, 255)
        else:
            posture_quality = "Poor"
            color = (0, 0, 255)

        # ---------------- Cognitive Load Calculation ----------------
        # Normalize spine deviation (S) and head tilt (H)
        S = min(torso_angle / 45.0, 1.0)       # 0–1
        H = min(neck_angle / 40.0, 1.0)        # 0–1

        # Fidget score (F): based on posture changes
        if len(self.posture_history) >= 2:
            fidget_score = np.std(self.posture_history) / 3.0  # scaled to 0–1
        else:
            fidget_score = 0.0
        F = min(fidget_score, 1.0)

        # Pose confidence (Cp)
        key_indices = [11, 12, 23, 24]  # shoulders & hips
        Cp = np.mean([landmarks[i].visibility for i in key_indices])
        Cp = np.clip(Cp, 0, 1)

        # Raw cognitive load based on posture
        CL_raw = (0.4 * S + 0.4 * H + 0.2 * F) * Cp

        # Exponential smoothing
        CL_smooth = self.beta * self.prev_CL + (1 - self.beta) * CL_raw
        self.prev_CL = CL_smooth

        return {
            'points': {
                'shoulder_mid_y': shoulder_mid_y,
                'hip_mid_y': hip_mid_y,
                'nose_x': nose.x
            },
            'angles': {
                'torso_angle': torso_angle,
                'neck_angle': neck_angle
            },
            'issues': issues,
            'quality': posture_quality,
            'color': color,
            'issue_count': issue_count,
            'cognitive_load': {
                'raw': CL_raw,
                'smooth': CL_smooth
            }
        }


# ------------------- Main Execution -------------------
pose_tracker = MoodMatrixPose(smoothing_factor=0.9)

cap = cv2.VideoCapture(0)
prev_time = time.time()
display_interval = 2.5  # seconds between cognitive load updates
last_display_load = 0

with mp_pose.Pose(min_detection_confidence=0.5, min_tracking_confidence=0.5) as pose:
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        frame = cv2.flip(frame, 1)
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = pose.process(rgb)

        if results.pose_landmarks:
            data = pose_tracker.analyze_posture_quality(results)
            mp_drawing.draw_landmarks(
                frame, results.pose_landmarks, mp_pose.POSE_CONNECTIONS)

            # Update display every few seconds for stability
            current_time = time.time()
            if current_time - prev_time > display_interval:
                last_display_load = data['cognitive_load']['smooth']
                prev_time = current_time

            CL_percent = round(last_display_load * 100, 2)
            quality = data['quality']

            cv2.putText(frame, f"Posture: {quality}", (30, 50),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.8, data['color'], 2)
            cv2.putText(frame, f"Cognitive Load: {CL_percent}%", (30, 90),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)

        cv2.imshow('MoodMatrix Pose-Based Cognitive Load', frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

cap.release()
cv2.destroyAllWindows()