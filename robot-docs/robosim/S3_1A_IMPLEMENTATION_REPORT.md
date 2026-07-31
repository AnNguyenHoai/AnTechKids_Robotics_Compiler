Create a report with the following sections:

Changed Files – list of all modified files.

Architecture Mapping – diagram showing the pipeline from RoboSim to physical motors.

New Opcode/Function IDs – SetMotorSpeed ID = 35.

Test Results – summary of frontend, compiler, and existing regression tests (all pass).

Physical Test Instructions – as described above.

Known Limitations – threading not implemented; SetMoveSpeed does not have a blocking behavior (it sets speed and returns immediately, which is intended).

No-regression Statement – all existing tests pass; no regressions introduced.