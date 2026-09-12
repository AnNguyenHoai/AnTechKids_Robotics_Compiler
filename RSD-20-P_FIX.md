# RSD-20-P Regression Fix

The portable-release proof API returns a `PortableReleaseProofReport` with `passed=False` and populated findings when dependency closure fails. It does not raise `PortableReleaseProofError` for ordinary dependency findings; exceptions are reserved for malformed/unreadable artifacts and structural validation failures.

The regression test is therefore required to assert the failed report and its finding rather than expect an exception. The production CLI already converts `passed=False` into a non-zero exit code, so the fail-closed release gate remains unchanged.
