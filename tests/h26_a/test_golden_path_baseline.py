#!/usr/bin/env python3
"""H26-A characterization guards for the protected production path.

These tests are intentionally implementation-light: they verify that the
repository still contains the stage boundaries used by the current working
E2E flow without changing or replacing that flow.
"""

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


def test_build_pipeline_preserves_rewrite_then_compile_order():
    build_source = (ROOT / "tools" / "build.py").read_text(encoding="utf-8")
    rewrite_marker = 'rewrite_script = ROOT / "tools" / "rewrite.py"'
    compile_marker = 'compile_script = ROOT / "tools" / "compile.py"'
    rewrite_call = 'subprocess.check_call([sys.executable, str(rewrite_script)'
    compile_call = 'subprocess.check_call([sys.executable, str(compile_script)'

    assert rewrite_marker in build_source
    assert compile_marker in build_source
    assert rewrite_call in build_source
    assert compile_call in build_source
    assert build_source.index(rewrite_call) < build_source.index(compile_call), (
        "Protected build order changed: rewrite must precede compile"
    )


def test_flash_pipeline_consumes_program_header_and_uploads_existing_firmware():
    flash_source = (ROOT / "tools" / "flash.py").read_text(encoding="utf-8")
    assert 'header_src = build_dir / "program.h"' in flash_source
    assert 'generated_program.h' in flash_source
    assert 'platformio_command("run", "-t", "upload", "-d", str(platform_dir))' in flash_source
    assert "run_process(" in flash_source


def test_h26_a_documentation_exists():
    assert (ROOT / "docs" / "H26-A_GOLDEN_PATH_BASELINE.md").is_file()
