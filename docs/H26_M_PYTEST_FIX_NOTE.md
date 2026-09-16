# H26-M Pytest Environment Boundary

H26-M is a standalone deployment-contract regression gate. Its assertions are plain Python assertions and do not require pytest at runtime.

The runner must not invoke `python -m pytest` because a target/developer Python installation may contain an incompatible or shadowing pytest installation. H26-M validates the deployment contract, not the health of the local pytest environment.

The test cases therefore own their temporary directories with the Python standard library when executed by the standalone gate. They remain callable as normal pytest tests when pytest is available.
