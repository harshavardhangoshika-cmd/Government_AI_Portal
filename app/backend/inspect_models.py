import os
import joblib
from sklearn.pipeline import Pipeline

# Pickle folder
BASE_DIR = os.path.dirname(os.path.dirname(__file__))
PICKLE_DIR = os.path.join(BASE_DIR, "pickles")

print("=" * 70)
print("INSPECTING ALL MODELS")
print("=" * 70)

for file in sorted(os.listdir(PICKLE_DIR)):

    if file.endswith(".pkl"):

        print(f"\n{file}")

        obj = joblib.load(os.path.join(PICKLE_DIR, file))

        print("Type:", type(obj))

        if isinstance(obj, Pipeline):
            print("Pipeline Model")
            print("Steps:")
            print(obj.named_steps)

        else:
            print(obj)