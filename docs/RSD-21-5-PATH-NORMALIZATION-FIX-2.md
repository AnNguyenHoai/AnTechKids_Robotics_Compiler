# RSD-21.5 — Artifact Evidence Path Normalization Fix

Windows path separators are normalized to POSIX-style paths for machine-readable artifact evidence. This keeps evidence stable across Windows and POSIX hosts without changing actual process execution paths.
