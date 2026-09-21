#!/usr/bin/env python3
"""H26-A characterization guards for the protected production path.

These tests are intentionally implementation-light: they verify that the
repository still contains the stage boundaries used by the current working
E2E flow without changing or replacing that flow.
"""

import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_golden_pipeline_tools_exist():
    required = [
        ROOT / "tools" / "rewrite.py",
        ROOT / "tools" / "compile.py",
        ROOT / "tools" / "build.py",
        ROOT / "tools" / "flash.py",
        ROOT / "tools" / "golden_build.py",
    ]
    missing = [str(path.relative_to(ROOT)) for path in required if not path.is_file()]
    assert not missing, f"Golden-path tooling missing: {missing}"


def test_production_firmware_program_boundary_exists():
    firmware_header = (
        ROOT
        / "robot-platform"
        / "main"
        / "src"
        / "Application"
        / "generated_program.h"
    )
    assert firmware_header.is_file(), (
        "Protected firmware program boundary is missing: "
        f"{firmware_header.relative_to(ROOT)}"
    )


def test_golden_corpus_exists():
    golden_dir = ROOT / "robot-platform" / "golden"
    programs = sorted(golden_dir.glob("*.py"))
    assert programs, "Golden program corpus must not be empty"


def _check_call_for_script(tree, script_name):
    """Return the subprocess.check_call node that invokes a named script variable."""
    matches = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        if not (
            isinstance(node.func, ast.Attribute)
            and node.func.attr == "check_call"
            and isinstance(node.func.value, ast.Name)
            and node.func.value.id == "subprocess"
        ):
            continue
        if not node.args or not isinstance(node.args[0], (ast.List, ast.Tuple)):
            continue

        command = node.args[0].elts
        invokes_script = any(
            isinstance(item, ast.Call)
            and isinstance(item.func, ast.Name)
            and item.func.id == "str"
            and len(item.args) == 1
            and isinstance(item.args[0], ast.Name)
            and item.args[0].id == script_name
            for item in command
        )
        if invokes_script:
            matches.append(node)

    assert len(matches) == 1, (
        f"Expected exactly one subprocess.check_call for {script_name}; "
        f"found {len(matches)}"
    )
    return matches[0]


def _command_elements(call_node):
    command = call_node.args[0]
    assert isinstance(command, (ast.List, ast.Tuple))
    return command.elts


def test_build_pipeline_preserves_rewrite_then_compile_order():
    build_source = (ROOT / "tools" / "build.py").read_text(encoding="utf-8")
    tree = ast.parse(build_source)

    rewrite_call = _check_call_for_script(tree, "rewrite_script")
    compile_call = _check_call_for_script(tree, "compile_script")

    assert rewrite_call.lineno < compile_call.lineno, (
        "Protected build order changed: rewrite must precede compile"
    )

    compile_command = _command_elements(compile_call)
    target_flag_indices = [
        index
        for index, item in enumerate(compile_command)
        if isinstance(item, ast.Constant) and item.value == "--target"
    ]
    assert len(target_flag_indices) == 1, (
        "Protected compile boundary must forward exactly one --target argument"
    )

    target_index = target_flag_indices[0]
    assert target_index + 1 < len(compile_command), "--target is missing its value"
    target_value = compile_command[target_index + 1]
    assert (
        isinstance(target_value, ast.Attribute)
        and target_value.attr == "target"
        and isinstance(target_value.value, ast.Name)
        and target_value.value.id == "args"
    ), "Protected compile boundary must forward args.target"


def test_flash_pipeline_consumes_program_header_and_uploads_existing_firmware():
    flash_source = (ROOT / "tools" / "flash.py").read_text(encoding="utf-8")
    assert 'header_src = build_dir / "program.h"' in flash_source
    assert 'generated_program.h' in flash_source
    assert 'platformio_command("run", "-t", "upload", "-d", str(platform_dir))' in flash_source
    assert "run_process(" in flash_source


def test_h26_a_documentation_exists():
    assert (ROOT / "docs" / "H26-A_GOLDEN_PATH_BASELINE.md").is_file()
