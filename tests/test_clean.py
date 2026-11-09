import clean


def rec(i, text, raw):
    return {"id": f"C{i:04d}", "text": text, "teacher_raw": raw}


def test_each_rejection_reason_is_counted_once():
    records = [
        rec(1, "what is the weather in london", '{"intent": "weather_query", "date": null, "time": null, "place": "london"}'),
        rec(2, "set alarm for six am", 'not json at all'),                                                  # (a)
        rec(3, "set alarm for six am", '{"intent": "alarm_set", "date": null, "time": "six am"}'),          # (b) missing key
        rec(4, "set alarm for six am", '{"intent": "alarm_make", "date": null, "time": "six am", "place": null}'),  # (c)
        rec(5, "set alarm for six am", '{"intent": "alarm_set", "date": "tomorrow", "time": "six am", "place": null}'),  # (d) invented
        rec(6, "what is the weather in london", '{"intent": "weather_query", "date": null, "time": null, "place": "london"}'),  # duplicate of 1
    ]
    kept, counts = clean.clean(records)
    assert counts == {"input": 6, "a": 1, "b": 1, "c": 1, "d": 1, "duplicates": 1, "kept": 1}
    assert kept[0]["id"] == "C0001"
    total = counts["a"] + counts["b"] + counts["c"] + counts["d"] + counts["duplicates"] + counts["kept"]
    assert total == counts["input"]


def test_output_sorted_by_id_and_smallest_duplicate_kept():
    records = [
        rec(9, "delete my meeting", '{"intent": "calendar_remove", "date": null, "time": null, "place": null}'),
        rec(2, "delete my meeting", '{"intent": "calendar_remove", "date": null, "time": null, "place": null}'),
        rec(5, "time in tokyo", '{"intent": "datetime_query", "date": null, "time": null, "place": "tokyo"}'),
    ]
    kept, counts = clean.clean(records)
    assert [k["id"] for k in kept] == ["C0002", "C0005"]
    assert counts["duplicates"] == 1


def test_json_wrapped_in_text_is_still_parsed():
    obj = clean.parse_reply('Sure! {"intent": "alarm_query", "date": "today", "time": null, "place": null}')
    assert obj["intent"] == "alarm_query"
