# B2.5 — Real Clean-Machine End-to-End Acceptance

## Goal

Prove the production release on an independent Windows machine through the real user boundary:

`copy ZIP -> extract -> launch RoboStudio -> select real COM -> compile -> physically flash -> robot runs -> collect evidence`

B2.5 does **not** allow GitHub-hosted CI, a developer checkout, host Python, host PlatformIO, or a hard-coded COM port to stand in for this proof.

## Acceptance boundary

The production artifact owns:

- `RoboStudio.exe`
- `runtime/bin/python.exe`
- compiler + RoboSim frontend
- PlatformIO Core package + ESP32 platform/packages/toolchain/uploader
- firmware project
- deployment/preflight/qualification tools
- `tools/clean_machine_physical_e2e.py`

The only permitted machine-level hardware prerequisite is the Windows USB/UART driver needed by the connected board when Windows does not already provide one.

A B2.5 result is final `PASS` only after both the automated stage and real operator observations succeed.

## Why acceptance is two-phase

Hosted CI cannot truthfully observe a physical robot. The B2.5 runner therefore uses a fail-closed evidence state machine:

1. `run` proves the automated software path and writes `PENDING_OPERATOR_CONFIRMATION` evidence.
2. The operator performs/observes the real GUI + robot flow on the independent machine.
3. `confirm` records the real observations. Only then may evidence become `PASS`.

An upload failure, release mutation, missing COM port, host-Python execution, or failed robot observation can never be overridden into `PASS`.

## Machine preparation

Use a Windows 10/11 x64 machine that is independent from the build machine.

Required setup:

- Copy only the production release ZIP and a student `.py` program to the machine.
- Do not clone the source repository.
- Do not install Python for RoboStudio.
- Do not install PlatformIO for RoboStudio.
- Do not install Node/compiler/toolchain for RoboStudio.
- Install only the board USB/UART driver if the selected robot is not visible as a COM port.
- Extract the ZIP to a normal local folder with write access to the user's profile/state directory.

The student source file and evidence file must remain outside the extracted release directory.

## Phase 1 — Automated physical run

From a terminal opened in the extracted release root, run:

```bat
runtime\bin\python.exe -B tools\clean_machine_physical_e2e.py run ^
  --port COM11 ^
  --source C:\B2_5_Input\student_program.py ^
  --evidence C:\B2_5_Evidence\b2_5_evidence.json
```

Replace `COM11` with the explicitly selected robot port.

The runner performs these checks in order:

1. Verifies it is running with `runtime/bin/python.exe` from this artifact.
2. Verifies source/evidence/state are outside the immutable release.
3. Seals PATH/PYTHONPATH/PlatformIO state using the B2.2/B2.3 dependency boundary.
4. Fingerprints every file in the release tree.
5. Starts the real packaged `RoboStudio.exe --acceptance-probe` and constructs the real RoboStudio window + Robot tab.
6. Qualifies the explicit COM port through packaged PlatformIO.
7. Runs packaged `tools/deploy_robot.py` with bundled Python, packaged compiler, packaged PlatformIO/toolchain/uploader, and explicit `--port`.
8. Re-fingerprints the release and requires byte-stable contents.
9. Writes machine-readable evidence outside the release.

A successful automated phase intentionally ends as:

```text
B2.5 clean-machine physical E2E: PENDING_OPERATOR_CONFIRMATION
```

This is not a failure. It means the software/flash path passed and physical truth still needs human observation.

## Phase 2 — Real UI and robot observation

On the same independent machine:

1. Launch `RoboStudio.cmd` normally.
2. Open or enter the same student program.
3. Open the Robot / First-Flash or deployment surface used by the target workflow.
4. Refresh USB devices.
5. Select the real detected COM port. Do not type or assume a default COM port.
6. Compile/deploy through the real RoboStudio UI.
7. Verify the upload completes successfully.
8. Verify the robot reboots/starts and physically performs the expected program behavior.

If any of those observations fail, record `fail`; do not retry by editing evidence manually.

## Phase 3 — Confirm evidence

When the independent-machine setup, real GUI flow, and robot behavior all pass:

```bat
runtime\bin\python.exe -B tools\clean_machine_physical_e2e.py confirm ^
  --evidence C:\B2_5_Evidence\b2_5_evidence.json ^
  --clean-machine pass ^
  --ui-flow pass ^
  --robot-result pass ^
  --note "Independent machine; RoboStudio UI flash completed; robot executed expected program."
```

If the robot or UI flow fails, use `fail` for that field. The final evidence will become `FAIL`.

## Validate evidence

```bat
runtime\bin\python.exe -B tools\clean_machine_physical_e2e.py validate ^
  --evidence C:\B2_5_Evidence\b2_5_evidence.json
```

A final B2.5 release-acceptance record is valid only when it reports:

```text
B2.5 clean-machine physical E2E: PASS
```

## Evidence contract

Schema:

`antechkids.robostudio.clean-machine-physical-e2e` / version `1`

Evidence records, without depending on developer-machine paths:

- application executable identity
- student source name + SHA-256
- explicit selected serial port
- bundled-Python ownership
- host PATH inheritance policy (`false`)
- source-checkout/global-Python/global-PlatformIO requirement (`false`)
- RoboStudio launch-probe result
- target/driver/serial qualification result
- packaged compile + USB deploy result
- release-tree SHA-256 before/after and immutable status
- operator clean-machine confirmation
- operator real GUI-flow confirmation
- operator robot-execution confirmation
- final status

## CI responsibility

`tests/b2_5/run_b2_5.py` runs in hosted Windows CI with fake process/hardware boundaries. It proves the harness is fail-closed, portable and evidence-consistent. It does **not** claim a physical robot was flashed.

CI must verify at least:

- automated stage cannot self-claim final PASS
- host Python is rejected
- poisoned host PATH/PYTHONPATH are removed
- explicit COM selection is preserved
- bundled Python + packaged `deploy_robot.py` are used
- release mutation fails acceptance
- upload failure cannot be manually overridden
- robot failure produces final FAIL
- final PASS requires clean-machine + real UI + robot confirmations
- B2.5 runtime is included in the production distribution and final ZIP

## B2.5 Done criteria

B2.5 is fully Done only when:

- B2.5 hosted regression gate passes,
- full repository regression passes,
- a real production ZIP is copied to an independent Windows machine,
- the operator completes the real RoboStudio UI flow,
- a physical robot is successfully flashed and executes the expected behavior,
- the resulting external evidence JSON validates with final status `PASS`.

Until the last three physical-machine items happen, the implementation may be automated-ready but the physical acceptance itself remains pending.
