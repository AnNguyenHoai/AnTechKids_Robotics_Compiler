# H30 Scope Boundary

H30 owns persistent multi-robot management inside RoboStudio:

- known robot registry;
- discovery merge;
- Online/Offline presentation;
- stable selected robot identity;
- safe per-robot OTA target selection;
- multi-robot first-flash ambiguity handling.

H30 intentionally does **not** add:

- deploy-to-many/group deployment;
- classroom groups or named fleets;
- synchronized robot execution;
- remote cloud fleet management;
- multi-robot program orchestration.

Those capabilities require a separate contract because they introduce partial-failure, fan-out, progress aggregation, retry, and authorization semantics beyond persistent local robot management.
