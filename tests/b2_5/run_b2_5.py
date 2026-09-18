#!/usr/bin/env python3
"""B2.5 clean-machine physical E2E evidence regression gate.

Hosted CI has no physical robot.  This suite therefore tests the acceptance
runner's fail-closed semantics with deterministic fake process/qualification
boundaries.  It must never manufacture final physical PASS evidence.
"""
from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools import clean_machine_physical_e2e as b25


def check(name: str, condition: bool) -> None:
    if not condition:
        raise AssertionError(name)
    print(f"PASS: {name}")


def _write(path: Path, content: str = "fixture") -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return path


def _fixture(base: Path, name: str) -> tuple[Path, Path, Path, Path]:
    root = base / name / "release"
    _write(root / "RoboStudio.exe")
    _write(root / "runtime" / "bin" / "python.exe")
    _write(root / "compiler" / "robostudio_bridge.py")
    _write(root / "tools" / "deploy_robot.py")
    _write(root / "tools" / "clean_machine_physical_e2e.py")
    _write(root / "firmware" / "robot-platform" / "platformio.ini")
    _write(
        root / "distribution-manifest.json",
        json.dumps(
            {
                "schema": "antechkids.robostudio.distribution",
                "schema_version": 2,
                "production_boundary": True,
                "application": "RoboStudio.exe",
                "deployment_tools": "tools",
            }
        )
        + "\n",
    )
    external = base / name / "external"
    source = _write(external / "student.py", "import rcu\nrcu.SetMoveSpeed(50, 50)\n")
    evidence = external / "b2-5-evidence.json"
    state = external / "state"
    return root, source, evidence, state


def _qualification(port: str, env) -> dict[str, object]:
    return {
        "scope": "flash",
        "passed": True,
        "automated_checks_passed": True,
        "flash_preflight": {
            "status": "PASS",
            "selected_port": {"port": port},
            "driver_visibility_proven": True,
        },
    }


class RecordingRunner:
    def __init__(self, root: Path, *, deploy_returncode: int = 0, mutate_release: bool = False):
        self.root = root
        self.deploy_returncode = deploy_returncode
        self.mutate_release = mutate_release
        self.calls: list[dict[str, object]] = []

    def __call__(self, command, *, cwd, env, timeout):
        command = list(command)
        self.calls.append({"command": command, "cwd": Path(cwd), "env": dict(env), "timeout": timeout})
        if command[0].lower().endswith("robostudio.exe"):
            return SimpleNamespace(returncode=0, output="")
        if self.mutate_release:
            _write(self.root / "unexpected-runtime-write.txt", "mutation")
        output = "DEPLOYMENT PASS\n" if self.deploy_returncode == 0 else "upload failed\n"
        return SimpleNamespace(returncode=self.deploy_returncode, output=output)


def _run(
    root: Path,
    source: Path,
    evidence: Path,
    state: Path,
    runner: RecordingRunner,
) -> dict[str, object]:
    return b25.run_clean_machine_e2e(
        port="COM11",
        source=source,
        evidence=evidence,
        timeout=10,
        application_root=root,
        python_executable=root / "runtime" / "bin" / "python.exe",
        base_env={
            "PATH": str(root.parent / "HOST-POISON-PATH"),
            "PYTHONPATH": str(root.parent / "HOST-POISON-PYTHONPATH"),
            "ROBOSTUDIO_STATE_ROOT": str(state.resolve()),
        },
        qualification_runner=_qualification,
        process_runner=runner,
    )


def test_pending_then_confirmed_pass(base: Path) -> None:
    root, source, evidence, state = _fixture(base, "pass")
    runner = RecordingRunner(root)
    before, _ = b25.release_tree_digest(root)
    payload = _run(root, source, evidence, state, runner)
    after, _ = b25.release_tree_digest(root)

    check("automated B2.5 stage never self-claims physical PASS", payload["status"] == b25.STATUS_PENDING)
    check("release tree remains byte-stable", before == after)
    check("pending evidence is written outside release", evidence.is_file() and not str(evidence).startswith(str(root)))
    check("RoboStudio launch and deploy are both exercised", len(runner.calls) == 2)

    launch = runner.calls[0]
    deploy = runner.calls[1]
    launch_command = launch["command"]
    deploy_command = deploy["command"]
    check("real RoboStudio executable is probed", Path(launch_command[0]).name == "RoboStudio.exe")
    check("RoboStudio launch probe is bounded", "--acceptance-probe" in launch_command)
    check("deployment uses bundled Python", Path(deploy_command[0]).resolve() == (root / "runtime" / "bin" / "python.exe").resolve())
    check("deployment uses packaged deploy_robot", Path(deploy_command[1]).resolve() == (root / "tools" / "deploy_robot.py").resolve())
    check("deployment requires explicit selected COM port", "--port" in deploy_command and deploy_command[deploy_command.index("--port") + 1] == "COM11")
    check("deployment working directory is external", not str(Path(deploy["cwd"]).resolve()).startswith(str(root.resolve())))
    check("host PATH poison is removed", "HOST-POISON-PATH" not in str(deploy["env"].get("PATH", "")))
    check("host PYTHONPATH poison is removed", "PYTHONPATH" not in deploy["env"])
    check("artifact-closed mode reaches child", deploy["env"].get("ROBOSTUDIO_DEPENDENCY_MODE") == "artifact-closed")

    evidence_payload = json.loads(evidence.read_text(encoding="utf-8"))
    check("evidence schema is stable", evidence_payload["schema"] == b25.SCHEMA and evidence_payload["schema_version"] == 1)
    check("evidence records no host PATH inheritance", evidence_payload["clean_machine_contract"]["host_path_inherited"] is False)
    check("evidence records immutable release", evidence_payload["release_integrity"]["unchanged"] is True)
    check("operator truth starts pending", evidence_payload["operator_confirmation"]["robot_execution"] == "pending")

    confirmed = b25.confirm_operator_evidence(
        evidence=evidence,
        clean_machine="pass",
        ui_flow="pass",
        robot_execution="pass",
        note="Independent Windows machine; RoboStudio UI flash completed and robot executed the expected motion.",
        application_root=root,
    )
    check("final PASS requires all real operator confirmations", confirmed["status"] == b25.STATUS_PASS)
    check("confirmed PASS evidence validates", b25.load_evidence(evidence)["status"] == b25.STATUS_PASS)


def test_operator_failure_is_final_failure(base: Path) -> None:
    root, source, evidence, state = _fixture(base, "operator-fail")
    payload = _run(root, source, evidence, state, RecordingRunner(root))
    check("operator-fail fixture reaches pending state", payload["status"] == b25.STATUS_PENDING)
    confirmed = b25.confirm_operator_evidence(
        evidence=evidence,
        clean_machine="pass",
        ui_flow="pass",
        robot_execution="fail",
        note="Flash completed but the robot did not execute the expected program.",
        application_root=root,
    )
    check("real robot failure can never be upgraded to PASS", confirmed["status"] == b25.STATUS_FAIL)


def test_automated_failure_cannot_be_overridden(base: Path) -> None:
    root, source, evidence, state = _fixture(base, "deploy-fail")
    payload = _run(root, source, evidence, state, RecordingRunner(root, deploy_returncode=7))
    check("failed physical upload fails automated stage", payload["status"] == b25.STATUS_FAIL)
    try:
        b25.confirm_operator_evidence(
            evidence=evidence,
            clean_machine="pass",
            ui_flow="pass",
            robot_execution="pass",
            note="must not override",
            application_root=root,
        )
    except b25.CleanMachineE2EError as exc:
        check("operator confirmation cannot override automated failure", "cannot override" in str(exc))
    else:
        raise AssertionError("failed automated stage was incorrectly overridable")


def test_release_mutation_fails(base: Path) -> None:
    root, source, evidence, state = _fixture(base, "mutation")
    payload = _run(root, source, evidence, state, RecordingRunner(root, mutate_release=True))
    check("runtime mutation fails B2.5", payload["status"] == b25.STATUS_FAIL)
    check("runtime mutation is recorded", payload["release_integrity"]["unchanged"] is False)


def test_context_rejects_host_or_in_release_inputs(base: Path) -> None:
    root, source, evidence, _ = _fixture(base, "context")
    try:
        b25.validate_clean_machine_context(
            application_root=root,
            python_executable=Path(sys.executable),
            source=source,
            evidence=evidence,
        )
    except b25.CleanMachineE2EError as exc:
        check("host Python is rejected", "host Python is not accepted" in str(exc))
    else:
        raise AssertionError("host Python unexpectedly accepted")

    in_release_source = _write(root / "student.py", "pass\n")
    try:
        b25.validate_clean_machine_context(
            application_root=root,
            python_executable=root / "runtime" / "bin" / "python.exe",
            source=in_release_source,
            evidence=evidence,
        )
    except b25.CleanMachineE2EError as exc:
        check("student source inside release is rejected", "outside" in str(exc))
    else:
        raise AssertionError("release-local student source unexpectedly accepted")

    try:
        b25.validate_clean_machine_context(
            application_root=root,
            python_executable=root / "runtime" / "bin" / "python.exe",
            source=source,
            evidence=root / "evidence.json",
        )
    except b25.CleanMachineE2EError as exc:
        check("evidence inside release is rejected", "outside" in str(exc))
    else:
        raise AssertionError("release-local evidence unexpectedly accepted")


def test_gui_probe_contract() -> None:
    main_text = (ROOT / "robostudio" / "main.py").read_text(encoding="utf-8")
    check("RoboStudio exposes B2.5 acceptance probe", 'ACCEPTANCE_PROBE_ARG = "--acceptance-probe"' in main_text)
    check("acceptance probe constructs real RoboStudio window", "window = RoboStudioApp()" in main_text)
    check("acceptance probe constructs real Robot tab", "robot_tab = RobotTab" in main_text)
    check("acceptance probe processes Qt events", "app.processEvents()" in main_text)
    check("normal RoboStudio launch still enters event loop", "return app.exec()" in main_text)


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="robostudio-b25-") as temp:
        base = Path(temp)
        test_pending_then_confirmed_pass(base)
        test_operator_failure_is_final_failure(base)
        test_automated_failure_cannot_be_overridden(base)
        test_release_mutation_fails(base)
        test_context_rejects_host_or_in_release_inputs(base)
    test_gui_probe_contract()
    print("B2.5 real clean-machine E2E harness checks: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
