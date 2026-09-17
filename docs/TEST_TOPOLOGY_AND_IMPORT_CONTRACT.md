# Test Topology and Import Contract

## Purpose

The repository contains several Python subsystems with different source roots and test runners. CI must not treat the repository as one Python package and must not use a global `pytest` collection pass as the production regression gate.

## Canonical test boundaries

| Boundary | Source root | Test entry point | Ownership |
|---|---|---|---|
| Robot language | `robot-language/` | `robot-language/tests/` and its runner where applicable | language model, API, SDK generation |
| Compiler | `robot-compiler/` | `robot-compiler/tests/run_tests.py` | compiler/IR/backend/golden tests |
| RoboSim frontend | `robot-frontend-robosim/` | `robot-frontend-robosim/test/run_tests.py` | frontend rewrite/normalization |
| RoboStudio | `robostudio/` | RoboStudio/H26/RSD runners | application/services/UI contracts |
| Cross-cutting acceptance | repository root | `run_all_tests.py` | release/runtime/production contracts |

## Import rule

A subsystem's source root is part of its test environment. Tests must not rely on the developer machine's current virtualenv, PATH, IDE configuration, or an unrelated sibling source root being accidentally importable.

In particular, `language`, `robot`, and `compiler` are source-root-sensitive namespaces. The CI environment must not globally prepend every subsystem root to `PYTHONPATH`, because doing so can make the wrong package win import resolution.

## Dependency rule

CI dependencies are declared in `tests/requirements-ci.txt`. The file contains only dependencies required to execute the automated test suite. Production runtime dependencies remain governed by the production runtime/release contracts and are not inferred from CI dependencies.

Current CI dependencies include pytest, PyYAML, and PySide6 because repository tests/imports require them.

## Runner rule

`run_all_tests.py` is the canonical repository regression orchestrator. It explicitly enumerates the subsystem and contract runners and stops on the first failing runner. CI invokes it once instead of first running a repository-wide `pytest` collection that mixes incompatible import roots.

This does not mean pytest is forbidden. Pytest may still be used inside a subsystem with its correct source-root context. It is simply not the repository-wide acceptance boundary.

## Acceptance rule

A green CI result requires:

1. declared CI dependencies install successfully;
2. required test boundaries and the canonical runner exist;
3. `run_all_tests.py` completes successfully;
4. RSD/H26 production acceptance runners included by `run_all_tests.py` are executed rather than skipped because of an unrelated collection failure.

## Known source defect surfaced by the audit

`robot-language/robot/motion.py` contains generated annotations using `string` rather than a defined Python type. This is a source-generation defect, not an import-topology problem, and should be fixed separately after the test environment is normalized.

## Design principle

Fix test infrastructure at the boundary level. Do not modify individual assertions merely to accommodate a broken collection environment. A production contract change should update a shared fixture/contract once, and all dependent tests should consume that contract.
