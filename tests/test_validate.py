import model_runner as mr


def test_valid_output_passes():
    out = mr.validate('{"intent": "weather_query", "date": null, "time": null, "place": "london"}')
    assert out == {"intent": "weather_query", "date": None, "time": None, "place": "london"}


def test_not_json_fails():
    assert mr.validate("not json") is None


def test_wrong_keys_or_intent_fail():
    assert mr.validate('{"intent": "weather_query", "date": null, "time": null}') is None
    assert mr.validate('{"intent": "pizza", "date": null, "time": null, "place": null}') is None
    assert mr.validate('{"intent": "alarm_set", "date": 5, "time": null, "place": null}') is None
