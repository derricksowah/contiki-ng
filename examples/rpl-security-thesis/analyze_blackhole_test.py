from pathlib import Path
import re
from collections import defaultdict

logfile = Path("results/blackhole/blackhole_test_seed101.log")

tx_re = re.compile(
    r"TX,time=(?P<time>\d+),node=(?P<node>\d+),seq=(?P<seq>\d+),tx_total=(?P<tx>\d+)"
)

rx_re = re.compile(
    r"SERVER_RX,time=(?P<time>\d+),node=1,total_rx=(?P<total>\d+),"
    r"payload=node=(?P<src>\d+),seq=(?P<seq>\d+)"
)

drop_re = re.compile(
    r"BLACKHOLE_DROP,node=(?P<node>\d+),proto=(?P<proto>\d+)"
)

tx = defaultdict(set)
rx = defaultdict(set)
drops = 0

for line in logfile.read_text(errors="ignore").splitlines():

    m = tx_re.search(line)
    if m:
        node = int(m.group("node"))
        seq = int(m.group("seq"))
        tx[node].add(seq)

    m = rx_re.search(line)
    if m:
        node = int(m.group("src"))
        seq = int(m.group("seq"))
        rx[node].add(seq)

    if drop_re.search(line):
        drops += 1

print("\n===== BLACKHOLE TEST RESULTS =====\n")

total_tx = 0
total_rx = 0

for node in range(2, 26):
    sent = len(tx[node])
    received = len(rx[node])

    total_tx += sent
    total_rx += received

    pdr = (received / sent * 100) if sent else 0

    print(
        f"Node {node:2d}: "
        f"TX={sent:3d} "
        f"RX={received:3d} "
        f"Lost={sent-received:3d} "
        f"PDR={pdr:7.3f}%"
    )

overall = total_rx / total_tx * 100 if total_tx else 0

print("\n--------------------------------")
print(f"Total TX           : {total_tx}")
print(f"Total root RX      : {total_rx}")
print(f"Total packet loss  : {total_tx-total_rx}")
print(f"Overall PDR        : {overall:.4f}%")
print(f"Blackhole drops    : {drops}")
print("--------------------------------")
