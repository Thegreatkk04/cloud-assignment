import importlib
import os

from fastapi.testclient import TestClient


class FakeRunner:
    def __init__(self, reply):
        self.reply = reply

    def generate(self, text):
        return self.reply


def make_app(fault="0"):
    os.environ["SKIP_MODEL_LOAD"] = "1"
    os.environ["FAULT_INJECT"] = fault
    os.environ["MODEL_VERSION"] = "v1"
    os.environ["POD_NAME"] = "parser-test-pod"
    import app as service_app
    importlib.reload(service_app)
    return service_app


def test_healthz_and_readyz_before_model_loads():
    m = make_app()
    c = TestClient(m.app)
    assert c.get("/healthz").status_code == 200
    assert c.get("/readyz").status_code == 503
    m.state["runner"] = FakeRunner('{"intent": "weather_query", "date": null, "time": null, "place": "london"}')
    assert c.get("/readyz").status_code == 200


def test_parse_returns_four_keys_and_headers():
    m = make_app()
    m.state["runner"] = FakeRunner('{"intent": "weather_query", "date": null, "time": null, "place": "london"}')
    c = TestClient(m.app)
    r = c.post("/parse", json={"text": "what is the weather in london"})
    assert r.status_code == 200
    assert r.json() == {"intent": "weather_query", "date": None, "time": None, "place": "london"}
    assert r.headers["X-Model-Version"] == "v1"
    assert r.headers["X-Served-By"] == "parser-test-pod"


def test_fault_inject_gives_500_with_exact_body():
    m = make_app(fault="1")
    m.state["runner"] = FakeRunner('{"intent": "weather_query", "date": null, "time": null, "place": "london"}')
    c = TestClient(m.app)
    r = c.post("/parse", json={"text": "weather"})
    assert r.status_code == 500
    assert r.json() == {"error": "invalid_model_output"}
