# VM-RT J Physical Robot Qualification

Tracking: #312 / #325, parent #302
Historical evidence baseline: `main@18875d500bb64f4ff4a495f8915795af4f8a02f8` (merged #311 / PR #323)

## Purpose

This runbook defines the evidence required to qualify cooperative VM responsiveness on a real ESP32 robot. Host fixtures validate the tooling only; they are not physical qualification evidence and cannot approve production thresholds.

A September 25, 2026 physical retest exposed visible line-follow/control lag with the original four-work-unit scheduler. The corrective firmware under qualification therefore uses a dual scheduler configuration. This configuration is **provisional** until the campaign below is completed.

## Qualification firmware

Build the diagnostic-only profile:

```text
python -m platformio run -d robot-platform -e esp32dev_vm_qualification
```

The profile inherits the production `esp32dev` configuration and adds only:

```text
-DVM_RESPONSIVENESS_DIAGNOSTICS=1
```

The normal production profile remains unchanged.

### Observer-safe telemetry behavior

The qualification profile no longer prints a JSON record after every active VM slice. `RecordSlice()` stores the latest bounded evidence window in RAM, and the firmware dumps the buffered JSONL only after VM motion has stopped. This prevents 115200-baud UART traffic from becoming part of the control latency being measured.

For serial capture, **keep the capture running through the stop/end of the scenario** so the post-run JSONL dump is retained. A file that ends before the VM stops may contain no VM-RT JSON records even though the in-RAM measurements were captured correctly.

### CI-verified evidence commit

Physical evidence must be captured from a qualification firmware commit that passed the GitHub Actions step **Compile VM-RT qualification firmware** using the exact `esp32dev_vm_qualification` profile. The same compile is required for VM-impact CI, full regression, and release scope.

Before a physical campaign:

1. record the exact firmware commit SHA that will be qualified;
2. verify that commit has a successful qualification-profile compile in CI;
3. check out that exact commit when rebuilding/flashing locally;
4. record the same SHA in every scenario metadata file as `firmware_commit`;
5. record the exact dual slice configuration in every scenario metadata file;
6. do not substitute a later local edit or unverified build while keeping the old SHA in evidence metadata.

A successful production `esp32dev` build does not substitute for the qualification-profile build because physical telemetry requires `VM_RESPONSIVENESS_DIAGNOSTICS=1`.

## Required metadata per run

Create a JSON metadata file containing at least:

```json
{
  "schema_version": 1,
  "evidence_kind": "physical_robot",
  "physical_robot": true,
  "scenario": "line_follow_recovery",
  "hardware": "robot-id / board revision / sensor revision / motor driver",
  "profile": "esp32dev_vm_qualification",
  "firmware_commit": "<exact git sha>",
  "program_identity": "<source/bytecode identity>",
  "slice_configuration": {
    "max_work_units": 16,
    "max_duration_us": 2000
  },
  "failures_or_outliers": [],
  "thresholds": null
}
```

`tools/vm_rt_qualification.py` rejects `physical_robot=true` metadata that omits either scheduler field. `tools/vm_rt_physical_campaign.py` also refuses to combine reports that do not use exactly one firmware commit and exactly one `(max_work_units, max_duration_us)` configuration.

Do not set `physical_robot=true` for synthetic or desktop-generated telemetry.

## Required scenarios

Run each scenario with an exact program/bytecode identity and retain the raw serial capture.

1. **Line following and recovery** — continuous line follow plus forced deviation/recovery. Capture line snapshot age, read count, slice timing, slowest work unit and any visible steering lag. Include the exact `line_basis` test cadence used by the operator.
2. **Intersection behavior** — where the hardware/course supports it, exercise intersection stop/turn behavior and confirm the pending operation progresses across slices without starving platform services.
3. **Ultrasonic decision loop** — repeatedly sample distance, make a decision and update motor output. Record the sensor→decision→motor observation using the available telemetry plus an external timestamp/video/logic-analyzer reference when end-to-end timing is required.
4. **Timed wait/movement** — exercise `Wait` and timed movement while another platform service remains active. Verify pending state spans slices and the VM continues only after completion.
5. **Long-running/forever loop** — run long enough to establish a useful timing distribution. Stop the VM cleanly at the end so the RAM-buffered telemetry is emitted to the serial capture.
6. **Stop/abort while pending** — issue stop while a cooperative wait/line/timed operation is pending. Record `stop_latency_us`, pending owner/opcode before stop, motor/output state after stop, and the physical stopping distance separately from software latency.

## Capture

Start serial capture before the scenario, run the test, then stop/end the VM while capture remains active. Save the complete output to a text/JSONL file. Lines not containing VM telemetry are allowed; the parser ignores them. Each accepted telemetry record must have `type="vm_rt"` and the full VM-RT H field set.

Generate a normalized report:

```text
python tools/vm_rt_qualification.py \
  --telemetry artifacts/vm-rt/<run>/serial.jsonl \
  --metadata artifacts/vm-rt/<run>/metadata.json \
  --output artifacts/vm-rt/<run>/qualification-report.json
```

The report records:

- slice count and termination reason distribution;
- slice duration p50/p95/p99/max;
- indivisible work-unit p50/p95/p99/max;
- top slowest work units with owning PC;
- line-snapshot age distribution and physical-read evidence;
- observed stop/abort latency distribution;
- hardware/profile/firmware/program/dual-slice metadata;
- operator-recorded failures and outliers.

## Sensor → decision → motor evidence

Current VM telemetry directly measures scheduler and snapshot timing, not the complete electrical sensor-to-motor path. For scenarios where end-to-end sensor→decision→motor latency is required, correlate the JSONL evidence with a physical observation source such as logic analyzer, GPIO marker, or frame-accurate video. Do not label `sliceDurationUs` alone as end-to-end actuator latency.

For the reported `GetTraceV2I2CState -> SetMoveStop` overshoot, record software timing and physical stopping distance as separate measurements. PWM-command latency and mechanical/coast/brake distance must not be conflated.

## Threshold approval

`docs/VM_RESPONSIVENESS_THRESHOLDS.json` intentionally contains `null` thresholds and status `UNAPPROVED_PENDING_PHYSICAL_EVIDENCE`.

The manifest also records the provisional runtime configuration currently under test:

```text
max_work_units = 16
max_duration_us = 2000
```

These values are a corrective configuration after an observed physical failure; they are not approved thresholds. Only populate/approve thresholds after the required physical scenarios have enough samples to identify normal distributions and worst observed outliers. Any final scheduler tuning must reference the physical reports that justify it.

## Exit checklist for #312 / #325

- [ ] Exact evidence firmware commit has a successful CI qualification-profile compile.
- [ ] Every run records the same dual slice configuration.
- [ ] All required scenarios executed on physical robot.
- [ ] Raw post-stop JSONL and metadata retained for each run.
- [ ] Qualification report generated for each run.
- [ ] Sensor→decision→motor evidence captured where applicable.
- [ ] Stop/abort software latency measured while pending.
- [ ] Physical stopping distance recorded separately from software latency.
- [ ] Longest indivisible work-unit outliers reviewed by PC/opcode.
- [ ] Final budget tuning, if any, justified by measured evidence.
- [ ] `VM_RESPONSIVENESS_THRESHOLDS.json` populated from evidence and approved.
- [ ] Host VM-RT gates remain green.

Until these boxes have physical evidence, #312/#325 remain open even if the corrective implementation PR is merged.
