import unittest
import subprocess
import sys
import tempfile
from pathlib import Path

class TestIntegration(unittest.TestCase):
    def test_compile_and_generate_header(self):
        # Tạo file nguồn tạm
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write("forward(80)\nstop()\n")
            source = f.name

        # Tạo file header tạm
        with tempfile.NamedTemporaryFile(suffix='.h', delete=False) as out:
            output = out.name

        try:
            compiler_script = Path(__file__).parent.parent / "robot-compiler" / "main.py"
            result = subprocess.run(
                [sys.executable, str(compiler_script), "--file", source, "--output", output],
                capture_output=True,
                text=True
            )
            self.assertEqual(result.returncode, 0,
                             msg=f"Compilation failed:\n{result.stdout}\n{result.stderr}")

            # Kiểm tra header có nội dung đúng
            with open(output, 'r', encoding='utf-8') as f:
                content = f.read()
                self.assertIn("Instruction(Opcode::LoadConst", content)
                self.assertIn("Instruction(Opcode::Forward", content)
                self.assertIn("Instruction(Opcode::Stop", content)

        finally:
            Path(source).unlink(missing_ok=True)
            Path(output).unlink(missing_ok=True)