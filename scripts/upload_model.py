"""Upload a trained model folder to the models bucket: python scripts/upload_model.py models/v1"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "worker"))
import storage  # noqa: E402

folder = sys.argv[1].rstrip("/")
version = os.path.basename(folder)
c = storage.client()
for name in sorted(os.listdir(folder)):
    p = os.path.join(folder, name)
    if os.path.isfile(p):
        c.upload_file(p, "models", f"{version}/{name}")
        print("uploaded", f"models/{version}/{name}")
