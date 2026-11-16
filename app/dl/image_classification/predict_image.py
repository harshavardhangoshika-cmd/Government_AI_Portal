"""
Deep Learning Image Classification Inference Module
===================================================
Classifies civic issue images into 7 municipal complaint categories:
1. road_damage
2. garbage
3. streetlights
4. water_supply
5. electricity
6. traffic_safety
7. sewerage

Uses a fine-tuned MobileNetV2 architecture with high accuracy (~93%).
Provides rich civic metadata (recommended department, SLA, priority).
"""

import os
import json
import io
import numpy as np
from PIL import Image

# Suppress verbose TensorFlow logs during inference
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "2"

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.path.join(BASE_DIR, "model", "civic_classifier.keras")
LABELS_PATH = os.path.join(BASE_DIR, "model", "class_labels.json")

# Cached model instance
_MODEL = None
_CLASS_NAMES = None

# Rich Civic Metadata Mapping for the 7 Complaint Classes
CIVIC_CATEGORY_METADATA = {
    "road_damage": {
        "display_name": "Road Damage / Potholes",
        "department": "BBMP / Municipal Works",
        "complaint_reason": "Mobility - Roads & Infrastructure",
        "priority": "High",
        "estimated_sla_hours": 48,
        "description": "Potholes, cracked asphalt, road collapse, or damaged road surface."
    },
    "garbage": {
        "display_name": "Garbage & Waste Accumulation",
        "department": "Solid Waste Management / BBMP",
        "complaint_reason": "Public Cleanliness / Sanitation",
        "priority": "Medium",
        "estimated_sla_hours": 24,
        "description": "Garbage piles, roadside litter, overflowing dumpsters, or plastic waste."
    },
    "streetlights": {
        "display_name": "Streetlight Malfunction / Dark Spot",
        "department": "BESCOM / Municipal Electrical Works",
        "complaint_reason": "Street Lighting & Electrical",
        "priority": "Medium",
        "estimated_sla_hours": 36,
        "description": "Broken streetlight, dark pathway, damaged lamppost, or non-functional lighting."
    },
    "water_supply": {
        "display_name": "Water Supply Disruption / Pipeline Leak",
        "department": "BWSSB / Sanitation & Water",
        "complaint_reason": "Water Supply & Distribution",
        "priority": "High",
        "estimated_sla_hours": 24,
        "description": "Burst water main, contaminated water, tap water interruption, or pipeline leakage."
    },
    "electricity": {
        "display_name": "Electrical Hazard / Powerline Fault",
        "department": "BESCOM / Power & Electricity",
        "complaint_reason": "Electricity & Power Supply",
        "priority": "Urgent",
        "estimated_sla_hours": 12,
        "description": "Hanging wires, sparking transformer, dangerous power pole, or live cable exposure."
    },
    "traffic_safety": {
        "display_name": "Traffic Safety & Signal Violations",
        "department": "Traffic Police / Transport",
        "complaint_reason": "Traffic & Road Safety",
        "priority": "High",
        "estimated_sla_hours": 24,
        "description": "Damaged traffic signs, malfunctioning signals, road blockage, or safety hazard."
    },
    "sewerage": {
        "display_name": "Sewerage Overflow / Damaged Manhole",
        "department": "BWSSB / Sanitation & Water",
        "complaint_reason": "Drainage & Sewerage",
        "priority": "High",
        "estimated_sla_hours": 24,
        "description": "Broken manhole cover, overflowing sewage, clogged storm drain, or hazardous open drain."
    }
}


def load_classifier():
    """
    Lazy loads the trained Keras model and class names dictionary.
    """
    global _MODEL, _CLASS_NAMES

    if _MODEL is None:
        if not os.path.exists(MODEL_PATH):
            raise FileNotFoundError(f"Trained model not found at: {MODEL_PATH}")

        import tensorflow as tf
        _MODEL = tf.keras.models.load_model(MODEL_PATH)

    if _CLASS_NAMES is None:
        if os.path.exists(LABELS_PATH):
            with open(LABELS_PATH, "r", encoding="utf-8") as f:
                mapping = json.load(f)
                # Ensure sorted by integer index
                _CLASS_NAMES = [mapping[str(i)] for i in range(len(mapping))]
        else:
            # Fallback default alphabetical ordering matching flow_from_directory
            _CLASS_NAMES = [
                "electricity",
                "garbage",
                "road_damage",
                "sewerage",
                "streetlights",
                "traffic_safety",
                "water_supply"
            ]

    return _MODEL, _CLASS_NAMES


def preprocess_image_input(image_input, target_size=(224, 224)):
    """
    Standardizes image input from filepath, bytes, BytesIO, or PIL Image into
    a preprocessed batch tensor ready for MobileNetV2.
    """
    if isinstance(image_input, (str, os.PathLike)):
        pil_img = Image.open(image_input)
    elif isinstance(image_input, (bytes, bytearray)):
        pil_img = Image.open(io.BytesIO(image_input))
    elif hasattr(image_input, "read"):
        # File-like object (BytesIO, Streamlit UploadedFile, FastAPI UploadFile)
        image_input.seek(0)
        pil_img = Image.open(io.BytesIO(image_input.read()))
    elif isinstance(image_input, Image.Image):
        pil_img = image_input
    else:
        raise TypeError(f"Unsupported image input type: {type(image_input)}")

    # Ensure RGB (discard alpha or convert grayscale/palette)
    if pil_img.mode != "RGB":
        pil_img = pil_img.convert("RGB")

    # Resize to model target input
    resized_img = pil_img.resize(target_size, Image.Resampling.BILINEAR)

    # Convert to float32 array in [0, 255] range expected by the Keras model
    # Note: tf.keras.applications.mobilenet_v2.preprocess_input is already embedded
    # in Layer 4 of the trained model architecture, so we do not double-preprocess.
    img_array = np.array(resized_img, dtype=np.float32)

    # Expand batch dimension: (1, 224, 224, 3)
    batch_array = np.expand_dims(img_array, axis=0)

    return batch_array, pil_img


def classify_image(image_input, top_k=3):
    """
    Predicts the civic complaint category for an image.

    Parameters:
    - image_input: File path, bytes, file-like object, or PIL.Image
    - top_k: Number of top ranked classes to return

    Returns dict:
    {
        "status": "success",
        "predicted_class": "road_damage",
        "display_name": "Road Damage / Potholes",
        "confidence": 97.4,
        "is_confident": True,
        "suggested_department": "BBMP / Municipal Works",
        "suggested_reason": "Mobility - Roads & Infrastructure",
        "suggested_priority": "High",
        "sla_hours": 48,
        "all_probabilities": { "road_damage": 0.974, ... },
        "top_predictions": [ {"class": "road_damage", "confidence": 97.4}, ... ]
    }
    """
    model, class_names = load_classifier()
    batch_tensor, _ = preprocess_image_input(image_input)

    raw_preds = model.predict(batch_tensor, verbose=0)[0]

    # Map class name to float probability
    prob_dict = {
        name: float(round(float(raw_preds[idx]) * 100, 2))
        for idx, name in enumerate(class_names)
    }

    # Best prediction
    best_idx = int(np.argmax(raw_preds))
    best_class = class_names[best_idx]
    best_conf = prob_dict[best_class]

    # Top-K predictions
    sorted_indices = np.argsort(raw_preds)[::-1][:top_k]
    top_predictions = [
        {
            "class": class_names[i],
            "display_name": CIVIC_CATEGORY_METADATA.get(class_names[i], {}).get("display_name", class_names[i]),
            "confidence": prob_dict[class_names[i]]
        }
        for i in sorted_indices
    ]

    meta = CIVIC_CATEGORY_METADATA.get(best_class, {
        "display_name": best_class.replace("_", " ").title(),
        "department": "Municipal Administration",
        "complaint_reason": "General Civic Issue",
        "priority": "Medium",
        "estimated_sla_hours": 48,
        "description": ""
    })

    return {
        "status": "success",
        "predicted_class": best_class,
        "display_name": meta["display_name"],
        "confidence": best_conf,
        "is_confident": bool(best_conf >= 60.0),
        "suggested_department": meta["department"],
        "suggested_reason": meta["complaint_reason"],
        "suggested_priority": meta["priority"],
        "sla_hours": meta["estimated_sla_hours"],
        "description": meta["description"],
        "top_predictions": top_predictions,
        "all_probabilities": prob_dict
    }


if __name__ == "__main__":
    import sys
    print("Testing image classification module...")
    if len(sys.argv) > 1:
        test_path = sys.argv[1]
    else:
        # Pick first available test image from dataset
        dataset_dir = os.path.join(BASE_DIR, "dataset")
        for cls in ["road_damage", "garbage", "electricity", "sewerage"]:
            folder = os.path.join(dataset_dir, cls)
            if os.path.exists(folder):
                files = os.listdir(folder)
                if files:
                    test_path = os.path.join(folder, files[0])
                    break

    print(f"Testing on sample: {test_path}")
    res = classify_image(test_path)
    print("\nPrediction Result:")
    print(json.dumps(res, indent=2))
