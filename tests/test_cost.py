import cost


def test_cost_formula_with_rate_card():
    rates = {"vcpu_hour": 3.5, "gib_memory_hour": 0.45, "currency": "INR"}
    r = cost.estimate(replicas=2, cpu_limit=1, mem_gib=1, rps=1.0, rates=rates)
    assert r["per_replica_hour"] == 3.95
    assert r["hourly_all_replicas"] == 7.9
    assert r["requests_per_hour"] == 3600
    assert abs(r["cost_per_1000_requests"] - 7.9 / 3600 * 1000) < 1e-3
