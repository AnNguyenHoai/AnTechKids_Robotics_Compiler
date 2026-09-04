# H26-B tests

Run from repository root:

```bash
python tests/h26_b/run_h26_b.py
```

The suite intentionally uses only the Python standard library. It validates
both the read-only contract checker and the current protected Golden Path
baseline.

A failure means either the production boundary drifted or the baseline/test
contract itself is inconsistent. Do not repair the production path as part of
H26-B; route intentional architecture changes through the corresponding
migration task.
