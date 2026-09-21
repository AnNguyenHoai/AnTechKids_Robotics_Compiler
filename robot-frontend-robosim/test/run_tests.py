from pathlib import Path
import sys
import tempfile
import ast

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from frontend import rewrite
from frontend.transformer import RoboSimTransformer


def test_rewrite(input_file, golden_file):
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as tmp:
        output_path = Path(tmp.name)
    try:
        rewrite(input_file, output_path)
        with open(output_path, 'r') as f:
            actual = f.read()
        with open(golden_file, 'r') as f:
            expected = f.read()
        assert actual == expected, (
            f"Mismatch for {input_file.name}\n"
            f"Expected:\n{expected}\n"
            f"Actual:\n{actual}"
        )
        print(f"PASS: {input_file.name}")
    finally:
        output_path.unlink(missing_ok=True)


def rewrite_source(source):
    with tempfile.TemporaryDirectory() as tmpdir:
        source_path = Path(tmpdir) / "source.py"
        output_path = Path(tmpdir) / "output.py"
        source_path.write_text(source, encoding="utf-8")
        rewrite(source_path, output_path)
        return output_path.read_text(encoding="utf-8")


def test_invalid_sensor_args():
    """Test that wrong argument counts raise SyntaxError."""
    invalid_cases = [
        ("rcu.GetUltrasound()", "GetUltrasound", 1, 0),
        ("rcu.GetUltrasound(1, 2)", "GetUltrasound", 1, 2),
        ("rcu.GetTouch()", "GetTouch", 1, 0),
        ("rcu.GetTouch(1, 2)", "GetTouch", 1, 2),
        ("rcu.GetLightSensor()", "GetLightSensor", 1, 0),
        ("rcu.GetLightSensor(1, 2)", "GetLightSensor", 1, 2),
        ("rcu.GetTraceV2I2CChxState(1)", "GetTraceV2I2CChxState", 2, 1),
        ("rcu.GetTraceV2I2CChxState(1, 2, 3)", "GetTraceV2I2CChxState", 2, 3),
    ]
    for source, api_name, expected, actual in invalid_cases:
        try:
            tree = ast.parse(source)
            transformer = RoboSimTransformer()
            transformer.visit(tree)
            assert False, f"Expected SyntaxError for {api_name} with {actual} args"
        except SyntaxError as e:
            assert f"'{api_name}()' expects exactly {expected} argument(s)" in str(e)
            print(f"PASS: invalid {api_name} with {actual} args")


def test_trace_channel_normalization():
    """RoboSim owns only 1-based -> 0-based representation normalization."""
    api_targets = {
        "GetTraceV2I2CState": "get_trace_state",
        "GetTraceV2I2C": "get_trace_value",
        "GetTraceV2I2CChxState": "read_line",
    }
    for api_name, target_name in api_targets.items():
        for channel in range(1, 8):
            output = rewrite_source(
                f"import rcu\nvalue = rcu.{api_name}(1, {channel})\n"
            )
            canonical_channel = channel - 1
            assert f"{target_name}(1, {canonical_channel})" in output or (
                target_name == "read_line" and f"read_line({canonical_channel})" in output
            ), (
                f"Expected RoboSim {api_name} channel {channel} to normalize "
                f"to canonical channel {canonical_channel}; output={output!r}"
            )
    output = rewrite_source("import rcu\nvalue = rcu.GetTraceV2I2CState(1, +1)\n")
    assert "get_trace_state(1, 0)" in output
    print("PASS: RoboSim trace channels 1..7 and unary +1 normalize to canonical channels")


def test_invalid_trace_channels_rejected():
    """Frontend rejects only channels outside RoboSim's own 1..7 representation."""
    for api_name in ("GetTraceV2I2CState", "GetTraceV2I2C", "GetTraceV2I2CChxState"):
        for channel in (0, 8, -1):
            source = f"import rcu\nvalue = rcu.{api_name}(1, {channel})\n"
            try:
                rewrite_source(source)
                assert False, f"Expected SyntaxError for invalid RoboSim trace channel {channel}"
            except SyntaxError as e:
                assert "RoboSim trace channels are 1..7" in str(e)
                print(f"PASS: invalid {api_name} channel {channel} rejected")


def test_dynamic_trace_channel_normalized():
    """Dynamic channel stays dynamic; compiler target contract owns resource safety."""
    source = """import rcu
channel = 2
state = rcu.GetTraceV2I2CState(1, channel)
"""
    output = rewrite_source(source)
    assert "get_trace_state(1, channel - 1)" in output
    print("PASS: dynamic RoboSim trace channel is representation-normalized for compiler validation")


def test_set_motor_speed():
    source = """import rcu
rcu.SetMoveSpeed(50, 80)
rcu.SetMoveSpeed(-30, 40)
"""
    tree = ast.parse(source)
    transformer = RoboSimTransformer()
    tree = transformer.visit(tree)
    output = ast.unparse(tree)
    assert "set_motor_speed(50, 80)" in output
    assert "set_motor_speed(-30, 40)" in output
    print("PASS: SetMoveSpeed mapping")


def test_set_wait_for_time_conversion():
    source = """import rcu
rcu.SetWaitForTime(2)
rcu.SetWaitForTime(0.5)
rcu.SetWaitForTime(120)
"""
    tree = ast.parse(source)
    transformer = RoboSimTransformer()
    tree = transformer.visit(tree)
    output = ast.unparse(tree)
    assert "wait(2000)" in output
    assert "wait(500)" in output
    assert "wait(120000)" in output
    print("PASS: SetWaitForTime conversion (seconds to ms)")


def test_new_apis():
    source = """import rcu
rcu.SetServo(1, 90)
rcu.Set3CLed(2, 1)
rcu.SetLightSensorLed(3, 0)
rcu.SetMotorStraightAngle(1, 2, 70, 360)
rcu.line_intersection_stop(70, 17)
"""
    tree = ast.parse(source)
    transformer = RoboSimTransformer()
    tree = transformer.visit(tree)
    output = ast.unparse(tree)
    assert "set_servo(1, 90)" in output
    assert "set_3c_led(2, 1)" in output
    assert "set_light_sensor_led(3, 0)" in output
    assert "set_motor_straight_angle(1, 2, 70, 360)" in output
    assert "line_intersection_stop(70, 17)" in output
    print("PASS: New APIs rewrite correctly")


def main():
    examples = ROOT / "examples"
    golden_dir = ROOT / "test" / "golden"
    if not golden_dir.exists():
        print("Golden directory not found.")
        sys.exit(1)
    all_passed = True
    for py_file in examples.glob("*.py"):
        golden_file = golden_dir / f"{py_file.stem}.rewrite.py"
        if golden_file.exists():
            try:
                test_rewrite(py_file, golden_file)
            except AssertionError as e:
                print(e)
                all_passed = False
        else:
            print(f"SKIP: {py_file.name} (no golden)")
    test_invalid_sensor_args()
    test_trace_channel_normalization()
    test_invalid_trace_channels_rejected()
    test_dynamic_trace_channel_normalized()
    test_set_motor_speed()
    test_set_wait_for_time_conversion()
    test_new_apis()
    sys.exit(0 if all_passed else 1)


if __name__ == "__main__":
    main()
