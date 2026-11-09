"""Loads the student model (from object storage or a local folder) and runs inference."""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
with open(os.path.join(HERE, "schema.json"), encoding="utf-8") as f:
    SCHEMA = json.load(f)
KEYS = SCHEMA["keys"]
INTENTS = set(SCHEMA["intents"])


def validate(raw):
    """Return the parsed four-key dict if raw is a valid output, else None."""
    if not isinstance(raw, str):
        return None
    try:
        obj = json.loads(raw.strip())
    except Exception:  # noqa: BLE001
        return None
    if not isinstance(obj, dict) or sorted(obj.keys()) != sorted(KEYS):
        return None
    if obj["intent"] not in INTENTS:
        return None
    for k in ("date", "time", "place"):
        if obj[k] is not None and not isinstance(obj[k], str):
            return None
    return {k: obj[k] for k in KEYS}


def fetch_model(model_uri, dest):
    """model_uri like s3://models/v1 -> download into dest. A plain folder path is used as is."""
    if not model_uri.startswith("s3://"):
        return model_uri
    bucket, _, prefix = model_uri[5:].partition("/")
    sys.path.insert(0, os.path.join(HERE, "..", "worker"))
    import storage  # noqa: E402
    storage.download_dir(bucket, prefix, dest)
    return dest


class Runner:
    def __init__(self, model_dir, max_new_tokens):
        import torch
        from transformers import AutoModelForCausalLM, AutoTokenizer
        torch.set_num_threads(1)
        self.torch = torch
        self.tok = AutoTokenizer.from_pretrained(model_dir)
        self.model = AutoModelForCausalLM.from_pretrained(model_dir)
        self.model.eval()
        self.max_new_tokens = max_new_tokens

    def generate(self, text):
        prompt = f"Command: {text}\nJSON:"
        ids = self.tok(prompt, return_tensors="pt")
        with self.torch.no_grad():
            out = self.model.generate(**ids, max_new_tokens=self.max_new_tokens, do_sample=False,
                                      pad_token_id=self.tok.eos_token_id,
                                      eos_token_id=self.tok.eos_token_id)
        gen = self.tok.decode(out[0][ids["input_ids"].shape[1]:], skip_special_tokens=True)
        return gen.strip().split("\n")[0]
