#!/bin/bash

set -e

COOJA_DIR="/workspaces/contiki-ng/tools/cooja"
PROJECT_DIR="/workspaces/contiki-ng/examples/rpl-security-thesis"
RESULT_DIR="$PROJECT_DIR/results/baseline"

mkdir -p "$RESULT_DIR"

SEEDS=(101 202 303 404 505)

for SEED in "${SEEDS[@]}"
do
    echo "========================================"
    echo "Running baseline seed $SEED"
    echo "========================================"

    cd "$COOJA_DIR"

    ./gradlew run \
      --args="--no-gui --autostart --random-seed=$SEED ../../examples/rpl-security-thesis/baseline.csc"

    cp COOJA.testlog "$RESULT_DIR/baseline_seed_${SEED}.log"

    echo "Saved baseline_seed_${SEED}.log"
done

echo "All baseline runs completed."
