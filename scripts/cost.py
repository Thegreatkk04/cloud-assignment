"""Task 7 cost estimate from data/rate_card.json.

cost per 1000 requests = (hourly cost of all running replicas / requests served per hour) * 1000
Each replica is billed for its CPU limit and memory limit for every hour it runs.

  python scripts/cost.py --replicas 2 --cpu-limit 1 --mem-gib 1 --rps 1.5
"""
import argparse
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))


def load_rates(path=None):
    with open(path or os.path.join(HERE, "..", "data", "rate_card.json"), encoding="utf-8") as f:
        return json.load(f)


def estimate(replicas, cpu_limit, mem_gib, rps, rates):
    per_replica_hour = cpu_limit * rates["vcpu_hour"] + mem_gib * rates["gib_memory_hour"]
    hourly = replicas * per_replica_hour
    per_hour_requests = rps * 3600
    cost_1000 = hourly / per_hour_requests * 1000
    return {
        "per_replica_hour": round(per_replica_hour, 4),
        "hourly_all_replicas": round(hourly, 4),
        "requests_per_hour": round(per_hour_requests, 1),
        "cost_per_1000_requests": round(cost_1000, 4),
        "currency": rates["currency"],
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--replicas", type=int, default=2)
    ap.add_argument("--cpu-limit", type=float, default=1.0)
    ap.add_argument("--mem-gib", type=float, default=1.0)
    ap.add_argument("--rps", type=float, required=True, help="measured requests per second")
    a = ap.parse_args()
    rates = load_rates()
    r = estimate(a.replicas, a.cpu_limit, a.mem_gib, a.rps, rates)
    print(f"rate card: {rates['vcpu_hour']} {rates['currency']}/vCPU-hour, {rates['gib_memory_hour']} {rates['currency']}/GiB-hour")
    print(f"one replica per hour  = {a.cpu_limit} x {rates['vcpu_hour']} + {a.mem_gib} x {rates['gib_memory_hour']} = {r['per_replica_hour']}")
    print(f"{a.replicas} replicas per hour = {r['hourly_all_replicas']}")
    print(f"requests per hour     = {a.rps} x 3600 = {r['requests_per_hour']}")
    print(f"cost per 1000 requests = {r['hourly_all_replicas']} / {r['requests_per_hour']} x 1000 = {r['cost_per_1000_requests']} {rates['currency']}")


if __name__ == "__main__":
    main()
