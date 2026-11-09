"""Task 1 cleaning step.

Reads every datasets/teacher/shard-*.jsonl, drops bad records, writes
datasets/v1/train.jsonl (sorted by id) and datasets/v1/train.sha256.

Rejection reasons, checked in this order (a record is counted once, under
the first reason that applies):
  (a) teacher_raw is not valid JSON
  (b) keys are not exactly intent, date, time, place
  (c) intent is not one of the eight
  (d) a slot value is neither null nor text that appears in the command
  (e) duplicate command text (the smallest id is kept)

Usage:
  python worker/clean.py --local-shards datasets/teacher --local-out datasets/v1
  python worker/clean.py            (reads and writes the datasets bucket)
"""
import argparse
import glob
import hashlib
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
with open(os.path.join(HERE, "..", "data", "schema.json"), encoding="utf-8") as f:
    SCHEMA = json.load(f)
KEYS = SCHEMA["keys"]
INTENTS = set(SCHEMA["intents"])


def parse_reply(raw):
    """Return the parsed dict or None. Accepts the first {...} block in the text."""
    raw = raw.strip()
    try:
        obj = json.loads(raw)
    except Exception:  # noqa: BLE001
        start, end = raw.find("{"), raw.rfind("}")
        if start == -1 or end <= start:
            return None
        try:
            obj = json.loads(raw[start:end + 1])
        except Exception:  # noqa: BLE001
            return None
    return obj if isinstance(obj, dict) else None


def reject_reason(text, raw):
    """Return None if the record is fine, else 'a', 'b', 'c' or 'd'."""
    obj = parse_reply(raw)
    if obj is None:
        return "a", None
    if sorted(obj.keys()) != sorted(KEYS):
        return "b", None
    if obj["intent"] not in INTENTS:
        return "c", None
    low = " ".join(text.lower().split())
    for slot in ("date", "time", "place"):
        v = obj[slot]
        if v is None:
            continue
        if not isinstance(v, str) or " ".join(v.lower().split()) not in low:
            return "d", None
    return None, obj


def clean(records):
    """records: list of {"id","text","teacher_raw"}. Returns (kept, counts)."""
    counts = {"input": len(records), "a": 0, "b": 0, "c": 0, "d": 0, "duplicates": 0, "kept": 0}
    good = []
    for r in records:
        reason, obj = reject_reason(r["text"], r["teacher_raw"])
        if reason:
            counts[reason] += 1
            continue
        good.append({"id": r["id"], "text": r["text"], **{k: obj[k] for k in KEYS}})
    good.sort(key=lambda x: x["id"])
    seen = set()
    kept = []
    for g in good:
        key = " ".join(g["text"].lower().split())
        if key in seen:
            counts["duplicates"] += 1
            continue
        seen.add(key)
        kept.append(g)
    counts["kept"] = len(kept)
    return kept, counts


def to_jsonl(kept):
    return "".join(json.dumps(k) + "\n" for k in kept)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--local-shards", help="folder with shard-*.jsonl (instead of S3)")
    ap.add_argument("--local-out", help="folder for train.jsonl (instead of S3)")
    ap.add_argument("--counts-out", default="results/clean_counts.json")
    a = ap.parse_args()

    records = []
    if a.local_shards:
        for p in sorted(glob.glob(os.path.join(a.local_shards, "shard-*.jsonl"))):
            with open(p, encoding="utf-8") as f:
                records += [json.loads(ln) for ln in f if ln.strip()]
    else:
        sys.path.insert(0, HERE)
        import storage  # noqa: E402
        for key in storage.list_keys("datasets", "teacher/shard-"):
            records += [json.loads(ln) for ln in storage.get_text("datasets", key).splitlines() if ln.strip()]

    kept, counts = clean(records)
    text = to_jsonl(kept)
    digest = hashlib.sha256(text.encode("utf-8")).hexdigest()
    counts["sha256"] = digest

    if a.local_out:
        os.makedirs(a.local_out, exist_ok=True)
        with open(os.path.join(a.local_out, "train.jsonl"), "w", encoding="utf-8") as f:
            f.write(text)
        with open(os.path.join(a.local_out, "train.sha256"), "w", encoding="utf-8") as f:
            f.write(digest + "  train.jsonl\n")
    else:
        storage.put_text("datasets", "v1/train.jsonl", text)
        storage.put_text("datasets", "v1/train.sha256", digest + "  train.jsonl\n")

    os.makedirs(os.path.dirname(a.counts_out) or ".", exist_ok=True)
    with open(a.counts_out, "w", encoding="utf-8") as f:
        json.dump(counts, f, indent=2)
    print(json.dumps(counts, indent=2))
    total = counts["a"] + counts["b"] + counts["c"] + counts["d"] + counts["duplicates"] + counts["kept"]
    print(f"check: {total} == {counts['input']} -> {total == counts['input']}")


if __name__ == "__main__":
    main()
