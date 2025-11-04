import cv2
import mediapipe as mp
import numpy as np
import joblib
import pyttsx3
import time
import threading
from collections import Counter

# Load model trained on letters only
model = joblib.load("isl_letters_only_model.pkl")

# Setup MediaPipe
mp_hands = mp.solutions.hands
hands = mp_hands.Hands(
    static_image_mode=False,
    max_num_hands=2,
    model_complexity=1,
    min_detection_confidence=0.5,
    min_tracking_confidence=0.5
)
mp_draw = mp.solutions.drawing_utils

# Setup speech engine
engine = pyttsx3.init()
engine.setProperty('rate', 150)

# Cooldown and smoothing
last_prediction_time = 0
cooldown = 0.2  # faster prediction
recent_preds = []
last_prediction = None
sentence = ""

# Start webcam
cap = cv2.VideoCapture(0)
print("🎥 Live demo started. Show a gesture!")

while True:
    ret, frame = cap.read()
    if not ret:
        break

    frame = cv2.flip(frame, 1)
    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = hands.process(frame_rgb)

    row = []
    if results.multi_hand_landmarks:
        for hand_landmarks in results.multi_hand_landmarks:
            mp_draw.draw_landmarks(frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)
            for lm in hand_landmarks.landmark:
                row.extend([lm.x, lm.y, lm.z])
        while len(row) < 126:
            row.extend([0.0, 0.0, 0.0])
        row = row[:126]

        # Predict with cooldown
        current_time = time.time()
        if current_time - last_prediction_time > cooldown:
            prediction = model.predict([row])[0]
            recent_preds.append(prediction)
            if len(recent_preds) > 5:  # shorter buffer for faster smoothing
                recent_preds.pop(0)
            smoothed = Counter(recent_preds).most_common(1)[0][0]
            last_prediction = smoothed
            last_prediction_time = current_time
            print(f"👐 Predicted: {smoothed}")

    # Display prediction
    if last_prediction:
        cv2.putText(frame, f"Prediction: {last_prediction}", (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 0), 2)

    # Display sentence
    cv2.putText(frame, f"Sentence: {sentence}", (10, 450),
                cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

    # Key controls
    key = cv2.waitKey(1) & 0xFF
    if key == 27:  # ESC to quit
        break
    elif key == ord('a') and last_prediction:  # Add to sentence
        sentence += last_prediction + " "
        cv2.putText(frame, "✅ Added", (10, 80),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 255), 2)
    elif key == ord('c'):  # Clear sentence
        sentence = ""
    elif key == ord('s') and sentence:  # Speak sentence
        threading.Thread(target=engine.say, args=(sentence,), daemon=True).start()
        threading.Thread(target=engine.runAndWait, daemon=True).start()

    # Show frame
    cv2.imshow("ISL Live Demo", frame)

cap.release()
cv2.destroyAllWindows()
