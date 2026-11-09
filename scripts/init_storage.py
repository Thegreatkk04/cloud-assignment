"""Create the datasets and models buckets and upload commands_pool.jsonl (Task 1 step 2)."""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "worker"))
import storage  # noqa: E402

c = storage.client()
existing = {b["Name"] for b in c.list_buckets().get("Buckets", [])}
for b in ("datasets", "models"):
    if b not in existing:
        c.create_bucket(Bucket=b)
        print("created bucket", b)
c.upload_file("data/commands_pool.jsonl", "datasets", "commands_pool.jsonl")
print("uploaded commands_pool.jsonl to datasets")
