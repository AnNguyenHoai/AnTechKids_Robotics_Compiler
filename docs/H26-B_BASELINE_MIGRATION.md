# H26-B Baseline Migration — H26-M Deployment Contract

H26-M intentionally changed `tools/flash.py` to require a validated deployment manifest before flashing. H26-B's protected-file baseline still referenced the pre-H26-M `tools/flash.py` blob, so the drift checker correctly reported an error after the pull.

This migration advances the H26-B baseline to the reviewed H26-M deployment-contract implementation (`a8225414322d57e5bb9445013d8610af29ea8fdc`) and records its current blob SHA. No production contract is weakened and no `--no-baseline` bypass is used.
