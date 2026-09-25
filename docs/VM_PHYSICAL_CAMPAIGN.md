# VM-RT Physical Evidence Campaign

Tracking: #325. Parent closure: #313 / #302.

## Purpose

Turn the six required real-robot qualification scenarios into one reviewable evidence campaign. The campaign tooling validates coverage and consistency, aggregates measured maxima and prepares a threshold proposal. It never approves thresholds automatically.

## Required scenario names

Use these exact `scenario` values in each run metadata file:

- `line_follow_recovery`
- `intersection_behavior`
- `ultrasonic_decision_loop`
- `timed_wait_movement`
- `long_running_loop`
- `stop_abort_pending`

Each run is first converted to `qualification-report.json` with `tools/vm_rt_qualification.py` as described in `VM_PHYSICAL_QUALIFICATION.md`.

## Evidence layout

Recommended structure:

```text
artifacts/vm-rt/physical-campaign/
  line_follow_recovery/qualification-report.json
  intersection_behavior/qualification-report.json
  ultrasonic_decision_loop/qualification-report.json
  timed_wait_movement/qualification-report.json
  long_running_loop/qualification-report.json
  stop_abort_pending/qualification-report.json
  external-evidence.json
```

All six reports must be real physical evidence and should use one exact firmware commit and one slice budget.

## External sensor-to-decision-to-motor evidence

Scheduler telemetry alone is not end-to-end actuator latency. Record the externally measured result separately, for example:

```json
{
  "reviewed": true,
  "sensor_to_decision_to_motor_us_max": 1234,
  "method": "logic_analyzer",
  "evidence": ["artifacts/vm-rt/physical-campaign/external/latency.csv"]
}
```

`reviewed=true` means a human has checked that the source is genuine physical observation. Do not use host timing or estimates.

## Aggregate the campaign

```text
python tools/vm_rt_physical_campaign.py \
  --reports-root artifacts/vm-rt/physical-campaign \
  --external-evidence artifacts/vm-rt/physical-campaign/external-evidence.json \
  --output artifacts/vm-rt/physical-campaign/campaign-report.json
```

The campaign reports one of two states:

- `INCOMPLETE_PHYSICAL_EVIDENCE`: missing scenario, inconsistent firmware/slice budget, no stop latency observation, or missing external latency review.
- `READY_FOR_HUMAN_APPROVAL`: automated evidence checks are complete. This still does not approve production thresholds.

## Threshold proposal

The campaign report proposes measured maxima for:

- slice duration;
- indivisible work-unit duration;
- externally measured sensor→decision→motor latency;
- stop/abort latency;
- line snapshot age.

These are measured maxima, not automatically chosen safety limits. A human reviewer must decide the final production thresholds, document margin/rationale, update `docs/VM_RESPONSIVENESS_THRESHOLDS.json`, and set approval metadata explicitly.

## Closure sequence

1. Run all six scenarios on the target robot.
2. Generate six qualification reports.
3. Review external end-to-end latency evidence.
4. Generate `campaign-report.json`.
5. Resolve every blocker until status is `READY_FOR_HUMAN_APPROVAL`.
6. Review outliers and threshold margins.
7. Update and approve `VM_RESPONSIVENESS_THRESHOLDS.json` with evidence references.
8. Run `python tests/vm_responsiveness/run_vm_rt_ci.py`.
9. Run full regression and production packaging gates.
10. Only then close #325, #313 and parent #302 when their remaining DoD items are satisfied.
