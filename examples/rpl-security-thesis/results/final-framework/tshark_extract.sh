#!/bin/bash
set -e

if [ $# -ne 2 ]; then
  echo "Usage: $0 input.pcapng output.csv"
  exit 1
fi

tshark \
  -r "$1" \
  -T fields \
  -E header=y \
  -E separator=, \
  -E quote=d \
  -e frame.number \
  -e frame.time_relative \
  -e frame.len \
  -e ipv6.src \
  -e ipv6.dst \
  -e icmpv6.type \
  -e icmpv6.code \
  -e udp.srcport \
  -e udp.dstport \
  > "$2"

echo "Saved: $2"
