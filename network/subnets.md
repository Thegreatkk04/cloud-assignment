# Task 5: Subnetting 10.20.0.0/16

Generated with `python scripts/subnet_calc.py` (output saved in `results/subnet_table.txt`).

## Working

Rule: usable hosts = 2^(32 - prefix) - 2. I need the smallest prefix whose usable
count is still >= the requirement. Allocation goes from the largest requirement to
the smallest, each subnet starting right after the previous one.

| Subnet | Needed | Smallest block that fits | Why |
|---|---:|---|---|
| app | 1000 | /22 (1024 addresses, 1022 usable) | /23 gives only 510 usable, not enough |
| public | 250 | /24 (256 addresses, 254 usable) | /25 gives 126, not enough |
| data | 100 | /25 (128 addresses, 126 usable) | /26 gives 62, not enough |
| management | 20 | /27 (32 addresses, 30 usable) | /28 gives 14, not enough |

Placing them one after another from 10.20.0.0:

- app takes 10.20.0.0 to 10.20.3.255 (4 x /24 blocks)
- public starts at 10.20.4.0 and takes one /24
- data starts at 10.20.5.0 and takes half of the next /24
- management starts at 10.20.5.128 (the next /27 boundary after data ends at 10.20.5.127)

## Final table

| Subnet | Hosts needed | Network address | Prefix | Usable host range | Broadcast | Usable hosts |
|---|---:|---|---|---|---|---:|
| app | 1000 | 10.20.0.0 | /22 | 10.20.0.1 - 10.20.3.254 | 10.20.3.255 | 1022 |
| public | 250 | 10.20.4.0 | /24 | 10.20.4.1 - 10.20.4.254 | 10.20.4.255 | 254 |
| data | 100 | 10.20.5.0 | /25 | 10.20.5.1 - 10.20.5.126 | 10.20.5.127 | 126 |
| management | 20 | 10.20.5.128 | /27 | 10.20.5.129 - 10.20.5.158 | 10.20.5.159 | 30 |

Everything from 10.20.5.160 up to 10.20.255.255 stays free for later.

## NACL for the public subnet (network/nacl.json)

Inbound (source address is matched):

| Rule | Proto | Ports | Source | Action | Purpose |
|---:|---|---|---|---|---|
| 10 | all | all | 198.51.100.0/24 | deny | abusive range, blocked before anything else |
| 100 | tcp | 80 | 0.0.0.0/0 | allow | HTTP from anywhere |
| 110 | tcp | 443 | 0.0.0.0/0 | allow | HTTPS from anywhere |
| 120 | tcp | 22 | 10.20.5.128/27 | allow | SSH only from management |
| 130 | tcp | 1024-65535 | 10.20.0.0/22 | allow | replies from the app subnet to the LB's ephemeral ports |

Outbound (destination address is matched):

| Rule | Proto | Ports | Destination | Action | Purpose |
|---:|---|---|---|---|---|
| 100 | tcp | 8000 | 10.20.0.0/22 | allow | LB forwards requests to the service in app |
| 110 | tcp | 1024-65535 | 0.0.0.0/0 | allow | replies going back to clients' ephemeral ports |

Anything that matches no rule is denied, so there is no need for an explicit "deny all" at the end.

Check: `python tools/nacl_sim.py network/nacl.json network/packets_sample.jsonl --check`
gives 6/6 correct (see `results/nacl_check.txt`).

## Why reply traffic needs its own rules, and why order matters

A NACL is stateless. It does not keep a connection table, so it has no idea that an
outbound packet on port 8000 to the app subnet "belongs" to a request that was allowed
inbound a moment ago. Every packet is judged alone. The reply from the app server comes
back to the load balancer on whatever ephemeral port the LB used (1024 to 65535), so
inbound rule 130 has to allow that range from the app subnet, otherwise the request goes
out and the answer is dropped. The same thing happens on the client side: the client
sent the request to port 443, but the reply is sent to the client's ephemeral port, which
is why outbound rule 110 exists. A stateful firewall (like a security group) would
track the connection and allow the reply automatically; a NACL will not.

Order matters because rules are checked from the lowest number and the first match
decides. If the deny for 198.51.100.0/24 had a higher number than the "allow 443 from
anywhere" rule, a packet from 198.51.100.9 to port 443 would hit the allow rule first and
get through. Giving the deny rule number 10, below every allow rule, means that range is
rejected before the general allow rules are even looked at. The simulator shows this:
packet S04 (198.51.100.9 to port 443) is denied by rule 10 while S01 (192.0.2.55 to port
443) is allowed by rule 110.
