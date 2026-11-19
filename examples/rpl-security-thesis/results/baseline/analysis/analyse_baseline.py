import csv
import statistics
from pathlib import Path
from collections import defaultdict

BASE = Path("results/baseline/analysis")
SEEDS = [101, 202, 303, 404, 505]
WARMUP = 60


def read_csv(name):
    with (BASE / name).open() as f:
        return list(csv.DictReader(f))


state = read_csv("rpl_state.csv")
ctrl = read_csv("rpl_ctrl.csv")
energy = read_csv("energy.csv")
tx = read_csv("tx.csv")
rx = read_csv("server_rx.csv")
unreachable = read_csv("unreachable.csv")


def mean(values):
    return statistics.mean(values) if values else 0


def stdev(values):
    return statistics.stdev(values) if len(values) > 1 else 0


summary = []

print("\n==============================")
print("BASELINE STEADY-STATE ANALYSIS")
print("==============================")
print(f"Warm-up excluded: first {WARMUP} seconds\n")


for seed in SEEDS:

    # ------------------------------------------------
    # PDR
    # ------------------------------------------------

    seed_tx = [
        r for r in tx
        if int(r["seed"]) == seed
        and int(r["time"]) > WARMUP
    ]

    # Match receptions to packets transmitted after warm-up
    tx_keys = {
        (int(r["node"]), int(r["seq"]))
        for r in seed_tx
    }

    seed_rx = [
        r for r in rx
        if int(r["seed"]) == seed
    ]

    rx_keys = {
        (int(r["src"]), int(r["seq"]))
        for r in seed_rx
    }

    delivered = len(tx_keys & rx_keys)
    sent = len(tx_keys)

    pdr = (delivered / sent * 100) if sent else 0


    # ------------------------------------------------
    # RPL state
    # Exclude root for rank/ETX statistics
    # ------------------------------------------------

    ss = [
        r for r in state
        if int(r["seed"]) == seed
        and int(r["time"]) > WARMUP
    ]

    clients = [
        r for r in ss
        if int(r["node"]) != 1
        and int(r["joined"]) == 1
    ]

    ranks = [int(r["rank"]) for r in clients]

    etx = [
        int(r["etx"]) / int(r["etx_divisor"])
        for r in clients
        if int(r["etx_valid"]) == 1
    ]

    versions = {int(r["version"]) for r in ss}

    max_parent_changes = max(
        (int(r["parent_changes"]) for r in ss),
        default=0
    )


    # ------------------------------------------------
    # RPL control rates
    # Calculate cumulative-counter delta / elapsed time
    # ------------------------------------------------

    ctrl_by_node = defaultdict(list)

    for r in ctrl:
        if int(r["seed"]) == seed and int(r["time"]) >= WARMUP:
            ctrl_by_node[int(r["node"])].append(r)

    rates = {
        "dis_in": [],
        "dis_out": [],
        "dio_in": [],
        "dio_out": [],
        "dao_in": [],
        "dao_out": [],
    }

    for node, rows in ctrl_by_node.items():

        rows.sort(key=lambda x: int(x["time"]))

        if len(rows) < 2:
            continue

        first = rows[0]
        last = rows[-1]

        elapsed = int(last["time"]) - int(first["time"])

        if elapsed <= 0:
            continue

        minutes = elapsed / 60.0

        for field in rates:
            delta = int(last[field]) - int(first[field])
            rates[field].append(delta / minutes)


    # ------------------------------------------------
    # Energy radio-time deltas
    # ------------------------------------------------

    energy_by_node = defaultdict(list)

    for r in energy:
        if int(r["seed"]) == seed and int(r["time"]) >= WARMUP:
            energy_by_node[int(r["node"])].append(r)

    tx_radio_fraction = []
    rx_radio_fraction = []

    for node, rows in energy_by_node.items():

        rows.sort(key=lambda x: int(x["time"]))

        if len(rows) < 2:
            continue

        first = rows[0]
        last = rows[-1]

        elapsed_ticks = (
            int(last["cpu"]) + int(last["lpm"])
            - int(first["cpu"]) - int(first["lpm"])
        )

        if elapsed_ticks <= 0:
            continue

        delta_tx = int(last["tx"]) - int(first["tx"])
        delta_rx = int(last["rx"]) - int(first["rx"])

        tx_radio_fraction.append(delta_tx / elapsed_ticks)
        rx_radio_fraction.append(delta_rx / elapsed_ticks)


    # ------------------------------------------------
    # Unreachable events after warm-up
    # ------------------------------------------------

    unreach_after = [
        r for r in unreachable
        if int(r["seed"]) == seed
        and int(r["time"]) > WARMUP
    ]


    result = {
        "seed": seed,
        "tx_packets": sent,
        "delivered_packets": delivered,
        "pdr_percent": round(pdr, 4),

        "rank_min": min(ranks) if ranks else 0,
        "rank_mean": round(mean(ranks), 2),
        "rank_max": max(ranks) if ranks else 0,

        "etx_min": round(min(etx), 4) if etx else 0,
        "etx_mean": round(mean(etx), 4),
        "etx_max": round(max(etx), 4) if etx else 0,

        "versions": ";".join(map(str, sorted(versions))),
        "max_parent_changes": max_parent_changes,

        "dis_in_per_min_mean": round(mean(rates["dis_in"]), 4),
        "dis_out_per_min_mean": round(mean(rates["dis_out"]), 4),

        "dio_in_per_min_mean": round(mean(rates["dio_in"]), 4),
        "dio_in_per_min_max": round(max(rates["dio_in"]), 4)
            if rates["dio_in"] else 0,

        "dio_out_per_min_mean": round(mean(rates["dio_out"]), 4),
        "dio_out_per_min_max": round(max(rates["dio_out"]), 4)
            if rates["dio_out"] else 0,

        "dao_in_per_min_mean": round(mean(rates["dao_in"]), 4),
        "dao_out_per_min_mean": round(mean(rates["dao_out"]), 4),

        "radio_tx_fraction_mean": round(mean(tx_radio_fraction), 6),
        "radio_rx_fraction_mean": round(mean(rx_radio_fraction), 6),

        "unreachable_records_after_warmup": len(unreach_after),
    }

    summary.append(result)

    print(f"Seed {seed}")
    print(f"  PDR                  : {pdr:.4f}% ({delivered}/{sent})")
    print(
        f"  Rank min/mean/max    : "
        f"{result['rank_min']} / "
        f"{result['rank_mean']} / "
        f"{result['rank_max']}"
    )
    print(
        f"  ETX min/mean/max     : "
        f"{result['etx_min']} / "
        f"{result['etx_mean']} / "
        f"{result['etx_max']}"
    )
    print(f"  DODAG version(s)     : {result['versions']}")
    print(f"  Max parent changes   : {max_parent_changes}")
    print(
        f"  DIO-in rate mean/max : "
        f"{result['dio_in_per_min_mean']} / "
        f"{result['dio_in_per_min_max']} per min"
    )
    print(
        f"  DIO-out mean/max     : "
        f"{result['dio_out_per_min_mean']} / "
        f"{result['dio_out_per_min_max']} per min"
    )
    print(
        f"  DIS-out mean         : "
        f"{result['dis_out_per_min_mean']} per min"
    )
    print(
        f"  DAO-out mean         : "
        f"{result['dao_out_per_min_mean']} per min"
    )
    print(
        f"  Unreachable >60s     : "
        f"{result['unreachable_records_after_warmup']}"
    )
    print()


# ------------------------------------------------
# Save per-seed summary
# ------------------------------------------------

out = BASE / "baseline_steady_state_summary.csv"

with out.open("w", newline="") as f:
    writer = csv.DictWriter(
        f,
        fieldnames=summary[0].keys()
    )
    writer.writeheader()
    writer.writerows(summary)


# ------------------------------------------------
# Across-seed baseline
# ------------------------------------------------

pdrs = [r["pdr_percent"] for r in summary]
rank_means = [r["rank_mean"] for r in summary]
etx_means = [r["etx_mean"] for r in summary]
dio_in_maxes = [r["dio_in_per_min_max"] for r in summary]
dio_out_maxes = [r["dio_out_per_min_max"] for r in summary]


print("==============================")
print("ACROSS ALL FIVE BASELINE RUNS")
print("==============================")

print(
    f"PDR mean ± SD       : "
    f"{mean(pdrs):.4f}% ± {stdev(pdrs):.4f}"
)

print(
    f"PDR observed range  : "
    f"{min(pdrs):.4f}% - {max(pdrs):.4f}%"
)

print(
    f"Rank mean range     : "
    f"{min(rank_means):.2f} - {max(rank_means):.2f}"
)

print(
    f"ETX mean range      : "
    f"{min(etx_means):.4f} - {max(etx_means):.4f}"
)

print(
    f"Highest DIO-in rate : "
    f"{max(dio_in_maxes):.4f} messages/min"
)

print(
    f"Highest DIO-out rate: "
    f"{max(dio_out_maxes):.4f} messages/min"
)

print(
    "DODAG versions      : "
    + ", ".join(sorted(set(r["versions"] for r in summary)))
)

print(
    f"Highest parent-change count: "
    f"{max(r['max_parent_changes'] for r in summary)}"
)

print(
    "\nSaved:",
    BASE / "baseline_steady_state_summary.csv"
)
