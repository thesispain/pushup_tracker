import cv2
import mediapipe as mp
import numpy as np

# 1. The Math Engines
def calculate_angle(a, b, c):
    a = np.array(a)
    b = np.array(b)
    c = np.array(c)
    
    radians = np.arctan2(c[1]-b[1], c[0]-b[0]) - np.arctan2(a[1]-b[1], a[0]-b[0])
    angle = np.abs(radians*180.0/np.pi)
    
    if angle > 180.0:
        angle = 360 - angle
    return angle

def calculate_distance(p1, p2):
    return np.linalg.norm(np.array(p1) - np.array(p2))

# 2. Initialize MediaPipe
mp_pose = mp.solutions.pose
pose = mp_pose.Pose()
mp_draw = mp.solutions.drawing_utils

video_path = "D:/a cse project/push up tracker/video/pushUP2.mp4"
cap = cv2.VideoCapture(video_path)

# --- THE COUNTER VARIABLES ---
count = 0
direction = 0 

while cap.isOpened():
    success, frame = cap.read()
    if not success:
        break
        
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = pose.process(rgb_frame)
    
    if results.pose_landmarks:
        mp_draw.draw_landmarks(frame, results.pose_landmarks, mp_pose.POSE_CONNECTIONS)
        
        # 3. Extract Coordinates 
        landmarks = results.pose_landmarks.landmark
        
        shoulder = [landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER.value].x, landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER.value].y]
        elbow = [landmarks[mp_pose.PoseLandmark.LEFT_ELBOW.value].x, landmarks[mp_pose.PoseLandmark.LEFT_ELBOW.value].y]
        wrist = [landmarks[mp_pose.PoseLandmark.LEFT_WRIST.value].x, landmarks[mp_pose.PoseLandmark.LEFT_WRIST.value].y]
        hip = [landmarks[mp_pose.PoseLandmark.LEFT_HIP.value].x, landmarks[mp_pose.PoseLandmark.LEFT_HIP.value].y]
        nose = [landmarks[mp_pose.PoseLandmark.NOSE.value].x, landmarks[mp_pose.PoseLandmark.NOSE.value].y]
        
        # EXTRACT RIGHT SHOULDER FOR WIDTH!
        right_shoulder = [landmarks[mp_pose.PoseLandmark.RIGHT_SHOULDER.value].x, landmarks[mp_pose.PoseLandmark.RIGHT_SHOULDER.value].y]
        
        # Visibility scores
        shoulder_vis = landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER.value].visibility
        elbow_vis = landmarks[mp_pose.PoseLandmark.LEFT_ELBOW.value].visibility
        wrist_vis = landmarks[mp_pose.PoseLandmark.LEFT_WRIST.value].visibility
        
        # 4. Calculate the live metrics
        angle = calculate_angle(shoulder, elbow, wrist)
        nose_wrist_dist = calculate_distance(nose, wrist)
        
        # --- THE TORSO RATIO FIX ---
        shoulder_width = calculate_distance(shoulder, right_shoulder)
        torso_length = calculate_distance(shoulder, hip)
        
        # Prevent math errors if shoulders overlap exactly
        if shoulder_width == 0: 
            shoulder_width = 0.01 
            
        torso_ratio = torso_length / shoulder_width
        
        # --- THE MASTER STATE MACHINE ---
        
        if shoulder_vis > 0.4 and elbow_vis > 0.4 and wrist_vis > 0.4:
            
            # Check 1: Is the Torso Ratio low enough to be a plank?
            if torso_ratio < 0.85:  
                
                # Check 2: Are they at the bottom? 
                if angle <= 80 and nose_wrist_dist < 0.42:
                    direction = 1 
                
                # Check 3: Did they push back up? 
                if angle >= 160 and nose_wrist_dist < 0.75: 
                    if direction == 1:
                        count += 1
                        direction = 0 
                        
                cv2.putText(frame, f'PUSHUPS: {count}', (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1.5, (0, 255, 0), 3, cv2.LINE_AA)
                
            else:
                # Torso is longer than it is wide. You are standing!
                direction = 0 
                cv2.putText(frame, 'STAND DETECTED', (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 0, 255), 3, cv2.LINE_AA)
        
        else:
            direction = 0
            cv2.putText(frame, 'OUT OF FRAME!', (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 255, 255), 3, cv2.LINE_AA)

        # 5. NEW VISUAL TRACKERS FOR DEBUGGING
        h, w, _ = frame.shape
        elbow_coords = tuple(np.multiply(elbow, [w, h]).astype(int))
        nose_coords = tuple(np.multiply(nose, [w, h]).astype(int))
        
        cv2.putText(frame, f"Angle: {int(angle)}", elbow_coords, cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2, cv2.LINE_AA)
        cv2.putText(frame, f"Dist: {round(nose_wrist_dist, 2)}", (nose_coords[0] - 50, nose_coords[1] - 20), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2, cv2.LINE_AA)
        
        # New Torso Ratio Tracker
        cv2.putText(frame, f"Torso Ratio: {round(torso_ratio, 2)} (Needs < 0.9)", (50, 90), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2, cv2.LINE_AA)
        cv2.putText(frame, f"State: {'BOTTOM' if direction == 1 else 'TOP'}", (50, 120), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2, cv2.LINE_AA)

    cv2.imshow("Pushup Tracker Pro", frame)
    
    if cv2.waitKey(30) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()

print("\n" + "="*30)
print("WORKOUT COMPLETE!")
print(f"FINAL PUSHUP COUNT: {count}")
print("="*30 + "\n")