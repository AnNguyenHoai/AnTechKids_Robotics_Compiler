from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def test_runtime_paths_module_is_python_syntax_valid():
    source = (ROOT / "tools" / "runtime_paths.py").read_text(encoding="utf-8")
    compile(source, "tools/runtime_paths.py", "exec")


def test_tool_candidates_use_closed_f_strings():
    source = (ROOT / "tools" / "runtime_paths.py").read_text(encoding="utf-8")
    assert 'f"{name}{suffix}"' in source
