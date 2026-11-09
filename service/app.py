"""Task 3 inference service (FastAPI, port 8000).

POST /parse   {"text": "..."} -> 200 + four-key JSON, headers X-Model-Version, X-Served-By
GET  /healthz -> 200 while the process is alive
GET  /readyz  -> 503 until the model is loaded, then 200

Config (env): MODEL_URI, MODEL_VERSION, S3_ENDPOINT, MAX_NEW_TOKENS, FAULT_INJECT (0/1).
AWS_ACCESS_KEY_ID / AWS_SECRET_ACCESS_KEY come from the Kubernetes Secret.
"""
import os
import socket
import threading
from contextlib import asynccontextmanager

from fastapi import FastAPI, Response
from fastapi.responses import JSONResponse
from pydantic import BaseModel

import model_runner

MODEL_URI = os.environ.get("MODEL_URI", "s3://models/v1")
MODEL_VERSION = os.environ.get("MODEL_VERSION", "v1")
S3_ENDPOINT = os.environ.get("S3_ENDPOINT", "http://localhost:8333")
MAX_NEW_TOKENS = int(os.environ.get("MAX_NEW_TOKENS", "64"))
FAULT_INJECT = os.environ.get("FAULT_INJECT", "0") == "1"
POD_NAME = os.environ.get("POD_NAME") or socket.gethostname()

os.environ.setdefault("S3_ENDPOINT", S3_ENDPOINT)

state = {"runner": None, "error": None}


class ParseIn(BaseModel):
    text: str


def load_model():
    try:
        local = model_runner.fetch_model(MODEL_URI, f"/tmp/model-{MODEL_VERSION}")
        state["runner"] = model_runner.Runner(local, MAX_NEW_TOKENS)
        print(f"model {MODEL_VERSION} loaded from {MODEL_URI}", flush=True)
    except Exception as e:  # noqa: BLE001
        state["error"] = str(e)
        print(f"model load failed: {e}", flush=True)


@asynccontextmanager
async def lifespan(_app):
    # start the model download in the background so /healthz answers at once
    if os.environ.get("SKIP_MODEL_LOAD") != "1":
        threading.Thread(target=load_model, daemon=True).start()
    yield


app = FastAPI(title="command-parser", lifespan=lifespan)


@app.get("/healthz")
def healthz():
    return {"status": "ok"}


@app.get("/readyz")
def readyz():
    if state["runner"] is None:
        return JSONResponse({"status": "loading", "error": state["error"]}, status_code=503)
    return {"status": "ready"}


@app.post("/parse")
def parse(body: ParseIn, response: Response):
    headers = {"X-Model-Version": MODEL_VERSION, "X-Served-By": POD_NAME}
    if state["runner"] is None:
        return JSONResponse({"error": "model_not_ready"}, status_code=503, headers=headers)
    raw = state["runner"].generate(body.text)
    if FAULT_INJECT:
        raw = "not json"
    obj = model_runner.validate(raw)
    if obj is None:
        return JSONResponse({"error": "invalid_model_output"}, status_code=500, headers=headers)
    return JSONResponse(obj, status_code=200, headers=headers)
