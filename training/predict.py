"""Generate predictions for score.py with a local model folder (or the untrained base).

  python training/predict.py --model EleutherAI/pythia-70m --out results/pred_base.jsonl
  python training/predict.py --model models/v1 --out results/pred_student_v1.jsonl
Output: one line per validation command, {"id": ..., "prediction": "<raw text>"}.
"""
import argparse
import json
import time

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer


def generate(model, tok, text, max_new_tokens):
    prompt = f"Command: {text}\nJSON:"
    ids = tok(prompt, return_tensors="pt")
    with torch.no_grad():
        out = model.generate(**ids, max_new_tokens=max_new_tokens, do_sample=False,
                             pad_token_id=tok.eos_token_id, eos_token_id=tok.eos_token_id)
    gen = tok.decode(out[0][ids["input_ids"].shape[1]:], skip_special_tokens=True)
    return gen.strip().split("\n")[0]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", required=True)
    ap.add_argument("--data", default="data/validation.jsonl")
    ap.add_argument("--out", required=True)
    ap.add_argument("--max-new-tokens", type=int, default=64)
    a = ap.parse_args()

    tok = AutoTokenizer.from_pretrained(a.model)
    model = AutoModelForCausalLM.from_pretrained(a.model)
    model.eval()
    t0 = time.time()
    n = 0
    with open(a.data, encoding="utf-8") as f, open(a.out, "w", encoding="utf-8") as o:
        for line in f:
            r = json.loads(line)
            pred = generate(model, tok, r["text"], a.max_new_tokens)
            o.write(json.dumps({"id": r["id"], "prediction": pred}) + "\n")
            n += 1
    print(f"{n} predictions -> {a.out} in {time.time() - t0:.1f}s ({(time.time() - t0) / n:.2f}s each)")


if __name__ == "__main__":
    main()
