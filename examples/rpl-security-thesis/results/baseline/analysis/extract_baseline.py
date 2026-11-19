import re
import csv
from pathlib import Path

BASE = Path("results/baseline")
OUT = BASE / "analysis"

seeds = [101, 202, 303, 404, 505]

patterns = {
    "state": re.compile(
        r"ID:(?P<id>\d+).*RPL_STATE,"
        r"time=(?P<time>\d+),node=(?P<node>\d+),joined=(?P<joined>\d+),"
        r"rank=(?P<rank>\d+),parent=(?P<parent>\d+),version=(?P<version>\d+),"
        r"etx=(?P<etx>\d+),etx_divisor=(?P<etx_divisor>\d+),"
        r"etx_valid=(?P<etx_valid>\d+),parent_changes=(?P<parent_changes>\d+)"
    ),

    "ctrl": re.compile(
        r"ID:(?P<id>\d+).*RPL_CTRL,"
        r"time=(?P<time>\d+),node=(?P<node>\d+),"
        r"dis_in=(?P<dis_in>\d+),dis_out=(?P<dis_out>\d+),"
        r"dio_in=(?P<dio_in>\d+),dio_out=(?P<dio_out>\d+),"
        r"dao_in=(?P<dao_in>\d+),dao_out=(?P<dao_out>\d+)"
    ),

    "energy": re.compile(
        r"ID:(?P<id>\d+).*ENERGY,"
        r"time=(?P<time>\d+),node=(?P<node>\d+),"
        r"cpu=(?P<cpu>\d+),lpm=(?P<lpm>\d+),"
        r"tx=(?P<tx>\d+),rx=(?P<rx>\d+)"
    ),

    "tx": re.compile(
        r"ID:(?P<id>\d+).*TX,"
        r"time=(?P<time>\d+),node=(?P<node>\d+),"
        r"seq=(?P<seq>\d+),tx_total=(?P<tx_total>\d+)"
    ),

    "server_rx": re.compile(
        r"ID:(?P<id>\d+).*SERVER_RX,"
        r"time=(?P<time>\d+),node=1,total_rx=(?P<total_rx>\d+),"
        r"payload=node=(?P<src>\d+),seq=(?P<seq>\d+)"
    ),

    "unreachable": re.compile(
        r"ID:(?P<id>\d+).*UNREACHABLE,"
        r"time=(?P<time>\d+),node=(?P<node>\d+),count=(?P<count>\d+)"
    ),
}


def write_csv(name, rows):
    if not rows:
        return

    path = OUT / f"{name}.csv"

    fields = list(rows[0].keys())

    with path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


all_rows = {
    "rpl_state": [],
    "rpl_ctrl": [],
    "energy": [],
    "tx": [],
    "server_rx": [],
    "unreachable": [],
}

for seed in seeds:

    log = BASE / f"baseline_seed_{seed}.log"

    with log.open(errors="ignore") as f:

        for line in f:

            for key, pattern in patterns.items():

                m = pattern.search(line)

                if not m:
                    continue

                row = {"seed": seed}
                row.update(m.groupdict())

                if key == "state":
                    all_rows["rpl_state"].append(row)

                elif key == "ctrl":
                    all_rows["rpl_ctrl"].append(row)

                elif key == "energy":
                    all_rows["energy"].append(row)

                elif key == "tx":
                    all_rows["tx"].append(row)

                elif key == "server_rx":
                    all_rows["server_rx"].append(row)

                elif key == "unreachable":
                    all_rows["unreachable"].append(row)

                break


for name, rows in all_rows.items():
    write_csv(name, rows)


print("Baseline extraction complete.")
for name, rows in all_rows.items():
    print(f"{name}: {len(rows)} rows")
