# B2.6 Implementation Status

- Base: B2.5 head `7a84885b7b4bee1a7e35c950fd5d5101ffad0f45`.
- Branch: `b2-6-release-copy-run-contract`.
- Canonical build path: `tools/one_command_production_build.py`.
- Copy/run contract: `copy-run-contract.json` inside the final production ZIP.
- Finalizer: `tools/copy_run_release.py`.
- Automated gate: `tests/b2_6/run_b2_6.py`.
- Physical robot truth remains owned by B2.5; B2.6 never fabricates physical PASS.

B2.6 implementation is considered automated-qualified only after the exact branch head passes the Windows B2.2–B2.6 gates and the full repository regression suite.
