# RSD-13 Windows Path Canonicalization Fix

## Problem

On Windows, an application root or external working directory may be represented by an 8.3 short path while the child process reports the equivalent long path. Comparing `abspath()`/`normcase()` results alone can therefore produce a false mismatch.

## Fix

The RSD-13 clean-machine gate now canonicalizes existing filesystem paths with `realpath()` before equality and containment checks. This normalizes equivalent Windows path spellings, including short/long path forms, without changing runtime discovery behavior.

## Invariants

- The observed portable interpreter must equal the expected application-owned interpreter after canonicalization.
- The observed interpreter must remain under the application root.
- The external working directory must remain unchanged.
- Application-owned PlatformIO paths must remain under the application root.
