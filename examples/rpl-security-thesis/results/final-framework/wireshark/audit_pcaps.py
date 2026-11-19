from pathlib import Path
import csv

BASE = Path(__file__).resolve().parent
CSV_DIR = BASE / "csv"

rows = []

for path in sorted(CSV_DIR.glob("*.csv")):

    total = 0
    ipv6 = 0
    icmpv6 = 0
    udp = 0

    with path.open(errors="ignore") as f:

        reader = csv.DictReader(f)

        for r in reader:

            total += 1

            if r.get("ipv6.src") or r.get("ipv6.dst"):
                ipv6 += 1

            if r.get("icmpv6.type"):
                icmpv6 += 1

            if r.get("udp.srcport") or r.get("udp.dstport"):
                udp += 1

    rows.append({
        "capture": path.stem,
        "frames": total,
        "ipv6_frames": ipv6,
        "icmpv6_frames": icmpv6,
        "udp_frames": udp,
    })


out = BASE / "packet_capture_summary.csv"

if rows:

    with out.open("w", newline="") as f:

        writer = csv.DictWriter(
            f,
            fieldnames=rows[0].keys()
        )

        writer.writeheader()
        writer.writerows(rows)

    print("===== PACKET CAPTURE SUMMARY =====")

    for r in rows:

        print(
            f"{r['capture']:35} "
            f"frames={r['frames']:6} "
            f"IPv6={r['ipv6_frames']:6} "
            f"ICMPv6={r['icmpv6_frames']:6} "
            f"UDP={r['udp_frames']:6}"
        )

    print()
    print("Saved:", out)

else:

    print("No extracted CSV files found.")

