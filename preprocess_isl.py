import cv2
import mediapipe as mp
import os

# Paths
input_folder = "dataset_raw"       # Folder with original ISL gesture images
output_folder = "dataset_skeleton" # Folder to save skeleton images

os.makedirs(output_folder, exist_ok=True)

# MediaPipe setup
mp_hands = mp.solutions.hands
hands = mp_hands.Hands(static_image_mode=True, max_num_hands=1)
mp_draw = mp.solutions.drawing_utils

# Loop through each image
for filename in os.listdir(input_folder):
    if filename.endswith(".jpg") or filename.endswith(".png"):
        image_path = os.path.join(input_folder, filename)
        image = cv2.imread(image_path)
        image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        results = hands.process(image_rgb)

        # Create blank canvas
        canvas = 255 * np.ones((200, 200, 3), dtype=np.uint8)

        if results.multi_hand_landmarks:
            for hand_landmarks in results.multi_hand_landmarks:
                mp_draw.draw_landmarks(canvas, hand_landmarks, mp_hands.HAND_CONNECTIONS)

        # Save skeleton image
        save_path = os.path.join(output_folder, filename)
        cv2.imwrite(save_path, canvas)

print("✅ Skeleton images saved to:", output_folder)
