# VM-RT Physical Evidence Campaign

Tracking: #325. Parent closure: #313 / #302. Reconciliation: #330 / #343.

## Purpose

Turn the six required real-robot qualification scenarios into one reviewable evidence campaign. The campaign tooling validates coverage and consistency, aggregates measured maxima and prepares a threshold proposal. It never approves thresholds automatically.

The same real capture may support multiple VM-RT child issues when the hardware/profile/firmware identity and measured signal are genuinely applicable. Do not duplicate runs merely to satisfy issue bookkeeping, and do not close a physical-evidence issue from synthetic/host data.

## Required scenario names

Use these exact `scenario` values in each run metadata file:

- `line_follow_recovery`
- `intersection_behavior`
- `ultrasonic_decision_loop`
- `timed_wait_movement`
- `long_running_loop`
- `stop_abort_pending`

Each run is first converted to `qualification-report.json` with `tools/vm_rt_qualification.py` as described in `VM_PHYSICAL_QUALIFICATION.md`.

## Reconciliation coverage map

The #330 audit assigned previously ownerless timing/compatibility risks to explicit issues. Cover them in the campaign as follows:

| Issue | Evidence focus | Primary campaign scenarios |
|---:|---|---|
| #336 | touch/light/color driver-read latency if those devices are active on the qualification hardware | scenario exercising each active sensor; may be an additional focused capture linked to the same campaign identity |
| #337 | `LineBasis` / line-control indivisible work-unit duration and outliers | `line_follow_recovery`, `intersection_behavior` |
| #339 | line getter/raw timing after shared-snapshot conversion | `line_follow_recovery`, `intersection_behavior` |
| #340 | ultrasonic no-echo/timeout work-unit latency versus approved threshold | `ultrasonic_decision_loop` |
| #341 | synchronous diagnostics/logging overhead with production vs qualification configuration stated explicitly | all scenarios; especially slowest-work-unit review |
| #342 | motor/actuator/output work-unit outliers | `line_follow_recovery`, `ultrasonic_decision_loop`, `stop_abort_pending` |
| #344 | ensure feature-gated/dummy paths are not used as proof of real hardware timing | campaign metadata/review for every relevant device |

#338 is a source/compatibility guard task and does not require a separate physical run. #343 owns this mapping and can close once the mapping is merged and evidence traceability is maintained by #325.

## Evidence identity

All physical reports used for one approval campaign must identify the exact hardware/profile and firmware used. The qualification firmware commit must be a SHA for which CI successfully compiled `esp32dev_vm_qualification`; record that same SHA in run metadata.

The evidence set must also state the diagnostics configuration. Timing collected with `VM_RESPONSIVENESS_DIAGNOSTICS=1` is qualification timing; production threshold review must explicitly account for whether the shipped production configuration has less, equal, or different synchronous logging overhead.

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

1. Verify the exact qualification firmware SHA passed the `esp32dev_vm_qualification` CI compile.
2. Run all six scenarios on the target robot.
3. Generate six qualification reports.
4. Review #336/#337/#339/#340/#341/#342/#344 evidence coverage and record evidence paths in those issues.
5. Review external end-to-end latency evidence.
6. Generate `campaign-report.json`.
7. Resolve every blocker until status is `READY_FOR_HUMAN_APPROVAL`.
8. Review outliers and threshold margins.
9. Update and approve `VM_RESPONSIVENESS_THRESHOLDS.json` with evidence references.
10. Run `python tests/vm_responsiveness/run_vm_rt_ci.py`.
11. Run H35, full regression, qualification compile, production packaging and first-flash gates.
12. Only then close the physical child issues, #325, #312, #313 and parent #302 when their remaining DoD items are satisfied.
