# Mapper

**Responsibility:** Convert RoboSim API calls to Platform API.

- e.g. `rcu.SetMoveRun()` → `move.run()`
- After this stage, no RoboSim names remain
- Output: Platform API Tree