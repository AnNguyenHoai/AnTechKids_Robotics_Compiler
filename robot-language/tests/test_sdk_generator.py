import unittest
import sys
from pathlib import Path

# Thêm đường dẫn để import generator
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from language import RobotLanguage
from generators.sdk_generator import SDKGenerator
from build.context import BuildContext


class TestSDKGenerator(unittest.TestCase):
    def setUp(self):
        self.context = BuildContext()
        self.generator = SDKGenerator()
        self.robot_dir = self.context.root / "robot"
        # Xóa thư mục cũ để test sạch
        if self.robot_dir.exists():
            import shutil
            shutil.rmtree(self.robot_dir)

    def test_generator_creates_files(self):
        """Kiểm tra generator sinh đúng các file."""
        self.generator.generate(self.context)

        self.assertTrue((self.robot_dir / "__init__.py").exists())
        self.assertTrue((self.robot_dir / "motion.py").exists())
        self.assertTrue((self.robot_dir / "system.py").exists())
        self.assertFalse((self.robot_dir / "internal.py").exists())  # bỏ qua internal

    def test_generated_init_exports_all(self):
        """Kiểm tra __init__.py có export đúng."""
        self.generator.generate(self.context)
        init_content = (self.robot_dir / "__init__.py").read_text(encoding="utf-8")

        self.assertIn("from .motion import *", init_content)
        self.assertIn("from .system import *", init_content)

        self.assertIn("__all__ = [", init_content)
        self.assertIn("'forward'", init_content)
        self.assertIn("'backward'", init_content)
        self.assertIn("'wait'", init_content)

        self.assertIn('__version__ = "1.0.0"', init_content)

    def test_generated_motion_has_type_hints(self):
        """Kiểm tra motion.py có type hints và docstring."""
        self.generator.generate(self.context)
        motion_content = (self.robot_dir / "motion.py").read_text(encoding="utf-8")

        # Kiểm tra type hints
        self.assertIn("def forward(speed: int) -> None:", motion_content)
        self.assertIn("def backward(speed: int) -> None:", motion_content)
        self.assertIn("def turn_left(speed: int) -> None:", motion_content)
        self.assertIn("def turn_right(speed: int) -> None:", motion_content)

        # Kiểm tra docstring (không cần chính xác tuyệt đối)
        self.assertIn('"""', motion_content)
        self.assertIn("Move robot forward", motion_content)
        self.assertIn("Args:", motion_content)
        self.assertIn("speed (int):", motion_content)

    def test_generated_system_has_type_hints(self):
        """Kiểm tra system.py có type hints."""
        self.generator.generate(self.context)
        system_content = (self.robot_dir / "system.py").read_text(encoding="utf-8")

        self.assertIn("def wait(milliseconds: int) -> None:", system_content)
        self.assertIn("def stop() -> None:", system_content)

        self.assertIn('"""', system_content)
        self.assertIn("Wait milliseconds", system_content)
        self.assertIn("milliseconds (int):", system_content)

    def test_generator_does_not_create_internal(self):
        """Kiểm tra không sinh internal.py."""
        self.generator.generate(self.context)
        self.assertFalse((self.robot_dir / "internal.py").exists())

    def test_import_from_generated_sdk(self):
        """Kiểm tra có thể import từ SDK đã sinh."""
        self.generator.generate(self.context)
        sys.path.insert(0, str(self.robot_dir.parent))
        try:
            from robot import forward, wait, stop
            self.assertTrue(callable(forward))
            self.assertTrue(callable(wait))
            self.assertTrue(callable(stop))
        finally:
            sys.path.pop(0)


if __name__ == "__main__":
    unittest.main()