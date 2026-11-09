"""Split 10.20.0.0/16 into the four subnets needed for Task 5.

Rule used: biggest requirement first, each subnet starts right after the
previous one, smallest prefix that still fits (usable hosts = 2^(32-prefix) - 2).
Run:  python scripts/subnet_calc.py        (prints a markdown table)
"""
import ipaddress
import math

BLOCK = ipaddress.ip_network("10.20.0.0/16")
NEEDS = {"app": 1000, "public": 250, "data": 100, "management": 20}


def prefix_for(hosts):
    # need hosts + 2 addresses (network + broadcast)
    bits = math.ceil(math.log2(hosts + 2))
    return 32 - bits


def allocate(block=BLOCK, needs=NEEDS):
    rows = []
    next_addr = int(block.network_address)
    for name, hosts in sorted(needs.items(), key=lambda kv: -kv[1]):
        p = prefix_for(hosts)
        net = ipaddress.ip_network((next_addr, p))
        usable = net.num_addresses - 2
        rows.append({
            "name": name,
            "needed": hosts,
            "network": str(net.network_address),
            "prefix": p,
            "first": str(net.network_address + 1),
            "last": str(net.broadcast_address - 1),
            "broadcast": str(net.broadcast_address),
            "usable": usable,
        })
        next_addr = int(net.broadcast_address) + 1
    return rows


def main():
    rows = allocate()
    print("| Subnet | Hosts needed | Network | Prefix | Usable range | Broadcast | Usable hosts |")
    print("|---|---:|---|---|---|---|---:|")
    for r in rows:
        print(f"| {r['name']} | {r['needed']} | {r['network']} | /{r['prefix']} | "
              f"{r['first']} - {r['last']} | {r['broadcast']} | {r['usable']} |")


if __name__ == "__main__":
    main()
