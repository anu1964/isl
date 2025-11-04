import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, accuracy_score
import joblib

# Load filtered dataset
df = pd.read_csv("isl_prathum_landmarks.csv")
df.dropna(inplace=True)

# Split features and labels
X = df.drop("label", axis=1)
y = df["label"].astype(str).str.upper()

# Confirm shape
print("✅ Feature shape:", X.shape)
print("✅ Unique labels:", sorted(y.unique()))

# Train-test split
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# Train model
model = RandomForestClassifier(n_estimators=100, random_state=42)
model.fit(X_train, y_train)

# Evaluate
y_pred = model.predict(X_test)
print("✅ Accuracy:", accuracy_score(y_test, y_pred))
print("📊 Classification Report:\n", classification_report(y_test, y_pred))

# Save model
joblib.dump(model, "isl_letters_only_model.pkl")
print("✅ Model saved as isl_letters_only_model.pkl")
