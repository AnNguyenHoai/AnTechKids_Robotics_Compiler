#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
import math
import re
import statistics
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable, Sequence

LINE_RE = re.compile(
    r"^\[LINE-RESPONSE\]\s+"
    r"t=(?P<t>\d+)us\s+"
    r"mask=0x(?P<mask>[0-9A-Fa-f]{2})\s+"
    r"prev=(?P<prev>---|0x?[0-9A-Fa-f]{1,2}|\d+)\s+"
    r"loop=(?P<loop>\d+)us\s+\|\s+"
    r"sensor=(?P<sensor>\d+)us\s+"
    r"control=(?P<control>\d+)us\s+"
    r"output=(?P<output>\d+)us\s+"
    r"total=(?P<total>\d+)us\s+\|\s+"
    r"cmd\s+L=(?P<left>-?\d+)\s+R=(?P<right>-?\d+)\s*$"
)


@dataclass(frozen=True)
class LineResponseSample:
    t_us: int
    mask: int
    previous: str
    loop_us: int
    sensor_us: int
    control_us: int
    output_us: int
    total_us: int
    left_cmd: int
    right_cmd: int


def parse_line(line: str) -> LineResponseSample | None:
    match = LINE_RE.match(line.strip())
    if not match:
        return None
    g = match.groupdict()
    return LineResponseSample(
        t_us=int(g["t"]),
        mask=int(g["mask"], 16) & 0x1F,
        previous=g["prev"],
        loop_us=int(g["loop"]),
        sensor_us=int(g["sensor"]),
        control_us=int(g["control"]),
        output_us=int(g["output"]),
        total_us=int(g["total"]),
        left_cmd=int(g["left"]),
        right_cmd=int(g["right"]),
    )


def parse_lines(lines: Iterable[str]) -> list[LineResponseSample]:
    return [sample for line in lines if (sample := parse_line(line)) is not None]


def _percentile(values: Sequence[int], percentile: float) -> float:
    if not values:
        raise ValueError("cannot compute percentile of empty sample set")
    ordered = sorted(values)
    if len(ordered) == 1:
        return float(ordered[0])
    rank = (len(ordered) - 1) * percentile
    lower = math.floor(rank)
    upper = math.ceil(rank)
    if lower == upper:
        return float(ordered[lower])
    weight = rank - lower
    return ordered[lower] * (1.0 - weight) + ordered[upper] * weight


def metric_summary(values: Sequence[int]) -> dict[str, float | int]:
    if not values:
        raise ValueError("no samples")
    return {
        "count": len(values),
        "min": min(values),
        "median": statistics.median(values),
        "p95": _percentile(values, 0.95),
        "max": max(values),
        "mean": statistics.fmean(values),
    }


def summarize(samples: Sequence[LineResponseSample]) -> dict[str, dict[str, float | int]]:
    if not samples:
        raise ValueError("no [LINE-RESPONSE] samples found")
    return {
        "loop_us": metric_summary([s.loop_us for s in samples]),
        "sensor_us": metric_summary([s.sensor_us for s in samples]),
        "control_us": metric_summary([s.control_us for s in samples]),
        "output_us": metric_summary([s.output_us for s in samples]),
        "total_us": metric_summary([s.total_us for s in samples]),
    }


def write_csv(path: Path, samples: Sequence[LineResponseSample]) -> None:
    if not samples:
        raise ValueError("no samples")
    rows = [asdict(sample) for sample in samples]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Parse H23-D/V2-TEST-005 [LINE-RESPONSE] serial logs."
    )
    parser.add_argument("log", type=Path)
    parser.add_argument("--label", default="unlabeled", help="e.g. v1-direct-gpio or v2-mcp23017")
    parser.add_argument("--csv", type=Path, default=None)
    args = parser.parse_args()

    samples = parse_lines(args.log.read_text(encoding="utf-8", errors="replace").splitlines())
    summary = {
        "label": args.label,
        "sample_count": len(samples),
        "metrics": summarize(samples),
        "acceptance_threshold": None,
        "pass_fail": "NOT_EVALUATED",
    }

    if args.csv is not None:
        write_csv(args.csv, samples)

    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
