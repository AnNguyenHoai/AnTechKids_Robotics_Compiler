import unittest
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from language import LanguageLoader
from language.query import LanguageQuery


class TestLanguageQuery(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        spec_path = ROOT / "specification" / "api.yaml"
        language = LanguageLoader.load(spec_path)
        cls.query = LanguageQuery(language)

    def test_category_count(self):
        self.assertEqual(self.query.category_count(), 3)  # motion, system, internal

    def test_function_count(self):
        self.assertEqual(self.query.function_count(), 29)

    def test_opcode_count(self):
        self.assertEqual(len(self.query.opcodes()), 29)

    def test_public_functions_count(self):
        public = list(self.query.public_functions())
        self.assertEqual(len(public), 6)  # forward, backward, turn_left, turn_right, wait, stop

    def test_internal_functions_count(self):
        internal = list(self.query.internal_functions())
        self.assertEqual(len(internal), 23)  # remaining

    def test_function_by_name(self):
        func = self.query.function("forward")
        self.assertIsNotNone(func)
        self.assertEqual(func["name"], "forward")
        self.assertEqual(self.query.opcode_of(func), "Forward")
        self.assertEqual(self.query.opcode_id_of(func), 2)
        self.assertEqual(self.query.argument_count_of(func), 1)
        self.assertFalse(self.query.is_internal(func))

        func = self.query.function("LoadConst")
        self.assertIsNotNone(func)
        self.assertTrue(self.query.is_internal(func))

    def test_statistics(self):
        stats = self.query.statistics()
        self.assertEqual(stats["categories"], 3)
        self.assertEqual(stats["functions"], 29)
        self.assertEqual(stats["opcodes"], 29)
        self.assertEqual(stats["public_functions"], 6)
        self.assertEqual(stats["internal_functions"], 23)

    def test_module_of_func(self):
        func = self.query.function("forward")
        self.assertEqual(self.query.module_of_func(func), "motion_handler")
        self.assertEqual(self.query.handler_of_func(func), "MotionHandler")

        func = self.query.function("wait")
        self.assertEqual(self.query.module_of_func(func), "system_handler")
        self.assertEqual(self.query.handler_of_func(func), "SystemHandler")

        func = self.query.function("LoadConst")
        self.assertEqual(self.query.module_of_func(func), "internal")
        self.assertEqual(self.query.handler_of_func(func), "None")

    def test_description_of(self):
        func = self.query.function("forward")
        self.assertEqual(self.query.description_of(func), "Move robot forward")

    def test_arguments_of(self):
        func = self.query.function("forward")
        args = self.query.arguments_of(func)
        self.assertEqual(len(args), 1)
        self.assertEqual(args[0]["name"], "speed")
        self.assertEqual(args[0]["type"], "int")


if __name__ == "__main__":
    unittest.main()