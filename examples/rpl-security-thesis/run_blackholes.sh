#!/bin/bash

set -e

COOJA_DIR="/workspaces/contiki-ng/tools/cooja"
PROJECT_DIR="/workspaces/contiki-ng/examples/rpl-security-thesis"
RESULT_DIR="$PROJECT_DIR/results/blackhole"

mkdir -p "$RESULT_DIR"

SEEDS=(101 202 303 404 505)

for SEED in "${SEEDS[@]}"
do
    echo "========================================"
    echo "Running Blackhole attack seed $SEED"
    echo "Attacker node: 9"
    echo "========================================"

    cd "$COOJA_DIR"

    ./gradlew run \
      --args="--no-gui --autostart --random-seed=$SEED ../../examples/rpl-security-thesis/blackhole.csc"

    cp COOJA.testlog \
      "$RESULT_DIR/blackhole_seed_${SEED}.log"

    DROPS=$(grep -c "BLACKHOLE_DROP" COOJA.testlog || true)

    echo "Seed $SEED Blackhole drops: $DROPS"
    echo "Saved blackhole_seed_${SEED}.log"
done

echo "All Blackhole experiments completed."
