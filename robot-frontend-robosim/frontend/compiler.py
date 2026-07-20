from pathlib import Path
import sys
import ast

ROOT = Path(__file__).resolve().parent.parent

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

ROBOT_COMPILER = ROOT.parent / "robot-compiler"

if str(ROBOT_COMPILER) not in sys.path:
    sys.path.insert(0, str(ROBOT_COMPILER))

from compiler.compiler import RobotCompiler
from frontend.transformer import RoboSimTransformer


class RoboSimCompiler:

    def __init__(self):

        self.transformer = RoboSimTransformer()
        self.compiler = RobotCompiler()

    def compile(self, filename):

        #
        # Parse source
        #
        with open(filename, "r", encoding="utf8") as f:

            tree = ast.parse(f.read())

        #
        # Transform RoboSim AST
        #
        tree = self.transformer.visit(tree)

        ast.fix_missing_locations(tree)

        #
        # Compile Robot Language AST
        #
        return self.compiler.compile_ast(tree)