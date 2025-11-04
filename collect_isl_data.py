import cv2
import mediapipe as mp
import pandas as pd
import numpy as np

mp_hands = mp.solutions.hands
hands = mp_hands.Hands(static_image_mode=False, max_num_hands=2)
mp_draw = mp.solutions.drawing_utils

cap = cv2.VideoCapture(0)
data = []
current_label = None
sample_count = 0

print("Press a key (0-9, A-Z) to start collecting samples for that gesture.")
print("Press 'space' to stop collecting for current label.")
print("Press 'ESC' to quit and save CSV.")  # Update message

while True:
    ret, frame = cap.read()
    if not ret:
        break

    frame = cv2.flip(frame, 1)
    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = hands.process(frame_rgb)

    if results.multi_hand_landmarks:
        for hand_landmarks in results.multi_hand_landmarks:
            mp_draw.draw_landmarks(frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)

        if current_label:
            row = []
            for hand_landmarks in results.multi_hand_landmarks:
                for lm in hand_landmarks.landmark:
                    row.extend([lm.x, lm.y, lm.z])
            # Pad with zeros if only one hand detected
            while len(row) < 126:
                row.extend([0.0, 0.0, 0.0])
            row.append(current_label)
            data.append(row)
            sample_count += 1
            cv2.putText(frame, f"Collecting '{current_label}' ({sample_count})", (10, 30),
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

    cv2.imshow("ISL Data Collection", frame)
    key = cv2.waitKey(1) & 0xFF

    if key == 27:
        break
    elif key == 32:
        print(f"Stopped collecting for '{current_label}' with {sample_count} samples.")
        current_label = None
        sample_count = 0
    elif (48 <= key <= 57) or (97 <= key <= 122) or (65 <= key <= 90):  # 0-9 and a-z or A-Z
        current_label = chr(key).upper()
        sample_count = 0
        print(f"Started collecting for '{current_label}'")


cap.release()
cv2.destroyAllWindows()

# Save to CSV
columns = [f"{axis}{i}" for i in range(42) for axis in ['x', 'y', 'z']] + ['label']
df = pd.DataFrame(data, columns=columns)
df.to_csv("isl_landmarks.csv", index=False)
print(f"✅ Saved {len(df)} samples to isl_landmarks.csv")
