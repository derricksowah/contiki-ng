# RPL Security Thesis Reproduction Guide

## Project

**Title:**  
A Specification-Based Detection and Mitigation Framework for RPL Routing Attacks in Simulated IPv6 Wireless Sensor Networks

Evaluated attacks:

- Blackhole
- Grayhole
- Decreased Rank
- DODAG Version Number
- DIS Flooding

All traffic is generated within Contiki-NG/Cooja. Wireshark and tshark are used for packet-level validation.

## Repositories

Main repository:

```text
https://github.com/derricksowah/contiki-ng
```

Branch:

```text
codespace-fuzzy-space-acorn-xrwrp6r5w9gjcp4pv
```

Modified Cooja fork:

```text
https://github.com/derricksowah/cooja
```

Required Cooja commit:

```text
58aa805
```

## Setup

```bash
git clone --branch codespace-fuzzy-space-acorn-xrwrp6r5w9gjcp4pv \
https://github.com/derricksowah/contiki-ng.git

cd contiki-ng
git submodule update --init --recursive

cd tools/cooja
git remote set-url origin https://github.com/derricksowah/cooja.git
git fetch origin
git checkout 58aa805

cd ../..
```

Verify Cooja:

```bash
cd tools/cooja
git rev-parse --short HEAD
```

Expected:

```text
58aa805
```

## Thesis Project

```text
examples/rpl-security-thesis
```

Main custom implementation:

```text
thesis-security.c
thesis-security.h
rpl-metrics.c
rpl-metrics.h
udp-client.c
udp-server.c
project-conf.h
```

Custom Cooja PCAP plugin:

```text
tools/cooja/java/org/contikios/cooja/plugins/HeadlessPcapLogger.java
```

## Experimental Configuration

```text
Nodes: 25
Root: Node 1
Clients: Nodes 2-25
RPL: RPL Lite
IPv6/6LoWPAN
MAC: CSMA
IEEE 802.15.4
Channel: 26
PAN ID: 0xabcd
Simulation duration: 900 s
Nominal attack start: 120 s
Seeds: 101, 202, 303, 404, 505
```

Attack nodes:

```text
Node 12: Blackhole, Grayhole, DODAG Version Number, DIS Flooding
Node 19: Decreased Rank
```

## Build

```bash
cd examples/rpl-security-thesis
make clean
make TARGET=cooja
```

## Configuration Flags

Defined in:

```text
project-conf.h
```

Relevant flags:

```c
THESIS_DECREASED_RANK_ATTACK
THESIS_BLACKHOLE_ATTACK
THESIS_GRAYHOLE_ATTACK
THESIS_DODAG_VERSION_ATTACK
THESIS_DIS_FLOOD_ATTACK
THESIS_SECURITY_FRAMEWORK
```

Baseline:

```c
THESIS_DECREASED_RANK_ATTACK 0
THESIS_BLACKHOLE_ATTACK 0
THESIS_GRAYHOLE_ATTACK 0
THESIS_DODAG_VERSION_ATTACK 0
THESIS_DIS_FLOOD_ATTACK 0
THESIS_SECURITY_FRAMEWORK 0
```

Attack-only:

```text
selected attack flag = 1
THESIS_SECURITY_FRAMEWORK = 0
all other attack flags = 0
```

Mitigated:

```text
selected attack flag = 1
THESIS_SECURITY_FRAMEWORK = 1
all other attack flags = 0
```

Rebuild after any flag change.

## Run Command

From:

```bash
cd tools/cooja
```

General form:

```bash
./gradlew run --args='--no-gui --autostart --random-seed=SEED ../../examples/rpl-security-thesis/SCENARIO.csc'
```

Baseline example:

```bash
./gradlew run --args='--no-gui --autostart --random-seed=101 ../../examples/rpl-security-thesis/baseline.csc'
```

Repeat each condition with:

```text
101
202
303
404
505
```

## Scenario Mapping

```text
Baseline       -> baseline.csc
Blackhole      -> blackhole.csc
Grayhole       -> grayhole.csc
Decreased Rank -> decreased-rank.csc
```

DODAG Version Number and DIS Flooding scenario files are in:

```text
examples/rpl-security-thesis
```

## Experiment Matrix

Run:

```text
Baseline:
5 seeds

Blackhole:
5 attack-only
5 mitigated

Grayhole:
5 attack-only
5 mitigated

Decreased Rank:
5 attack-only
5 mitigated

DODAG Version Number:
5 attack-only
5 mitigated

DIS Flooding:
5 attack-only
5 mitigated
```

Preserve `COOJA.testlog` for every run.

## Relevant Log Records

```text
TX
RX
SERVER_RX
RPL_STATE
RPL_CTRL
ENERGY
SECURITY_EVIDENCE
DETECTION
MITIGATION
RECOVERY
```

Typical checks:

```bash
grep "RPL_STATE" COOJA.testlog
grep "RPL_CTRL" COOJA.testlog
grep "ENERGY" COOJA.testlog
grep -E "SECURITY_EVIDENCE|DETECTION|MITIGATION|RECOVERY" COOJA.testlog
```

## Results

```text
examples/rpl-security-thesis/results
```

Final framework outputs:

```text
examples/rpl-security-thesis/results/final-framework
```

Wireshark material:

```text
examples/rpl-security-thesis/results/final-framework/wireshark
```

## PCAP Capture

The modified Cooja plugin generates IEEE 802.15.4 PCAP output.

Default filename:

```text
headless-radiolog.pcap
```

Representative captures are stored under:

```text
results/final-framework/wireshark/captures
```

## tshark Validation

RPL:

```bash
tshark -r capture.pcap -Y "icmpv6.type == 155"
```

DIS:

```bash
tshark -r capture.pcap -Y "icmpv6.type == 155 && icmpv6.code == 0"
```

DIO:

```bash
tshark -r capture.pcap -Y "icmpv6.type == 155 && icmpv6.code == 1"
```

DAO:

```bash
tshark -r capture.pcap -Y "icmpv6.type == 155 && icmpv6.code == 2"
```

Count:

```bash
tshark -r capture.pcap -Y "FILTER" | wc -l
```

## Metrics

PDR is sequence-aware using unique:

```text
(source, sequence number)
```

Detection latency:

```text
detection_time - 120 s
```

Service-recovery latency:

```text
first successful root reception after mitigation
-
mitigation time
```

Energest values are reported as ticks.

## Detection Thresholds

```text
Blackhole: 3
Grayhole: 3
Decreased Rank: 1
DODAG Version Number: 1
DIS Flooding: 3
```

## Reproduction Checklist

A complete reproduction should produce:

```text
5 baseline runs
25 attack-only runs
25 mitigated runs
saved COOJA.testlog files
RPL_STATE / RPL_CTRL / ENERGY records
DETECTION / MITIGATION / RECOVERY records
representative PCAP captures
tshark/Wireshark validation
PDR and latency results
```

## Important

The live detection and mitigation framework operates inside Contiki-NG/Cooja.

Wireshark and tshark are used for independent packet-level validation.
