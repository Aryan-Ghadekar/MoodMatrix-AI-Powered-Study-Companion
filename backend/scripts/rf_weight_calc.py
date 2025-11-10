# =========================================================================================================
# Cognitive Load Prediction using Random Forest Classifier (We can use XGBoost for a Larger Dataset on GPU)
# =========================================================================================================
import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import json
import joblib
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, confusion_matrix, classification_report, ConfusionMatrixDisplay

# -----------------------------
# SETTINGS
# -----------------------------
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "cognitive_load_dataset_csv")

EMOTION_KEYS = ['happy', 'sad', 'angry', 'fear', 'disgust', 'surprise', 'neutral']
OUTPUT_JSON = "emotion_importance.json"
SCALER_FILE = os.path.join("models", "emotion_scaler1.pkl")
MODEL_FILE = os.path.join("models", "rf_cognitive_load_model1.pkl")

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
os.makedirs("models", exist_ok=True)
joblib.dump(scaler, SCALER_FILE)
print(f"[INFO] Saved StandardScaler to: {SCALER_FILE}")

# -----------------------------
# STEP 4: TRAIN RANDOM FOREST CLASSIFIER
# -----------------------------
rf = RandomForestClassifier(
    n_estimators=200,
    random_state=42,
    class_weight='balanced',
    max_depth=8
)
rf.fit(X_scaled, y)
joblib.dump(rf, MODEL_FILE)
print(f"[INFO] Saved Random Forest model to: {MODEL_FILE}")

# -----------------------------
# STEP 5: EVALUATE MODEL
# -----------------------------
y_pred = rf.predict(X_scaled)
accuracy = accuracy_score(y, y_pred)
print(f"\nRandom Forest Model Accuracy: {accuracy * 100:.2f}%")

print("\nClassification Report:")
print(classification_report(y, y_pred, target_names=['Low Load', 'High Load']))

# Confusion matrix visualization
cm = confusion_matrix(y, y_pred)
disp = ConfusionMatrixDisplay(confusion_matrix=cm, display_labels=['Low', 'High'])
disp.plot(cmap='Blues', values_format='d')
plt.title("Confusion Matrix - Cognitive Load Classification")
plt.show()

# -----------------------------
# STEP 6: FEATURE IMPORTANCE (Emotion Influence)
# -----------------------------
importances = rf.feature_importances_
sorted_idx = np.argsort(importances)[::-1]

plt.figure(figsize=(8, 5))
plt.barh(np.array(EMOTION_KEYS)[sorted_idx], importances[sorted_idx], color='skyblue', edgecolor='black')
plt.title("Emotion Importance on Cognitive Load (Random Forest)")
plt.xlabel("Feature Importance Score")
plt.gca().invert_yaxis()
plt.tight_layout()
plt.show()

# Save to JSON for backend use
importance_dict = {emo: float(importance) for emo, importance in zip(EMOTION_KEYS, importances)}
with open(OUTPUT_JSON, "w") as f:
    json.dump(importance_dict, f, indent=4)
print(f"[INFO] Feature importances saved to: {OUTPUT_JSON}")

# -----------------------------
# STEP 7: TEST PREDICTION
# -----------------------------
E = np.array([[0.6, 0.05, 0.1, 0.0, 0.05, 0.1, 0.1]])  # Example emotion probabilities
E_scaled = scaler.transform(E)
CL_pred = rf.predict_proba(E_scaled)[0][1]  # Probability of 'high' load
label = "High" if CL_pred >= 0.5 else "Low"

print(f"\nExample Emotion Input: {E.tolist()[0]}")
print(f"Predicted Cognitive Load: {label} ({CL_pred*100:.2f}% confidence)")

# -----------------------------
# STEP 8: VISUALIZE PREDICTED vs ACTUAL (for probability)
# -----------------------------
y_prob = rf.predict_proba(X_scaled)[:, 1]

plt.figure(figsize=(6,6))
plt.scatter(y, y_prob, color='blue', alpha=0.5)
plt.plot([0,1], [0,1], 'r--')
plt.title("Predicted vs Actual Cognitive Load Probability (Random Forest)")
plt.xlabel("Actual Cognitive Load")
plt.ylabel("Predicted Probability (High Load)")
plt.grid(True, linestyle='--', alpha=0.6)
plt.show()
