# This code is used to calculate the weights of different emotions on cognitive load

import os
import pandas as pd
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import StandardScaler
import numpy as np
import matplotlib.pyplot as plt
import json
import joblib  

# -----------------------------
# SETTINGS
# -----------------------------
DATA_DIR = "cognitive_load_dataset_csv"  # folder with all CSV session files
EMOTION_KEYS = ['happy', 'sad', 'angry', 'fear', 'disgust', 'surprise', 'neutral']
OUTPUT_JSON = "emotion_weights.json"
SCALER_FILE = os.path.join("models", "emotion_scaler.pkl") #Save the scaler for real-time use in models folder

# -----------------------------
# STEP 1: LOAD ALL CSV FILES
# -----------------------------
all_files = [os.path.join(DATA_DIR, f) for f in os.listdir(DATA_DIR) if f.endswith('.csv')]
if not all_files:
    raise FileNotFoundError(f"No CSV files found in {DATA_DIR}")

df_list = [pd.read_csv(file) for file in all_files]
data = pd.concat(df_list, ignore_index=True)
print(f"[INFO] Total frames loaded: {len(data)}")

# -----------------------------
# STEP 2: CLEAN & CONVERT LABELS
# -----------------------------
data['cognitive_load_numeric'] = data['cognitive_load_label'].map({'low': 0, 'high': 1})
data = data.dropna(subset=EMOTION_KEYS + ['cognitive_load_numeric'])

X = data[EMOTION_KEYS].values.astype(float)
y = data['cognitive_load_numeric'].values

# -----------------------------
# STEP 3: STANDARDIZE FEATURES
# -----------------------------
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)
joblib.dump(scaler, SCALER_FILE)  # Save scaler for real-time use
print(f"[INFO] Saved StandardScaler to: {SCALER_FILE}")

# -----------------------------
# STEP 4: FIT LINEAR REGRESSION
# -----------------------------
reg = LinearRegression()
reg.fit(X_scaled, y)

# -----------------------------
# STEP 5: OUTPUT TRUE WEIGHTS
# -----------------------------
W = reg.coef_
intercept = reg.intercept_

print("\nLinear Regression Weights for Emotions (actual, not normalized):")
for emo, weight in zip(EMOTION_KEYS, W):
    print(f"{emo:<10}: {weight:+.5f}")
print(f"\nIntercept (bias term): {intercept:+.5f}")

# -----------------------------
# STEP 6: VISUALIZE IMPORTANCE
# -----------------------------
plt.figure(figsize=(8, 5))
plt.bar(EMOTION_KEYS, W, color='skyblue', edgecolor='black')
plt.title("Emotion Influence on Cognitive Load (Linear Regression Weights)")
plt.xlabel("Emotion")
plt.ylabel("Weight (positive = increases CL, negative = decreases CL)")
plt.axhline(0, color='gray', linestyle='--')
plt.tight_layout()
plt.show()

# -----------------------------
# STEP 7: SAVE WEIGHTS FOR BACKEND USE
# -----------------------------
weights_dict = {emo: float(weight) for emo, weight in zip(EMOTION_KEYS, W)}
weights_dict["intercept"] = float(intercept)

with open(OUTPUT_JSON, "w") as f:
    json.dump(weights_dict, f, indent=4)

print(f"\nWeights saved to: {OUTPUT_JSON}")

# -----------------------------
# STEP 8: TEST PREDICTION
# -----------------------------
E = np.array([[0.6, 0.05, 0.1, 0.0, 0.05, 0.1, 0.1]])  # Example emotion probabilities
E_scaled = scaler.transform(E)
CL_pred = reg.predict(E_scaled)[0]
CL_pred = np.clip(CL_pred, 0, 1)  # bound between 0–1

print(f"\nPredicted cognitive load for example frame: {CL_pred:.3f}")
