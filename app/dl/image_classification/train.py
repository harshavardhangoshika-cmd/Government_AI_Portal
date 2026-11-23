import os
import json
import numpy as np
import tensorflow as tf
from tensorflow.keras import layers, models
from sklearn.metrics import classification_report, confusion_matrix

# Setup paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATASET_DIR = os.path.join(BASE_DIR, "dataset")
MODEL_DIR = os.path.join(BASE_DIR, "model")
os.makedirs(MODEL_DIR, exist_ok=True)

IMG_SIZE = (224, 224)
BATCH_SIZE = 32
EPOCHS = 8

print("=" * 65)
print("GOVERNMENT COMPLAINT ANALYSIS: CIVIC IMAGE CLASSIFIER TRAINING")
print("=" * 65)
print(f"Dataset directory : {DATASET_DIR}")
print(f"Model output path : {MODEL_DIR}")
print(f"TensorFlow version: {tf.__version__}")

# 1. Load Data with 80/20 train/validation split
print("\nLoading datasets with 80% train / 20% validation split...")
train_ds = tf.keras.utils.image_dataset_from_directory(
    DATASET_DIR,
    validation_split=0.2,
    subset="training",
    seed=42,
    image_size=IMG_SIZE,
    batch_size=BATCH_SIZE,
    label_mode="categorical"
)

val_ds = tf.keras.utils.image_dataset_from_directory(
    DATASET_DIR,
    validation_split=0.2,
    subset="validation",
    seed=42,
    image_size=IMG_SIZE,
    batch_size=BATCH_SIZE,
    label_mode="categorical"
)

class_names = train_ds.class_names
num_classes = len(class_names)
print(f"\nDiscovered {num_classes} classes:")
for idx, name in enumerate(class_names):
    print(f"  [{idx}] {name}")

# Save class label map
label_map = {idx: name for idx, name in enumerate(class_names)}
label_map_file = os.path.join(MODEL_DIR, "class_labels.json")
with open(label_map_file, "w", encoding="utf-8") as f:
    json.dump(label_map, f, indent=2)
print(f"\nSaved class labels mapping to: {label_map_file}")

# Optimize data loading performance
AUTOTUNE = tf.data.AUTOTUNE
train_ds = train_ds.prefetch(buffer_size=AUTOTUNE)
val_ds = val_ds.prefetch(buffer_size=AUTOTUNE)

# 2. Build MobileNetV2 Transfer Learning Architecture
print("\nBuilding MobileNetV2 transfer learning architecture...")
inputs = tf.keras.Input(shape=(224, 224, 3))

# Data Augmentation pipeline
x = layers.RandomFlip("horizontal")(inputs)
x = layers.RandomRotation(0.1)(x)
x = layers.RandomZoom(0.1)(x)

# MobileNetV2 preprocessing: scales pixels to [-1, 1]
x = tf.keras.applications.mobilenet_v2.preprocess_input(x)

# Base Feature Extractor (frozen)
base_model = tf.keras.applications.MobileNetV2(
    input_shape=(224, 224, 3),
    include_top=False,
    weights="imagenet"
)
base_model.trainable = False

x = base_model(x, training=False)
x = layers.GlobalAveragePooling2D()(x)
x = layers.Dropout(0.3)(x)
x = layers.Dense(128, activation="relu")(x)
outputs = layers.Dense(num_classes, activation="softmax")(x)

model = tf.keras.Model(inputs, outputs, name="CivicIssueClassifier_MobileNetV2")

model.compile(
    optimizer=tf.keras.optimizers.Adam(learning_rate=1e-3),
    loss="categorical_crossentropy",
    metrics=["accuracy"]
)

model.summary(line_length=80)

# 3. Model Training
best_model_path = os.path.join(MODEL_DIR, "civic_classifier.keras")

callbacks = [
    tf.keras.callbacks.EarlyStopping(
        monitor="val_accuracy",
        patience=3,
        restore_best_weights=True,
        verbose=1
    ),
    tf.keras.callbacks.ModelCheckpoint(
        filepath=best_model_path,
        monitor="val_accuracy",
        save_best_only=True,
        verbose=1
    )
]

print(f"\nStarting model training for up to {EPOCHS} epochs...")
history = model.fit(
    train_ds,
    validation_data=val_ds,
    epochs=EPOCHS,
    callbacks=callbacks,
    verbose=1
)

# 4. Evaluation and Metrics Computation
print("\n" + "=" * 65)
print("EVALUATING MODEL PERFORMANCE ON VALIDATION DATA")
print("=" * 65)

y_true = []
y_pred = []

for images, labels in val_ds:
    preds = model.predict(images, verbose=0)
    y_true.extend(np.argmax(labels.numpy(), axis=1))
    y_pred.extend(np.argmax(preds, axis=1))

y_true = np.array(y_true)
y_pred = np.array(y_pred)

report = classification_report(y_true, y_pred, target_names=class_names, output_dict=True)
report_text = classification_report(y_true, y_pred, target_names=class_names)
print("\nClassification Report:\n")
print(report_text)

cm = confusion_matrix(y_true, y_pred)
print("Confusion Matrix:\n")
print(cm)

# Save evaluation report
metrics_summary = {
    "total_images": 1512,
    "train_split": len(train_ds) * BATCH_SIZE,
    "val_split": len(val_ds) * BATCH_SIZE,
    "final_train_accuracy": float(history.history["accuracy"][-1]),
    "final_val_accuracy": float(history.history["val_accuracy"][-1]),
    "classification_report": report,
    "confusion_matrix": cm.tolist()
}

metrics_file = os.path.join(MODEL_DIR, "training_metrics.json")
with open(metrics_file, "w", encoding="utf-8") as f:
    json.dump(metrics_summary, f, indent=2)
print(f"\nSaved evaluation metrics to: {metrics_file}")
print("Model training and export complete successfully!")
