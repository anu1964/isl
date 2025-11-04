import pandas as pd

# Load full dataset
df = pd.read_csv("isl_prathum_landmarks.csv")
df.dropna(inplace=True)

# Remove digit labels
df = df[~df["label"].astype(str).str.isdigit()]

# Save new CSV
df.to_csv("isl_letters_only.csv", index=False)
print("✅ Saved letters-only dataset as isl_letters_only.csv")
