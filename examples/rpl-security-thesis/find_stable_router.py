from pathlib import Path
import re
from collections import defaultdict

RESULT_DIR = Path("results/baseline")
SEEDS = [101, 202, 303, 404, 505]

state_re = re.compile(
    r"RPL_STATE,time=(?P<time>\d+),node=(?P<node>\d+),joined=(?P<joined>\d+),"
    r"rank=(?P<rank>\d+),parent=(?P<parent>\d+),version=(?P<version>\d+),"
    r"etx=(?P<etx>\d+),etx_divisor=(?P<divisor>\d+),etx_valid=(?P<valid>\d+),"
    r"parent_changes=(?P<changes>\d+)"
)

all_children = defaultdict(dict)

for seed in SEEDS:
    logfile = RESULT_DIR / f"baseline_seed_{seed}.log"

    latest = {}

    for line in logfile.read_text(errors="ignore").splitlines():
        m = state_re.search(line)
        if not m:
            continue

        d = {k: int(v) for k, v in m.groupdict().items()}
        node = d["node"]

        if node not in latest or d["time"] > latest[node]["time"]:
            latest[node] = d

    children = defaultdict(list)

    for node, d in latest.items():
        parent = d["parent"]

        if node != 1 and d["joined"] == 1 and parent != 0:
            children[parent].append(node)

    print(f"\n===== SEED {seed} =====")

    for parent in sorted(children):
        if parent != 1:
            print(
                f"Router {parent:2d}: "
                f"{len(children[parent])} children -> "
                f"{children[parent]}"
            )

    for router in range(2, 26):
        all_children[router][seed] = len(children.get(router, []))


print("\n===== CROSS-SEED ROUTER STABILITY =====\n")

scores = []

for router in range(2, 26):
    counts = [all_children[router][seed] for seed in SEEDS]

    seeds_with_children = sum(1 for x in counts if x > 0)
    total_children = sum(counts)
    minimum_children = min(counts)

    scores.append(
        (
            seeds_with_children,
            minimum_children,
            total_children,
            router,
            counts
        )
    )

for seeds_with_children, minimum_children, total_children, router, counts in sorted(
    scores, reverse=True
):
    if seeds_with_children > 0:
        print(
            f"Node {router:2d}: "
            f"active in {seeds_with_children}/5 seeds, "
            f"children per seed={counts}, "
            f"minimum={minimum_children}, "
            f"total={total_children}"
        )
