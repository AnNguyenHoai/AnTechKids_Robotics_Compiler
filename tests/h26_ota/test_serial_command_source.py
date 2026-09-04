from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "robot-platform" / "main" / "src" / "Communication" / "SerialCommandHandler.cpp"


def test_imu_command_branches_do_not_contain_literal_backslash_n():
    text = SOURCE.read_text(encoding="utf-8")
    for command in ("imu status", "imu read", "imu calibrate", "imu timing"):
        marker = f'else if (input.startsWith("{command}"))'
        start = text.index(marker)
        line_end = text.index("\n", start)
        branch_line = text[start:line_end]
        assert "\\n" not in branch_line
        assert branch_line.rstrip().endswith("{")
