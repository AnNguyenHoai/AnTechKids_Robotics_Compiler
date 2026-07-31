Include:

Root cause: mixed time units.

Fix: standardize seconds in RoboSim, convert to ms at frontend.

Changed files list.

Verification of 120 000 ms survival.

Test results (all pass).

Updated contract.

Summary of Changed Files
File	Change
robot-frontend-robosim/examples/robosim_demo.py	SetWaitForTime(1000) → SetWaitForTime(1)
robot-frontend-robosim/test/golden/robosim_wait.rewrite.py	wait(2) → wait(2000)
robot-frontend-robosim/test/run_tests.py	Updated test to expect conversion
robot-docs/robosim/ROBOSIM_RC1_API_CONTRACT.md	Added time‑unit section
robot-docs/robosim/S3_1A_1_TIME_UNIT_FIX_REPORT.md	New report
All other changes (int32_t types) were already applied in the previous step.