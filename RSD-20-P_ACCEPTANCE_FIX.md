# RSD-20-P Acceptance Fixture Requirement

The RSD-20 CLI acceptance test must use a runnable application-owned Python interpreter in `runtime/bin`.

A byte placeholder such as `b"portable-python"` is sufficient for static dependency tests but cannot satisfy RSD-16 clean-machine acceptance, because the acceptance gate intentionally starts the packaged interpreter with an external CWD and hostile host runtime settings.

The regression fixture therefore copies the current base Python executable and, on Windows, its Python DLL, standard library, and DLL directory into the temporary application-owned runtime. This keeps the acceptance test self-contained while preserving the production gate's fail-closed behavior.
