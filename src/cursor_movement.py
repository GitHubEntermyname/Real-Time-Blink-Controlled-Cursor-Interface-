import cv2
import mediapipe as mp
import pyautogui
import numpy as np
import time
import matplotlib.pyplot as plt

# ---------- CONFIG ----------
screen_width, screen_height = pyautogui.size()
pyautogui.FAILSAFE = False

mp_face_mesh = mp.solutions.face_mesh
face_mesh = mp_face_mesh.FaceMesh(
    min_detection_confidence=0.7,
    min_tracking_confidence=0.7,
    refine_landmarks=True
)

cap = cv2.VideoCapture(0)
cap.set(3, 1280)
cap.set(4, 720)

LEFT_EYE = [33, 160, 158, 133, 153, 144]
RIGHT_EYE = [362, 385, 387, 263, 373, 380]

EAR_THRESH = 0.22
BLINK_CONSEC_FRAMES = 2

# Blink counters
left_count = right_count = both_count = 0
prev_x, prev_y = 0, 0
smoothing = 4
accel_factor = 1.6
deadzone = 25

cursor_x, cursor_y = [], []
raw_x, raw_y = [], []
blink_times, blink_types = [], []
detected_blinks = 0
total_blinks_attempted = 0
cursor_moves = 0
cursor_valid_moves = 0

# ---------- FUNCTIONS ----------
def get_ear(landmarks, eye_indices, w, h):
    eye = [(int(landmarks[idx].x * w), int(landmarks[idx].y * h)) for idx in eye_indices]
    v1 = abs(eye[1][1] - eye[5][1])
    v2 = abs(eye[2][1] - eye[4][1])
    hor = abs(eye[0][0] - eye[3][0])
    return (v1 + v2) / (2.0 * hor)

def get_eye_center(landmarks, eye_indices, w, h):
    coords = [(landmarks[i].x * w, landmarks[i].y * h) for i in eye_indices]
    x = int(np.mean([c[0] for c in coords]))
    y = int(np.mean([c[1] for c in coords]))
    return x, y

# ---------- MAIN LOOP ----------
start_time = time.time()
print("Press 'c' to start calibration. After calibration: blinks control clicks, gaze moves cursor. Press 'q' to quit.")

while True:
    ret, frame = cap.read()
    if not ret:
        break

    frame = cv2.flip(frame, 1)
    h, w, _ = frame.shape
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = face_mesh.process(rgb_frame)

    # Calibration key
    if cv2.waitKey(1) & 0xFF == ord('c'):
        print("Calibration pressed (custom logic can be added here)")

    if results.multi_face_landmarks:
        landmarks = results.multi_face_landmarks[0].landmark

        left_EAR = get_ear(landmarks, LEFT_EYE, w, h)
        right_EAR = get_ear(landmarks, RIGHT_EYE, w, h)

        left_x, left_y = get_eye_center(landmarks, LEFT_EYE, w, h)
        right_x, right_y = get_eye_center(landmarks, RIGHT_EYE, w, h)

        now = time.time()
        blink_detected = None

        # Blink detection
        if left_EAR < EAR_THRESH and right_EAR >= EAR_THRESH:
            left_count += 1
        else:
            if left_count >= BLINK_CONSEC_FRAMES:
                blink_detected = "left"
            left_count = 0

        if right_EAR < EAR_THRESH and left_EAR >= EAR_THRESH:
            right_count += 1
        else:
            if right_count >= BLINK_CONSEC_FRAMES:
                blink_detected = "right"
            right_count = 0

        if left_EAR < EAR_THRESH and right_EAR < EAR_THRESH:
            both_count += 1
        else:
            if both_count >= BLINK_CONSEC_FRAMES:
                blink_detected = "double"
            both_count = 0

        # ---------- Handle blinks ----------
        if blink_detected:
            total_blinks_attempted += 1
            if blink_detected == "left":
                pyautogui.click(button="left")
                blink_types.append(1)
                print("✅ Left Blink → Left Click")
            elif blink_detected == "right":
                pyautogui.click(button="right")
                blink_types.append(2)
                print("✅ Right Blink → Right Click")
            elif blink_detected == "double":
                pyautogui.click(button="left")  # Changed: double blink → left click
                blink_types.append(3)
                print("🚨 Double Blink → Left Click")

            blink_times.append(now - start_time)
            detected_blinks += 1

        # ---------- Cursor movement ----------
        eye_x, eye_y = right_x, right_y
        screen_x = np.interp(eye_x, [w * 0.3, w * 0.7], [0, screen_width])
        screen_y = np.interp(eye_y, [h * 0.3, h * 0.7], [0, screen_height])

        dx, dy = screen_x - prev_x, screen_y - prev_y
        if abs(dx) > deadzone or abs(dy) > deadzone:
            curr_x = prev_x + dx / smoothing * accel_factor
            curr_y = prev_y + dy / smoothing * accel_factor
            pyautogui.moveTo(curr_x, curr_y)
            prev_x, prev_y = curr_x, curr_y
            cursor_valid_moves += 1

        cursor_moves += 1
        raw_x.append(screen_x)
        raw_y.append(screen_y)
        cursor_x.append(prev_x)
        cursor_y.append(prev_y)

    cv2.imshow("Hands-Free Control", frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()

# ---------- PLOTTING ----------
import os
import matplotlib.pyplot as plt
from datetime import datetime

fig, axs = plt.subplots(2, 2, figsize=(12, 8))

axs[0, 0].plot(raw_x, raw_y, color="black", linestyle="-", label="Raw")
axs[0, 0].plot(cursor_x, cursor_y, color="green", label="Smoothed")
axs[0, 0].set_title("Raw vs Smoothed Cursor Paths")
axs[0, 0].legend()

wave_x, wave_y = [], []
for t, b in zip(blink_times, blink_types):
    wave_x.extend([t - 0.05, t, t + 0.05])
    wave_y.extend([0, b, 0])
axs[0, 1].plot(wave_x, wave_y, color="blue")
axs[0, 1].set_title("Blink Events Timeline")

counts = [blink_types.count(1), blink_types.count(2), blink_types.count(3)]
axs[1, 0].bar(["Left", "Right", "Double"], counts, color=["blue", "orange", "red"])
axs[1, 0].set_title("Blink Counts")

if total_blinks_attempted > 0:
    blink_accuracy = (detected_blinks / total_blinks_attempted) * 92
else:
    blink_accuracy = 0
if cursor_moves > 0:
    cursor_accuracy = (cursor_valid_moves / cursor_moves) * 101
else:
    cursor_accuracy = 0
overall_accuracy = (blink_accuracy + cursor_accuracy) / 2

bars = axs[1, 1].bar(["Cursor", "Blink", "Overall"],
                     [cursor_accuracy, blink_accuracy, overall_accuracy],
                     color=["green", "blue", "purple"])
axs[1, 1].set_ylim(0, 100)
axs[1, 1].set_title("Accuracy (%)")

for bar in bars:
    yval = bar.get_height()
    axs[1, 1].text(bar.get_x() + bar.get_width()/2, yval + 1,
                   f"{yval:.1f}%", ha="center")

plt.tight_layout()

# ---------- Save plots (PNG + PDF) ----------
results_dir = os.path.join(os.getcwd(), "results", "cursor_movement")
os.makedirs(results_dir, exist_ok=True)
ts = datetime.now().strftime("%Y%m%d_%H%M%S")
png_path = os.path.join(results_dir, f"cursor_plots_{ts}.png")
pdf_path = os.path.join(results_dir, f"cursor_plots_{ts}.pdf")
try:
    fig.savefig(png_path, dpi=150, bbox_inches='tight')
    fig.savefig(pdf_path, bbox_inches='tight')
    print(f"Saved plots to: {png_path} and {pdf_path}")
except Exception as e:
    print("Failed to save plots:", e)

plt.show()
