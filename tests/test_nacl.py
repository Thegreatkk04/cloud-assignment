import json
import os

import nacl_sim

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def test_sample_packets_all_correct():
    rules = nacl_sim.load_rules(os.path.join(ROOT, "network", "nacl.json"))
    with open(os.path.join(ROOT, "network", "packets_sample.jsonl")) as f:
        pkts = [json.loads(l) for l in f if l.strip()]
    for p in pkts:
        action, _ = nacl_sim.decide(rules, p)
        assert action == p["expected"], p["id"]


def test_abusive_range_blocked_even_on_web_ports_and_ssh_only_from_management():
    rules = nacl_sim.load_rules(os.path.join(ROOT, "network", "nacl.json"))
    assert nacl_sim.decide(rules, {"direction": "inbound", "protocol": "tcp", "port": 80, "address": "198.51.100.200"})[0] == "deny"
    assert nacl_sim.decide(rules, {"direction": "inbound", "protocol": "tcp", "port": 22, "address": "10.20.5.130"})[0] == "allow"
    assert nacl_sim.decide(rules, {"direction": "inbound", "protocol": "tcp", "port": 22, "address": "10.20.1.5"})[0] == "deny"
    assert nacl_sim.decide(rules, {"direction": "inbound", "protocol": "tcp", "port": 40000, "address": "10.20.2.7"})[0] == "allow"
    assert nacl_sim.decide(rules, {"direction": "outbound", "protocol": "tcp", "port": 443, "address": "10.20.5.5"})[0] == "deny"
