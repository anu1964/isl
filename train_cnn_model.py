import os
import cv2
import numpy as np
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Conv2D, MaxPooling2D, Flatten, Dense
from tensorflow.keras.utils import to_categorical
from sklearn.model_selection import train_test_split

# Load data
dataset_path = "Indian/dataset_skeleton"
X, y = [], []
labels = sorted(os.listdir(dataset_path))
label_map = {label: idx for idx, label in enumerate(labels)}

for label in labels:
    folder = os.path.join(dataset_path, label)
    for file in os.listdir(folder):
        img_path = os.path.join(folder, file)
        img = cv2.imread(img_path, cv2.IMREAD_GRAYSCALE)
        img = cv2.resize(img, (64, 64))
        X.append(img)
        y.append(label_map[label])

X = np.array(X).reshape(-1, 64, 64, 1) / 255.0
y = to_categorical(np.array(y))

# Split
X_train, X_val, y_train, y_val = train_test_split(X, y, test_size=0.2)

# Build model
model = Sequential([
    Conv2D(32, (3, 3), activation='relu', input_shape=(64, 64, 1)),
    MaxPooling2D(2, 2),
    Conv2D(64, (3, 3), activation='relu'),
    MaxPooling2D(2, 2),
    Flatten(),
    Dense(128, activation='relu'),
    Dense(len(labels), activation='softmax')
])

model.compile(optimizer='adam', loss='categorical_crossentropy', metrics=['accuracy'])
model.fit(X_train, y_train, validation_data=(X_val, y_val), epochs=10)

# Save model
model.save("Indian/isl_letters_only_model.h5")
print("✅ CNN model saved as isl_letters_only_model.h5")
