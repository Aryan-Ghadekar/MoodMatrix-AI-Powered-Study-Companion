import cv2
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision
import math
import numpy as np
from collections import deque
import time

class PostureAnalyzer:
    def __init__(self):
        # Posture thresholds
        self.TORSO_ANGLE_THRESHOLD = 15  # degrees from vertical
        self.SHOULDER_ANGLE_THRESHOLD = 10  # degrees from horizontal
        self.HEAD_POSITION_THRESHOLD = 0.15  # ratio of frame height
        self.NECK_ANGLE_THRESHOLD = 20  # degrees from vertical
        
        # Smoothing
        self.angle_history = deque(maxlen=10)
        self.posture_history = deque(maxlen=30)
        
        # Timing
        self.last_alert_time = 0
        self.alert_cooldown = 5  # seconds
        
        # Posture states
        self.good_posture_count = 0
        self.bad_posture_count = 0
        
    def calculate_torso_angle(self, mid_shoulder, mid_hip):
        """Calculate torso angle relative to vertical"""
        dx = mid_hip[0] - mid_shoulder[0]
        dy = mid_hip[1] - mid_shoulder[1]
        if dy == 0:
            return 90.0
        angle = math.degrees(math.atan2(abs(dx), abs(dy)))
        return angle
    
    def calculate_shoulder_angle(self, left_shoulder, right_shoulder):
        """Calculate shoulder angle relative to horizontal"""
        dy = right_shoulder[1] - left_shoulder[1]
        dx = right_shoulder[0] - left_shoulder[0]
        if dx == 0:
            return 90.0
        angle = math.degrees(math.atan2(abs(dy), abs(dx)))
        return angle
    
    def calculate_neck_angle(self, nose, mid_shoulder):
        """Calculate neck angle (head position relative to shoulders)"""
        dx = nose[0] - mid_shoulder[0]
        dy = nose[1] - mid_shoulder[1]
        if dy == 0:
            return 90.0
        angle = math.degrees(math.atan2(abs(dx), abs(dy)))
        return angle
    
    def detect_forward_head(self, nose, mid_shoulder, frame_height):
        """Detect forward head posture"""
        vertical_distance = abs(nose[1] - mid_shoulder[1])
        threshold = frame_height * self.HEAD_POSITION_THRESHOLD
        return vertical_distance > threshold
    
    def analyze_posture_quality(self, landmarks, frame_shape):
        """Comprehensive posture analysis"""
        h, w = frame_shape
        
        # Extract key points
        left_shoulder = (landmarks[11].x * w, landmarks[11].y * h)
        right_shoulder = (landmarks[12].x * w, landmarks[12].y * h)
        left_hip = (landmarks[23].x * w, landmarks[23].y * h)
        right_hip = (landmarks[24].x * w, landmarks[24].y * h)
        nose = (landmarks[0].x * w, landmarks[0].y * h)
        
        # Calculate midpoints
        mid_shoulder = ((left_shoulder[0] + right_shoulder[0]) / 2,
                        (left_shoulder[1] + right_shoulder[1]) / 2)
        mid_hip = ((left_hip[0] + right_hip[0]) / 2,
                   (left_hip[1] + right_hip[1]) / 2)
        
        # Calculate angles
        torso_angle = self.calculate_torso_angle(mid_shoulder, mid_hip)
        shoulder_angle = self.calculate_shoulder_angle(left_shoulder, right_shoulder)
        neck_angle = self.calculate_neck_angle(nose, mid_shoulder)
        
        # Detect issues
        torso_issue = torso_angle > self.TORSO_ANGLE_THRESHOLD
        shoulder_issue = shoulder_angle > self.SHOULDER_ANGLE_THRESHOLD
        neck_issue = neck_angle > self.NECK_ANGLE_THRESHOLD
        forward_head = self.detect_forward_head(nose, mid_shoulder, h)
        
        # Overall posture assessment
        issues = [torso_issue, shoulder_issue, neck_issue, forward_head]
        issue_count = sum(issues)
        
        if issue_count == 0:
            posture_quality = "Excellent"
            color = (0, 255, 0)  # Green
        elif issue_count == 1:
            posture_quality = "Good"
            color = (0, 200, 255)  # Yellow
        elif issue_count == 2:
            posture_quality = "Fair"
            color = (0, 140, 255)  # Orange
        else:
            posture_quality = "Poor"
            color = (0, 0, 255)  # Red
        
        # Update history
        self.angle_history.append(torso_angle)
        self.posture_history.append(issue_count)
        
        return {
            'points': {
                'left_shoulder': left_shoulder,
                'right_shoulder': right_shoulder,
                'left_hip': left_hip,
                'right_hip': right_hip,
                'nose': nose,
                'mid_shoulder': mid_shoulder,
                'mid_hip': mid_hip
            },
            'angles': {
                'torso': torso_angle,
                'shoulder': shoulder_angle,
                'neck': neck_angle
            },
            'issues': {
                'torso_lean': torso_issue,
                'uneven_shoulders': shoulder_issue,
                'neck_bend': neck_issue,
                'forward_head': forward_head
            },
            'quality': posture_quality,
            'color': color,
            'issue_count': issue_count
        }

class PostureVisualizer:
    def __init__(self):
        self.colors = {
            'excellent': (0, 255, 0),
            'good': (0, 200, 255),
            'fair': (0, 140, 255),
            'poor': (0, 0, 255),
            'skeleton': (0, 255, 255),
            'text': (255, 255, 255)
        }
    
    def draw_skeleton(self, image, points):
        """Draw complete posture skeleton"""
        ls = tuple(map(int, points['left_shoulder']))
        rs = tuple(map(int, points['right_shoulder']))
        lh = tuple(map(int, points['left_hip']))
        rh = tuple(map(int, points['right_hip']))
        ms = tuple(map(int, points['mid_shoulder']))
        mh = tuple(map(int, points['mid_hip']))
        nose = tuple(map(int, points['nose']))
        
        # Draw main torso line
        cv2.line(image, ms, mh, self.colors['skeleton'], 3)
        
        # Draw shoulder line
        cv2.line(image, ls, rs, self.colors['skeleton'], 2)
        
        # Draw hip line
        cv2.line(image, lh, rh, self.colors['skeleton'], 2)
        
        # Draw neck line
        cv2.line(image, ms, nose, self.colors['skeleton'], 2)
        
        # Draw points
        for point in [ls, rs, lh, rh, nose]:
            cv2.circle(image, point, 5, self.colors['skeleton'], -1)
    
    def draw_analysis_info(self, image, analysis_result, student_id):
        """Draw comprehensive analysis information"""
        h, w = image.shape[:2]
        points = analysis_result['points']
        angles = analysis_result['angles']
        issues = analysis_result['issues']
        quality = analysis_result['quality']
        color = analysis_result['color']
        
        # Main posture quality indicator
        cv2.putText(image, f"Student {student_id}: {quality} Posture",
                   (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)
        
        # Angle information
        y_offset = 60
        cv2.putText(image, f"Torso: {angles['torso']:.1f}°",
                   (10, y_offset), cv2.FONT_HERSHEY_SIMPLEX, 0.5, self.colors['text'], 1)
        cv2.putText(image, f"Shoulders: {angles['shoulder']:.1f}°",
                   (10, y_offset + 20), cv2.FONT_HERSHEY_SIMPLEX, 0.5, self.colors['text'], 1)
        cv2.putText(image, f"Neck: {angles['neck']:.1f}°",
                   (10, y_offset + 40), cv2.FONT_HERSHEY_SIMPLEX, 0.5, self.colors['text'], 1)
        
        # Issue indicators
        issue_y = y_offset + 70
        issue_count = 0
        
        for issue_name, is_issue in issues.items():
            if is_issue:
                issue_count += 1
                issue_text = issue_name.replace('_', ' ').title()
                cv2.putText(image, f"! {issue_text}",
                           (10, issue_y), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 1)
                issue_y += 20
        
        if issue_count == 0:
            cv2.putText(image, "✓ All postures correct",
                       (10, issue_y), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
        
        # Draw visual guides
        self.draw_visual_guides(image, points, analysis_result['quality'])

    def draw_visual_guides(self, image, points, quality):
        """Draw visual guides for proper posture"""
        ms = tuple(map(int, points['mid_shoulder']))
        mh = tuple(map(int, points['mid_hip']))
        nose = tuple(map(int, points['nose']))
        
        # Draw vertical reference line
        cv2.line(image, (ms[0], ms[1] - 100), (ms[0], mh[1] + 50), 
                (255, 255, 255), 1, cv2.LINE_AA)
        
        # Draw quality indicator circle
        circle_color = self.colors[quality.lower()]
        cv2.circle(image, (image.shape[1] - 30, 30), 15, circle_color, -1)

def main():
    MODEL_PATH = 'models/pose_landmarker_full.task'
    
    # Configuration
    BaseOptions = mp.tasks.BaseOptions
    PoseLandmarker = mp.tasks.vision.PoseLandmarker
    PoseLandmarkerOptions = mp.tasks.vision.PoseLandmarkerOptions
    VisionRunningMode = mp.tasks.vision.RunningMode

    options = PoseLandmarkerOptions(
        base_options=BaseOptions(model_asset_path=MODEL_PATH),
        running_mode=VisionRunningMode.VIDEO,
        num_poses=10,  # Reduced for better performance
        min_pose_detection_confidence=0.7,
        min_pose_presence_confidence=0.7,
        min_tracking_confidence=0.7,
        output_segmentation_masks=False
    )

    # Initialize components
    posture_analyzer = PostureAnalyzer()
    visualizer = PostureVisualizer()
    
    # Statistics
    session_start_time = time.time()
    posture_stats = {i: {'good': 0, 'total': 0} for i in range(10)}

    with PoseLandmarker.create_from_options(options) as landmarker:
        cap = cv2.VideoCapture(0)
        frame_counter = 0
        
        # Set camera resolution for better accuracy
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
        
        print("Starting robust posture detection...")
        print("Posture Quality Indicators:")
        print("• Excellent (Green): No issues detected")
        print("• Good (Yellow): 1 minor issue")
        print("• Fair (Orange): 2 issues")
        print("• Poor (Red): 3+ issues")
        print("Press 'q' to quit")

        while cap.isOpened():
            success, frame = cap.read()
            if not success:
                print("Ignoring empty camera frame.")
                continue

            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_frame)

            timestamp_ms = frame_counter * 33  # ~30 FPS
            result = landmarker.detect_for_video(mp_image, timestamp_ms)
            frame_counter += 1

            annotated_image = frame.copy()
            
            if result.pose_landmarks:
                for idx, landmarks in enumerate(result.pose_landmarks):
                    # Analyze posture
                    analysis = posture_analyzer.analyze_posture_quality(landmarks, frame.shape[:2])
                    
                    # Update statistics
                    posture_stats[idx]['total'] += 1
                    if analysis['issue_count'] <= 1:  # Excellent or Good
                        posture_stats[idx]['good'] += 1
                    
                    # Visualize
                    visualizer.draw_skeleton(annotated_image, analysis['points'])
                    visualizer.draw_analysis_info(annotated_image, analysis, idx + 1)
                    
                    # Display statistics
                    if posture_stats[idx]['total'] > 0:
                        good_percentage = (posture_stats[idx]['good'] / posture_stats[idx]['total']) * 100
                        stats_text = f"Good: {good_percentage:.1f}%"
                        cv2.putText(annotated_image, stats_text,
                                  (10, frame.shape[0] - 10 - (idx * 25)),
                                  cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 255), 1)
            
            # Display overall session statistics
            session_duration = time.time() - session_start_time
            total_students = sum(1 for stats in posture_stats.values() if stats['total'] > 0)
            if total_students > 0:
                overall_good = sum(stats['good'] for stats in posture_stats.values())
                overall_total = sum(stats['total'] for stats in posture_stats.values())
                overall_percentage = (overall_good / overall_total) * 100
                
                cv2.putText(annotated_image, 
                          f"Session: {session_duration:.0f}s | Overall Good: {overall_percentage:.1f}%",
                          (frame.shape[1] - 400, 30),
                          cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)

            cv2.imshow('Robust Posture Detection', annotated_image)

            if cv2.waitKey(5) & 0xFF == ord('q'):
                break

        # Final statistics
        print("\nSession Summary:")
        for idx, stats in posture_stats.items():
            if stats['total'] > 0:
                percentage = (stats['good'] / stats['total']) * 100
                print(f"Student {idx + 1}: {percentage:.1f}% good posture")

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()