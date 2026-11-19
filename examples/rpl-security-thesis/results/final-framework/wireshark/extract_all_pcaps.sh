#!/bin/bash
set -euo pipefail

BASE="$(cd "$(dirname "$0")" && pwd)"
CAP="$BASE/captures"
CSV="$BASE/csv"

mkdir -p "$CSV"

if ! command -v tshark >/dev/null 2>&1; then
    echo "ERROR: tshark is not installed."
    exit 1
fi

COUNT=0

find "$CAP" \
  -type f \
  \( -name '*.pcap' -o -name '*.pcapng' \) \
  -print0 |
while IFS= read -r -d '' FILE
do

    COUNT=$((COUNT + 1))

    NAME="$(basename "$FILE")"
    NAME="${NAME%.pcapng}"
    NAME="${NAME%.pcap}"

    OUT="$CSV/${NAME}.csv"

    echo "Extracting: $FILE"

    tshark \
      -r "$FILE" \
      -T fields \
      -E header=y \
      -E separator=, \
      -E quote=d \
      -E occurrence=f \
      -e frame.number \
      -e frame.time_relative \
      -e frame.len \
      -e wpan.src16 \
      -e wpan.dst16 \
      -e ipv6.src \
      -e ipv6.dst \
      -e icmpv6.type \
      -e icmpv6.code \
      -e udp.srcport \
      -e udp.dstport \
      -e data.data \
      > "$OUT"

    echo "Saved: $OUT"

done
