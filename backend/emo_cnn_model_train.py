import os
# Set environment variable for memory growth before any TF import
os.environ['TF_FORCE_GPU_ALLOW_GROWTH'] = 'true'

import tensorflow as tf
from tensorflow.keras import mixed_precision
from tensorflow.keras.applications import EfficientNetB0
from tensorflow.keras.layers import Dense, GlobalAveragePooling2D, Dropout, Rescaling, RandomRotation, RandomFlip, RandomZoom, RandomContrast
from tensorflow.keras.models import Model, Sequential
from sklearn.utils.class_weight import compute_class_weight  # Keep for verification if needed
from sklearn.metrics import classification_report, confusion_matrix
from google.colab import files

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# =============================
# GPU Detection and Configuration
# =============================
physical_gpus = tf.config.list_physical_devices('GPU')
logical_gpus = tf.config.list_logical_devices('GPU')
print(f"Physical GPUs: {len(physical_gpus)}, Logical GPUs: {len(logical_gpus)}")

if physical_gpus:
    try:
        for gpu in physical_gpus:
            tf.config.experimental.set_memory_growth(gpu, True)
        print("GPU memory growth enabled successfully; training will use GPU.")
    except RuntimeError as e:
        print(f"Could not enable memory growth (already initialized): {e}")
        print("Proceeding with default GPU allocation.")
else:
    print("No GPU detected; training on CPU (slower).")

# Enable mixed precision for speed on GPU
mixed_precision.set_global_policy('mixed_float16')

# =============================
# 1. Paths and Class Names (Early Setup)
# =============================
train_dir = "/content/drive/MyDrive/FER2013/train"
val_dir = "/content/drive/MyDrive/FER2013/test"

img_size = 224
batch_size = 64
num_classes = 7

# Derive class names from directory structure (avoids dataset loading)
class_names = sorted([d for d in os.listdir(train_dir) if os.path.isdir(os.path.join(train_dir, d))])
print(f"Class names: {class_names}")

# =============================
# 2. Compute Class Weights (ULTRA-FAST: Directory-based, no dataset loading)
# =============================
print("Computing class weights...")

train_class_counts = {}
for class_name in class_names:
    class_dir = os.path.join(train_dir, class_name)
    if os.path.exists(class_dir):
        files_in_dir = [f for f in os.listdir(class_dir) if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
        train_class_counts[class_name] = len(files_in_dir)
    else:
        train_class_counts[class_name] = 0

total_samples = sum(train_class_counts.values())
print(f"Class distribution: {train_class_counts} (Total: {total_samples})")

# Map class names to indices
class_to_idx = {name: idx for idx, name in enumerate(class_names)}

# Compute balanced weights (direct formula, equivalent to sklearn)
class_weights = {}
for class_name, count in train_class_counts.items():
    if count > 0:
        weight = total_samples / (num_classes * count)
        class_weights[class_to_idx[class_name]] = weight
    else:
        class_weights[class_to_idx[class_name]] = 1.0  # Default for empty classes

print("Class weights computed:", class_weights)

# =============================
# 3. Data Preprocessing with tf.data (Parallel Loading)
# =============================
AUTOTUNE = tf.data.AUTOTUNE

# Load datasets with grayscale mode (FER2013 is grayscale; stack to RGB in preprocess)
train_ds = tf.keras.utils.image_dataset_from_directory(
    train_dir,
    image_size=(img_size, img_size),
    color_mode='grayscale',  # Load as (H,W,1) to match FER2013
    batch_size=batch_size,
    label_mode='int',
    shuffle=True,
    seed=42
)

val_ds = tf.keras.utils.image_dataset_from_directory(
    val_dir,
    image_size=(img_size, img_size),
    color_mode='grayscale',
    batch_size=batch_size,
    label_mode='int',
    shuffle=False,
    seed=42
)

# Augmentation layer for training
augmentation_layer = Sequential([
    RandomRotation(0.1, fill_mode='nearest'),
    RandomFlip("horizontal"),
    RandomZoom(0.2),
    RandomContrast(0.2),
    Rescaling(1./255)
], name='augmentation')

# Fixed preprocess functions: Use tf.cond for conditional stacking (graph-compatible)
def preprocess_train(image, label):
    # Stack grayscale (H,W,1) to RGB (H,W,3)
    image = tf.cond(
        tf.shape(image)[-1] == 1,
        lambda: tf.repeat(image, 3, axis=-1),
        lambda: image
    )
    # Resize and augment
    image = tf.image.resize(image, [img_size, img_size])
    image = augmentation_layer(image, training=True)
    return image, label

def preprocess_val(image, label):
    # Stack grayscale to RGB
    image = tf.cond(
        tf.shape(image)[-1] == 1,
        lambda: tf.repeat(image, 3, axis=-1),
        lambda: image
    )
    # Resize and normalize
    image = tf.image.resize(image, [img_size, img_size])
    image = image / 255.0
    return image, label

# Apply preprocessing
train_ds_processed = train_ds.map(preprocess_train, num_parallel_calls=AUTOTUNE)
val_ds_processed = val_ds.map(preprocess_val, num_parallel_calls=AUTOTUNE)

# One-hot encode labels
train_ds_processed = train_ds_processed.map(lambda x, y: (x, tf.one_hot(y, num_classes)), num_parallel_calls=AUTOTUNE)
val_ds_processed = val_ds_processed.map(lambda x, y: (x, tf.one_hot(y, num_classes)), num_parallel_calls=AUTOTUNE)

# Optimize datasets (cache after map to avoid I/O during training)
train_ds_final = train_ds_processed.cache().shuffle(1000).prefetch(AUTOTUNE)  # Added shuffle post-cache for better mixing
val_ds_final = val_ds_processed.cache().prefetch(AUTOTUNE)

print("Datasets prepared successfully.")

# =============================
# 4. Build EfficientNet-B0
# =============================
print("Building model...")
base_model = EfficientNetB0(weights="imagenet", include_top=False, input_shape=(img_size, img_size, 3))
base_model.trainable = False

x = base_model.output
x = GlobalAveragePooling2D()(x)
x = Dropout(0.3)(x)
predictions = Dense(num_classes, activation="softmax", dtype='float32')(x)

model = Model(inputs=base_model.input, outputs=predictions)

model.compile(optimizer=tf.keras.optimizers.Adam(1e-3),
              loss="categorical_crossentropy",
              metrics=["accuracy"])

model.summary()

# =============================
# 5. Training
# =============================
callbacks = [
    tf.keras.callbacks.EarlyStopping(monitor='val_loss', patience=5, restore_best_weights=True),
    tf.keras.callbacks.ModelCheckpoint("efficientnet_fer.h5", monitor='val_loss', save_best_only=True),
    tf.keras.callbacks.ReduceLROnPlateau(monitor='val_loss', factor=0.5, patience=3, min_lr=1e-7)
]

print("Starting initial training...")
history = model.fit(
    train_ds_final,
    validation_data=val_ds_final,
    epochs=20,
    class_weight=class_weights,
    callbacks=callbacks,
    verbose=1
)

# =============================
# 6. Fine-tune (Unfreeze some layers)
# =============================
print("Starting fine-tuning...")
base_model.trainable = True

# Fine-tune from this layer onwards
fine_tune_at = len(base_model.layers) // 2

for layer in base_model.layers[:fine_tune_at]:
    layer.trainable = False

print(f"Fine-tuning {len(base_model.layers) - fine_tune_at} layers out of {len(base_model.layers)} total layers")

# Recompile with lower learning rate
model.compile(optimizer=tf.keras.optimizers.Adam(1e-5),
              loss="categorical_crossentropy", 
              metrics=["accuracy"])

# Update callbacks for fine-tuning
finetune_callbacks = [
    tf.keras.callbacks.EarlyStopping(monitor='val_loss', patience=5, restore_best_weights=True),
    tf.keras.callbacks.ModelCheckpoint("efficientnet_fer_finetuned.h5", monitor='val_loss', save_best_only=True),
    tf.keras.callbacks.ReduceLROnPlateau(monitor='val_loss', factor=0.5, patience=3, min_lr=1e-7)
]

history_finetune = model.fit(
    train_ds_final,
    validation_data=val_ds_final,
    epochs=30,
    class_weight=class_weights,
    callbacks=finetune_callbacks,
    verbose=1
)

# =============================
# 7. Save Final Model
# =============================
print("Saving model...")
model.save("efficientnet_fer_final.h5")
print("Model saved successfully.")

# =============================
# 8. Evaluate Model
# =============================
print("Evaluating model...")
val_preds = model.predict(val_ds_final, verbose=1)
y_pred = np.argmax(val_preds, axis=1)

# Extract true labels from validation set (raw int labels)
y_true = []
for _, labels in val_ds:  # Raw val_ds (int labels, no one-hot)
    y_true.extend(labels.numpy())
y_true = np.array(y_true)

# Use actual emotion labels
emotion_labels = class_names

# Classification report
report = classification_report(y_true, y_pred, target_names=emotion_labels, output_dict=True)
report_df = pd.DataFrame(report).transpose()
report_df.to_csv("classification_report.csv", index=True)

# Confusion matrix
cm = confusion_matrix(y_true, y_pred)
cm_df = pd.DataFrame(cm, index=emotion_labels, columns=emotion_labels)
cm_df.to_csv("confusion_matrix.csv", index=True)

with open("evaluation_metrics.txt", "w") as f:
    f.write("Classification Report:\n")
    f.write(str(classification_report(y_true, y_pred, target_names=emotion_labels)))
    f.write("\n\nConfusion Matrix:\n")
    f.write(str(cm))

print("Evaluation metrics saved.")

# =============================
# 9. Visualization
# =============================
def plot_history(history, history_finetune):
    # Merge histories (handle potential length differences from EarlyStopping)
    acc = history.history['accuracy'] + history_finetune.history['accuracy']
    val_acc = history.history['val_accuracy'] + history_finetune.history['val_accuracy']
    loss = history.history['loss'] + history_finetune.history['loss']
    val_loss = history.history['val_loss'] + history_finetune.history['val_loss']
    epochs = range(1, len(acc) + 1)

    # Accuracy
    plt.figure(figsize=(8, 6))
    plt.plot(epochs, acc, 'b-', label="Training Accuracy")
    plt.plot(epochs, val_acc, 'r-', label="Validation Accuracy")
    plt.title("Training & Validation Accuracy")
    plt.xlabel("Epochs")
    plt.ylabel("Accuracy")
    plt.legend()
    plt.savefig("training_accuracy.png")
    plt.close()

    # Loss
    plt.figure(figsize=(8, 6))
    plt.plot(epochs, loss, 'b-', label="Training Loss")
    plt.plot(epochs, val_loss, 'r-', label="Validation Loss")
    plt.title("Training & Validation Loss")
    plt.xlabel("Epochs")
    plt.ylabel("Loss")
    plt.legend()
    plt.savefig("training_loss.png")
    plt.close()

# Call plotting
plot_history(history, history_finetune)

# Confusion matrix heatmap
plt.figure(figsize=(10, 8))
sns.heatmap(cm_df, annot=True, fmt="d", cmap="Blues", xticklabels=emotion_labels, yticklabels=emotion_labels)
plt.title("Confusion Matrix")
plt.xlabel("Predicted")
plt.ylabel("True")
plt.tight_layout()
plt.savefig("confusion_matrix.png")
plt.close()

print("Visualizations saved.")

# =============================
# 10. Download Results
# =============================
print("Downloading results...")
files.download("efficientnet_fer_final.h5")
files.download("classification_report.csv")
files.download("confusion_matrix.csv")
files.download("evaluation_metrics.txt")
files.download("training_accuracy.png")
files.download("training_loss.png")
files.download("confusion_matrix.png")

print("All done!")
