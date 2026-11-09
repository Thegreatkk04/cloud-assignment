import subnet_calc


def test_four_subnets_match_the_table():
    rows = {r["name"]: r for r in subnet_calc.allocate()}
    assert rows["app"]["network"] == "10.20.0.0" and rows["app"]["prefix"] == 22 and rows["app"]["usable"] == 1022
    assert rows["public"]["network"] == "10.20.4.0" and rows["public"]["prefix"] == 24
    assert rows["data"]["network"] == "10.20.5.0" and rows["data"]["prefix"] == 25
    assert rows["management"]["network"] == "10.20.5.128" and rows["management"]["prefix"] == 27
    assert rows["management"]["broadcast"] == "10.20.5.159"
