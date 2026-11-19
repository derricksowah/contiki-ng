from pathlib import Path
import re
import csv
import statistics
from collections import defaultdict

BASE_DIR = Path("results/baseline")
ATTACK_DIR = Path("results/blackhole")
OUT_DIR = ATTACK_DIR / "analysis"
OUT_DIR.mkdir(parents=True, exist_ok=True)

SEEDS = [101, 202, 303, 404, 505]

tx_re = re.compile(
    r"TX,time=(?P<time>\d+),node=(?P<node>\d+),seq=(?P<seq>\d+),tx_total=(?P<tx>\d+)"
)

rx_re = re.compile(
    r"SERVER_RX,time=(?P<time>\d+),node=1,total_rx=(?P<total>\d+),"
    r"payload=node=(?P<src>\d+),seq=(?P<seq>\d+)"
)

state_re = re.compile(
    r"RPL_STATE,time=(?P<time>\d+),node=(?P<node>\d+),joined=(?P<joined>\d+),"
    r"rank=(?P<rank>\d+),parent=(?P<parent>\d+),version=(?P<version>\d+),"
    r"etx=(?P<etx>\d+),etx_divisor=(?P<divisor>\d+),etx_valid=(?P<valid>\d+),"
    r"parent_changes=(?P<changes>\d+)"
)

ctrl_re = re.compile(
    r"RPL_CTRL,time=(?P<time>\d+),node=(?P<node>\d+),"
    r"dis_in=(?P<dis_in>\d+),dis_out=(?P<dis_out>\d+),"
    r"dio_in=(?P<dio_in>\d+),dio_out=(?P<dio_out>\d+),"
    r"dao_in=(?P<dao_in>\d+),dao_out=(?P<dao_out>\d+)"
)

energy_re = re.compile(
    r"ENERGY,time=(?P<time>\d+),node=(?P<node>\d+),cpu=(?P<cpu>\d+),"
    r"lpm=(?P<lpm>\d+),tx=(?P<tx>\d+),rx=(?P<rx>\d+)"
)

drop_re = re.compile(
    r"BLACKHOLE_DROP,node=(?P<node>\d+),proto=(?P<proto>\d+)"
)

def analyse(logfile):
    tx = defaultdict(set)
    rx = defaultdict(set)

    states = []
    ctrls = []
    energies = []
    drops = 0

    for line in logfile.read_text(errors="ignore").splitlines():

        m = tx_re.search(line)
        if m:
            d = {k: int(v) for k, v in m.groupdict().items()}
            tx[d["node"]].add(d["seq"])
            continue

        m = rx_re.search(line)
        if m:
            d = {k: int(v) for k, v in m.groupdict().items()}
            rx[d["src"]].add(d["seq"])
            continue

        m = state_re.search(line)
        if m:
            states.append({k: int(v) for k, v in m.groupdict().items()})
            continue

        m = ctrl_re.search(line)
        if m:
            ctrls.append({k: int(v) for k, v in m.groupdict().items()})
            continue

        m = energy_re.search(line)
        if m:
            energies.append({k: int(v) for k, v in m.groupdict().items()})
            continue

        if drop_re.search(line):
            drops += 1

    total_tx = sum(len(v) for v in tx.values())
    total_rx = sum(len(v) for v in rx.values())

    pdr = total_rx / total_tx * 100 if total_tx else 0

    node_pdr = {}
    for node in range(2, 26):
        sent = len(tx[node])
        received = len(rx[node])
        node_pdr[node] = received / sent * 100 if sent else 0

    # Steady state after 120 seconds
    steady_states = [
        s for s in states
        if s["time"] >= 120 and s["node"] != 1 and s["joined"] == 1
    ]

    ranks = [s["rank"] for s in steady_states]

    etxs = [
        s["etx"] / s["divisor"]
        for s in steady_states
        if s["valid"] and s["divisor"] > 0
    ]

    changes = [s["changes"] for s in steady_states]

    final_ctrl = {}
    for c in ctrls:
        final_ctrl[c["node"]] = c

    final_energy = {}
    for e in energies:
        final_energy[e["node"]] = e

    return {
        "pdr": pdr,
        "total_tx": total_tx,
        "total_rx": total_rx,
        "loss": total_tx - total_rx,
        "drops": drops,
        "rank_mean": statistics.mean(ranks) if ranks else 0,
        "rank_min": min(ranks) if ranks else 0,
        "rank_max": max(ranks) if ranks else 0,
        "etx_mean": statistics.mean(etxs) if etxs else 0,
        "etx_min": min(etxs) if etxs else 0,
        "etx_max": max(etxs) if etxs else 0,
        "max_parent_changes": max(changes) if changes else 0,
        "dis_out": sum(c["dis_out"] for c in final_ctrl.values()),
        "dio_out": sum(c["dio_out"] for c in final_ctrl.values()),
        "dao_out": sum(c["dao_out"] for c in final_ctrl.values()),
        "radio_tx": sum(e["tx"] for e in final_energy.values()),
        "radio_rx": sum(e["rx"] for e in final_energy.values()),
        "node_pdr": node_pdr
    }

rows = []

print("\n===== BASELINE VS BLACKHOLE =====\n")

for seed in SEEDS:
    base = analyse(BASE_DIR / f"baseline_seed_{seed}.log")
    attack = analyse(ATTACK_DIR / f"blackhole_seed_{seed}.log")

    affected = [
        node for node, pdr in attack["node_pdr"].items()
        if pdr < 99.0
    ]

    row = {
        "seed": seed,
        "baseline_pdr": round(base["pdr"], 4),
        "blackhole_pdr": round(attack["pdr"], 4),
        "pdr_drop_points": round(base["pdr"] - attack["pdr"], 4),
        "blackhole_drops": attack["drops"],
        "packet_loss": attack["loss"],
        "affected_nodes": " ".join(map(str, affected)),
        "baseline_rank_mean": round(base["rank_mean"], 3),
        "blackhole_rank_mean": round(attack["rank_mean"], 3),
        "baseline_etx_mean": round(base["etx_mean"], 4),
        "blackhole_etx_mean": round(attack["etx_mean"], 4),
        "baseline_parent_changes": base["max_parent_changes"],
        "blackhole_parent_changes": attack["max_parent_changes"],
        "baseline_dis_out": base["dis_out"],
        "blackhole_dis_out": attack["dis_out"],
        "baseline_dio_out": base["dio_out"],
        "blackhole_dio_out": attack["dio_out"],
        "baseline_dao_out": base["dao_out"],
        "blackhole_dao_out": attack["dao_out"],
        "baseline_radio_tx": base["radio_tx"],
        "blackhole_radio_tx": attack["radio_tx"],
    }

    rows.append(row)

    print(
        f"Seed {seed}: "
        f"Baseline PDR={row['baseline_pdr']}% | "
        f"Blackhole PDR={row['blackhole_pdr']}% | "
        f"Drop={row['pdr_drop_points']} points | "
        f"BH drops={row['blackhole_drops']} | "
        f"Affected={row['affected_nodes']}"
    )

outfile = OUT_DIR / "baseline_vs_blackhole.csv"

with outfile.open("w", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=rows[0].keys())
    writer.writeheader()
    writer.writerows(rows)

print("\n===== CROSS-SEED MEANS =====\n")

print(
    f"Baseline mean PDR : "
    f"{statistics.mean(r['baseline_pdr'] for r in rows):.4f}%"
)

print(
    f"Blackhole mean PDR: "
    f"{statistics.mean(r['blackhole_pdr'] for r in rows):.4f}%"
)

print(
    f"Mean PDR reduction: "
    f"{statistics.mean(r['pdr_drop_points'] for r in rows):.4f} percentage points"
)

print(
    f"Mean BH drops/run : "
    f"{statistics.mean(r['blackhole_drops'] for r in rows):.2f}"
)

print(f"\nSaved: {outfile}")
