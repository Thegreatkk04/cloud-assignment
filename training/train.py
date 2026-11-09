"""Task 2: sequence-level distillation of pythia-70m.

Every training example is
    Command: <command>
    JSON: <teacher json>
and the student is trained (causal LM loss, prompt tokens masked out) to
produce the teacher's JSON. All settings come from training/config.yaml.

  python training/train.py                        full run (first 1,500 records)
  python training/train.py --subset 50            smoke test on 50 records
  python training/train.py --seed 7 --out models/v2   second version for Task 4
"""
import argparse
import csv
import hashlib
import json
import os
import random
import tarfile

import torch
import yaml
from torch.utils.data import DataLoader, Dataset
from transformers import AutoModelForCausalLM, AutoTokenizer

HERE = os.path.dirname(os.path.abspath(__file__))
CONFIG = os.path.join(HERE, "config.yaml")
KEYS = ["intent", "date", "time", "place"]


def load_config():
    with open(CONFIG, encoding="utf-8") as f:
        return yaml.safe_load(f)


def build_text(cmd, target_json):
    # No trailing space after "JSON:" so the prompt tokens are a clean prefix of the full text.
    return f"Command: {cmd}\nJSON:", " " + target_json


def set_seed(seed):
    random.seed(seed)
    torch.manual_seed(seed)


class JsonlDataset(Dataset):
    def __init__(self, path, tok, max_len, limit):
        self.items = []
        with open(path, encoding="utf-8") as f:
            for n, line in enumerate(f):
                if n >= limit:
                    break
                r = json.loads(line)
                target = json.dumps({k: r[k] for k in KEYS})
                prompt, completion = build_text(r["text"], target)
                p_ids = tok(prompt)["input_ids"]
                full = tok(prompt + completion)["input_ids"] + [tok.eos_token_id]
                full = full[:max_len]
                labels = [-100] * min(len(p_ids), len(full)) + full[len(p_ids):]
                self.items.append((full, labels))
        self.pad = tok.pad_token_id if tok.pad_token_id is not None else tok.eos_token_id

    def __len__(self):
        return len(self.items)

    def __getitem__(self, i):
        return self.items[i]

    def collate(self, batch):
        L = max(len(x[0]) for x in batch)
        ids = torch.full((len(batch), L), self.pad, dtype=torch.long)
        lab = torch.full((len(batch), L), -100, dtype=torch.long)
        att = torch.zeros((len(batch), L), dtype=torch.long)
        for i, (x, y) in enumerate(batch):
            ids[i, :len(x)] = torch.tensor(x)
            lab[i, :len(y)] = torch.tensor(y)
            att[i, :len(x)] = 1
        return ids, att, lab


def sha256_of_dir(folder):
    h = hashlib.sha256()
    for name in sorted(os.listdir(folder)):
        p = os.path.join(folder, name)
        if os.path.isfile(p) and name != "model.sha256":
            h.update(name.encode())
            with open(p, "rb") as f:
                for chunk in iter(lambda: f.read(1 << 20), b""):
                    h.update(chunk)
    return h.hexdigest()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--subset", type=int, default=None, help="train on the first N records only")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--epochs", type=int, default=None)
    ap.add_argument("--out", default=None)
    ap.add_argument("--train-file", default=None)
    a = ap.parse_args()

    cfg = load_config()
    seed = a.seed if a.seed is not None else cfg["seed"]
    epochs = a.epochs if a.epochs is not None else cfg["epochs"]
    out_dir = a.out or cfg["output_dir"]
    train_file = a.train_file or cfg["train_file"]
    limit = a.subset if a.subset else cfg["max_records"]
    set_seed(seed)
    torch.set_num_threads(max(1, os.cpu_count() or 1))

    tok = AutoTokenizer.from_pretrained(cfg["student"])
    model = AutoModelForCausalLM.from_pretrained(cfg["student"])
    model.train()

    ds = JsonlDataset(train_file, tok, cfg["max_seq_len"], limit)
    dl = DataLoader(ds, batch_size=cfg["batch_size"], shuffle=True, collate_fn=ds.collate,
                    generator=torch.Generator().manual_seed(seed))
    opt = torch.optim.AdamW(model.parameters(), lr=float(cfg["learning_rate"]))
    print(f"records={len(ds)} epochs={epochs} seed={seed} lr={cfg['learning_rate']} bs={cfg['batch_size']}")

    loss_rows = []
    for ep in range(1, epochs + 1):
        total, steps = 0.0, 0
        for ids, att, lab in dl:
            out = model(input_ids=ids, attention_mask=att, labels=lab)
            out.loss.backward()
            opt.step()
            opt.zero_grad()
            total += out.loss.item()
            steps += 1
        avg = total / max(steps, 1)
        loss_rows.append((ep, round(avg, 4)))
        print(f"epoch {ep}: loss {avg:.4f}")

    loss_path = os.path.join(HERE, "loss.csv")
    with open(loss_path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["epoch", "loss"])
        w.writerows(loss_rows)

    os.makedirs(out_dir, exist_ok=True)
    model.save_pretrained(out_dir)
    tok.save_pretrained(out_dir)
    with open(os.path.join(out_dir, "VERSION"), "w") as f:
        f.write(json.dumps({"version": os.path.basename(out_dir), "seed": seed, "epochs": epochs,
                            "records": len(ds), "student": cfg["student"]}) + "\n")
    digest = sha256_of_dir(out_dir)
    with open(os.path.join(out_dir, "model.sha256"), "w") as f:
        f.write(digest + "\n")
    tar_path = out_dir.rstrip("/") + ".tar.gz"
    with tarfile.open(tar_path, "w:gz") as t:
        t.add(out_dir, arcname=os.path.basename(out_dir))
    print(f"saved {out_dir}, sha256 {digest}, archive {tar_path}")


if __name__ == "__main__":
    main()
