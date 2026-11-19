from pathlib import Path
import re
import csv
import statistics

RESULT_DIR = Path("results/baseline")
OUTPUT_DIR = RESULT_DIR / "analysis"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

SEEDS = [101, 202, 303, 404, 505]

rpl_state_re = re.compile(
    r"RPL_STATE,time=(?P<time>\d+),node=(?P<node>\d+),joined=(?P<joined>\d+),"
    r"rank=(?P<rank>\d+),parent=(?P<parent>\d+),version=(?P<version>\d+),"
    r"etx=(?P<etx>\d+),etx_divisor=(?P<divisor>\d+),etx_valid=(?P<valid>\d+),"
    r"parent_changes=(?P<parent_changes>\d+)"
)

ctrl_re = re.compile(
    r"RPL_CTRL,time=(?P<time>\d+),node=(?P<node>\d+),"
    r"dis_in=(?P<dis_in>\d+),dis_out=(?P<dis_out>\d+),"
    r"dio_in=(?P<dio_in>\d+),dio_out=(?P<dio_out>\d+),"
    r"dao_in=(?P<dao_in>\d+),dao_out=(?P<dao_out>\d+)"
)

tx_re = re.compile(
    r"TX,time=(?P<time>\d+),node=(?P<node>\d+),seq=(?P<seq>\d+),tx_total=(?P<tx>\d+)"
)

server_rx_re = re.compile(
    r"SERVER_RX,time=(?P<time>\d+),node=1,total_rx=(?P<total>\d+),payload=node=(?P<src>\d+),seq=(?P<seq>\d+)"
)

energy_re = re.compile(
    r"ENERGY,time=(?P<time>\d+),node=(?P<node>\d+),cpu=(?P<cpu>\d+),"
    r"lpm=(?P<lpm>\d+),tx=(?P<tx>\d+),rx=(?P<rx>\d+)"
)

summary_rows = []

for seed in SEEDS:
    logfile = RESULT_DIR / f"baseline_seed_{seed}.log"

    if not logfile.exists():
        print(f"Missing {logfile}")
        continue

    states = []
    ctrls = []
    energies = []

    tx_packets = set()
    received_packets = set()

    for line in logfile.read_text(errors="ignore").splitlines():

        m = rpl_state_re.search(line)
        if m:
            d = {k: int(v) for k, v in m.groupdict().items()}
            states.append(d)
            continue

        m = ctrl_re.search(line)
        if m:
            d = {k: int(v) for k, v in m.groupdict().items()}
            ctrls.append(d)
            continue

        m = tx_re.search(line)
        if m:
            d = {k: int(v) for k, v in m.groupdict().items()}
            tx_packets.add((d["node"], d["seq"]))
            continue

        m = server_rx_re.search(line)
        if m:
            d = {k: int(v) for k, v in m.groupdict().items()}
            received_packets.add((d["src"], d["seq"]))
            continue

        m = energy_re.search(line)
        if m:
            d = {k: int(v) for k, v in m.groupdict().items()}
            energies.append(d)

    # Ignore first 120 seconds for steady-state analysis
    steady_states = [
        s for s in states
        if s["time"] >= 120 and s["node"] != 1 and s["joined"] == 1
    ]

    steady_ctrl = [
        c for c in ctrls
        if c["time"] >= 120
    ]

    ranks = [s["rank"] for s in steady_states]
    etxs = [
        s["etx"] / s["divisor"]
        for s in steady_states
        if s["valid"] == 1 and s["divisor"] > 0
    ]

    versions = [s["version"] for s in steady_states]
    parent_changes = [s["parent_changes"] for s in steady_states]

    pdr = (
        len(received_packets) / len(tx_packets) * 100
        if tx_packets else 0
    )

    final_ctrl = {}
    for c in ctrls:
        final_ctrl[c["node"]] = c

    total_dis_out = sum(x["dis_out"] for x in final_ctrl.values())
    total_dio_out = sum(x["dio_out"] for x in final_ctrl.values())
    total_dao_out = sum(x["dao_out"] for x in final_ctrl.values())

    final_energy = {}
    for e in energies:
        final_energy[e["node"]] = e

    total_radio_tx = sum(x["tx"] for x in final_energy.values())
    total_radio_rx = sum(x["rx"] for x in final_energy.values())

    joined_final = {}
    for s in states:
        joined_final[s["node"]] = s["joined"]

    all_joined = int(
        len(joined_final) == 25 and
        all(v == 1 for v in joined_final.values())
    )

    row = {
        "seed": seed,
        "pdr_percent": round(pdr, 4),
        "rank_min": min(ranks) if ranks else "",
        "rank_max": max(ranks) if ranks else "",
        "rank_mean": round(statistics.mean(ranks), 3) if ranks else "",
        "etx_min": round(min(etxs), 4) if etxs else "",
        "etx_max": round(max(etxs), 4) if etxs else "",
        "etx_mean": round(statistics.mean(etxs), 4) if etxs else "",
        "version_min": min(versions) if versions else "",
        "version_max": max(versions) if versions else "",
        "max_parent_changes": max(parent_changes) if parent_changes else "",
        "total_dis_out": total_dis_out,
        "total_dio_out": total_dio_out,
        "total_dao_out": total_dao_out,
        "radio_tx_time": total_radio_tx,
        "radio_rx_time": total_radio_rx,
        "all_nodes_joined_final": all_joined,
        "tx_packets": len(tx_packets),
        "root_received_packets": len(received_packets),
    }

    summary_rows.append(row)

summary_file = OUTPUT_DIR / "baseline_summary.csv"

with summary_file.open("w", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=summary_rows[0].keys())
    writer.writeheader()
    writer.writerows(summary_rows)

print("\n===== BASELINE SUMMARY =====\n")

for row in summary_rows:
    print(
        f"Seed {row['seed']}: "
        f"PDR={row['pdr_percent']}%, "
        f"Rank={row['rank_min']}..{row['rank_max']}, "
        f"ETX={row['etx_min']}..{row['etx_max']}, "
        f"Version={row['version_min']}..{row['version_max']}, "
        f"ParentChangesMax={row['max_parent_changes']}, "
        f"DISout={row['total_dis_out']}, "
        f"DIOout={row['total_dio_out']}, "
        f"DAOout={row['total_dao_out']}, "
        f"AllJoined={row['all_nodes_joined_final']}"
    )

print(f"\nSaved: {summary_file}")
