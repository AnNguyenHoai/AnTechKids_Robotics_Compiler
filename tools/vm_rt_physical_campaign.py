#!/usr/bin/env python3
"""Aggregate VM-RT physical qualification reports into a campaign readiness report.

This tool never approves production thresholds. It validates that all required
physical scenarios are represented and emits measured maxima as a proposal for
human review.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

REQUIRED_SCENARIOS = (
    "line_follow_recovery",
    "intersection_behavior",
    "ultrasonic_decision_loop",
    "timed_wait_movement",
    "long_running_loop",
    "stop_abort_pending",
)


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def load_reports(directory: Path) -> list[dict]:
    reports: list[dict] = []
    for path in sorted(directory.rglob("qualification-report.json")):
        report = json.loads(path.read_text(encoding="utf-8"))
        report["_source"] = path.as_posix()
        reports.append(report)
    require(bool(reports), "no qualification-report.json files found")
    return reports


def max_metric(reports: list[dict], key: str) -> int | None:
    values = [int(r[key]["max"]) for r in reports if int(r.get(key, {}).get("count", 0)) > 0]
    return max(values) if values else None


def build_campaign(reports: list[dict], external_evidence: dict | None = None) -> dict:
    external_evidence = external_evidence or {}
    physical = [r for r in reports if r.get("physical_robot") is True and r.get("qualification_status") == "PHYSICAL_EVIDENCE_CAPTURED"]
    scenarios: dict[str, list[dict]] = {}
    for report in physical:
        scenarios.setdefault(str(report.get("scenario")), []).append(report)

    coverage = {name: len(scenarios.get(name, [])) for name in REQUIRED_SCENARIOS}
    missing = [name for name, count in coverage.items() if count == 0]

    firmware_commits = sorted({str(r.get("firmware_commit")) for r in physical if r.get("firmware_commit")})

    slice_budgets = sorted({
        int(r.get("slice_configuration", {}).get("max_work_units"))
        for r in physical
        if r.get("slice_configuration", {}).get("max_work_units") is not None
    })
    slice_duration_budgets = sorted({
        int(r.get("slice_configuration", {}).get("max_duration_us"))
        for r in physical
        if r.get("slice_configuration", {}).get("max_duration_us") is not None
    })
    slice_configurations = sorted({
        (
            int(r.get("slice_configuration", {}).get("max_work_units")),
            int(r.get("slice_configuration", {}).get("max_duration_us")),
        )
        for r in physical
        if r.get("slice_configuration", {}).get("max_work_units") is not None
        and r.get("slice_configuration", {}).get("max_duration_us") is not None
    })
    missing_dual_config = [
        r.get("_source", "<unknown>")
        for r in physical
        if r.get("slice_configuration", {}).get("max_work_units") is None
        or r.get("slice_configuration", {}).get("max_duration_us") is None
    ]

    stop_reports = scenarios.get("stop_abort_pending", [])
    stop_observations = sum(int(r.get("stop_latency_us", {}).get("count", 0)) for r in stop_reports)
    slowest = sorted(
        [dict(item, source=r["_source"]) for r in physical for item in r.get("slowest_work_units", [])],
        key=lambda item: int(item["duration_us"]),
        reverse=True,
    )[:10]

    external_reviewed = external_evidence.get("reviewed") is True
    external_max = external_evidence.get("sensor_to_decision_to_motor_us_max") if external_reviewed else None
    proposal = {
        "slice_duration_us_max": max_metric(physical, "slice_duration_us"),
        "work_unit_duration_us_max": max_metric(physical, "work_unit_duration_us"),
        "sensor_to_decision_to_motor_us_max": int(external_max) if external_max is not None else None,
        "stop_abort_latency_us_max": max_metric(stop_reports, "stop_latency_us"),
        "line_snapshot_age_us_max": max_metric(physical, "line_snapshot_age_us"),
    }

    blockers: list[str] = []
    if missing:
        blockers.append("missing required scenarios: " + ", ".join(missing))
    if stop_observations == 0:
        blockers.append("stop_abort_pending has no positive stop latency observation")
    if len(firmware_commits) != 1:
        blockers.append("campaign must use exactly one firmware commit")
    if missing_dual_config:
        blockers.append("every physical report must record max_work_units and max_duration_us")
    if len(slice_configurations) != 1:
        blockers.append("campaign must use exactly one dual slice configuration")
    if not external_reviewed or proposal["sensor_to_decision_to_motor_us_max"] is None:
        blockers.append("external sensor-to-decision-to-motor evidence must be reviewed and measured")

    return {
        "schema_version": 1,
        "issue": 325,
        "reports_total": len(reports),
        "physical_reports": len(physical),
        "scenario_coverage": coverage,
        "firmware_commits": firmware_commits,
        # Legacy field retained for readers that only display the work budget.
        "slice_budgets": slice_budgets,
        "slice_duration_budgets_us": slice_duration_budgets,
        "slice_configurations": [
            {"max_work_units": work, "max_duration_us": duration}
            for work, duration in slice_configurations
        ],
        "stop_latency_observations": stop_observations,
        "external_evidence": external_evidence,
        "slowest_work_units": slowest,
        "measured_threshold_proposal": proposal,
        "blockers": blockers,
        "campaign_status": "READY_FOR_HUMAN_APPROVAL" if not blockers else "INCOMPLETE_PHYSICAL_EVIDENCE",
        "approval": {"approved": False, "note": "This tool never approves production thresholds."},
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--reports-root", type=Path, required=True)
    parser.add_argument("--external-evidence", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    external = json.loads(args.external_evidence.read_text(encoding="utf-8")) if args.external_evidence else None
    campaign = build_campaign(load_reports(args.reports_root), external)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(campaign, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"VM-RT physical campaign: {campaign['campaign_status']}")
    for blocker in campaign["blockers"]:
        print(f"BLOCKER: {blocker}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
