import cv2
import mediapipe as mp
import os
import pandas as pd

mp_hands = mp.solutions.hands
hands = mp_hands.Hands(static_image_mode=True, max_num_hands=2)
data = []

base_path = "Indian"  # Update this to match your folder name
for label in os.listdir(base_path):
    print("📂 Found folder:", label)
    folder_path = os.path.join(base_path, label)
    if not os.path.isdir(folder_path):
        continue
    for file in os.listdir(folder_path):
        if not file.lower().endswith((".jpg", ".png")):
            continue
        img_path = os.path.join(folder_path, file)
        image = cv2.imread(img_path)
        if image is None:
            continue
        image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        results = hands.process(image_rgb)

        row = []
        if results.multi_hand_landmarks:
            for hand_landmarks in results.multi_hand_landmarks[:2]:
                for lm in hand_landmarks.landmark:
                    row.extend([lm.x, lm.y, lm.z])
        while len(row) < 126:
            row.extend([0.0, 0.0, 0.0])
        row = row[:126]
        row.append(label.upper())  # Handles both digits and letters
        data.append(row)
    print("✅ Total samples collected:", len(data))


columns = [f"{axis}{i}" for i in range(42) for axis in ['x', 'y', 'z']] + ['label']
df = pd.DataFrame(data, columns=columns)
df.to_csv("isl_prathum_landmarks.csv", index=False)
print("✅ Saved: isl_prathum_landmarks.csv")
