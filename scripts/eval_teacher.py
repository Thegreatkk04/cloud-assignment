"""Run the teacher (phi3.5 on Ollama, same prompt/settings as Task 1) on validation.jsonl."""
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "worker"))
from label_worker import ask_teacher, load_prompt  # noqa: E402

url = os.environ.get("OLLAMA_URL", "http://localhost:11434")
prompt = load_prompt()
with open("data/validation.jsonl", encoding="utf-8") as f, open("results/pred_teacher.jsonl", "w", encoding="utf-8") as o:
    for line in f:
        r = json.loads(line)
        o.write(json.dumps({"id": r["id"], "prediction": ask_teacher(prompt, r["text"], url, "phi3.5")}) + "\n")
print("wrote results/pred_teacher.jsonl")
