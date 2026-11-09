"""Task 1 labelling worker.

Reads SHARD_INDEX and SHARD_COUNT, takes every command whose line number
(from 0) % SHARD_COUNT == SHARD_INDEX, asks the teacher (phi3.5 on Ollama,
temperature 0, seed 42) and writes {"id", "text", "teacher_raw"} lines to
datasets/teacher/shard-<SHARD_INDEX>.jsonl in the datasets bucket.

The teacher reply is stored exactly as returned. Nothing is edited.

Env vars:
  SHARD_INDEX, SHARD_COUNT   required
  OLLAMA_URL                 default http://host.k3d.internal:11434
  TEACHER_MODEL              default phi3.5
  S3_ENDPOINT + AWS creds    see storage.py
  LOCAL_POOL                 optional: read commands from this local file instead of S3
  LOCAL_OUT                  optional: write the shard to this local folder instead of S3
"""
import json
import os
import sys
import time

import requests

import storage

BUCKET = "datasets"
POOL_KEY = "commands_pool.jsonl"
PROMPT_PATH = os.path.join(os.path.dirname(__file__), "..", "prompts", "teacher_prompt.txt")


def load_prompt():
    p = os.environ.get("PROMPT_PATH", PROMPT_PATH)
    with open(p, encoding="utf-8") as f:
        return f.read()


def ask_teacher(prompt, command, url, model):
    body = {
        "model": model,
        "prompt": prompt.replace("{command}", command),
        "stream": False,
        "options": {"temperature": 0, "seed": 42, "num_predict": 80},
    }
    for attempt in range(3):
        try:
            r = requests.post(f"{url}/api/generate", json=body, timeout=300)
            r.raise_for_status()
            return r.json()["response"]
        except Exception as e:  # noqa: BLE001
            print(f"teacher call failed ({e}), retry {attempt + 1}/3", file=sys.stderr)
            time.sleep(2)
    raise RuntimeError("teacher not reachable")


def my_lines(lines, index, count):
    return [(i, line) for i, line in enumerate(lines) if i % count == index]


def main():
    index = int(os.environ["SHARD_INDEX"])
    count = int(os.environ["SHARD_COUNT"])
    url = os.environ.get("OLLAMA_URL", "http://host.k3d.internal:11434")
    model = os.environ.get("TEACHER_MODEL", "phi3.5")
    local_pool = os.environ.get("LOCAL_POOL")
    local_out = os.environ.get("LOCAL_OUT")

    if local_pool:
        with open(local_pool, encoding="utf-8") as f:
            raw = f.read()
    else:
        raw = storage.get_text(BUCKET, POOL_KEY)
    lines = [ln for ln in raw.splitlines() if ln.strip()]
    mine = my_lines(lines, index, count)
    print(f"shard {index}/{count}: {len(mine)} commands")

    prompt = load_prompt()
    out_lines = []
    key = f"teacher/shard-{index}.jsonl"
    t0 = time.time()
    for n, (_, line) in enumerate(mine, 1):
        rec = json.loads(line)
        reply = ask_teacher(prompt, rec["text"], url, model)
        out_lines.append(json.dumps({"id": rec["id"], "text": rec["text"], "teacher_raw": reply}))
        if n % 25 == 0:
            print(f"  {n}/{len(mine)} done, {time.time() - t0:.0f}s")
            if not local_out:
                storage.put_text(BUCKET, key, "\n".join(out_lines) + "\n")

    text = "\n".join(out_lines) + "\n"
    if local_out:
        os.makedirs(local_out, exist_ok=True)
        with open(os.path.join(local_out, f"shard-{index}.jsonl"), "w", encoding="utf-8") as f:
            f.write(text)
    else:
        storage.put_text(BUCKET, key, text)
    print(f"shard {index} finished in {time.time() - t0:.0f}s")


if __name__ == "__main__":
    main()
