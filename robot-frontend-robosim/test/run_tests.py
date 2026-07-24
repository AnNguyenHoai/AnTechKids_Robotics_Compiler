from pathlib import Path
import sys
import tempfile

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from frontend import rewrite

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
    sys.exit(0 if all_passed else 1)

if __name__ == "__main__":
    main()