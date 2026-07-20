import ast
from ..error import CompilerError
from ..generated.opcode import Opcode

class CompareHandler:
    COMPARE_OPCODE = {
        ast.Eq: Opcode.CompareEQ,
        ast.NotEq: Opcode.CompareNE,
        ast.Lt: Opcode.CompareLT,
        ast.LtE: Opcode.CompareLE,
        ast.Gt: Opcode.CompareGT,
        ast.GtE: Opcode.CompareGE,
    }

    @staticmethod
    def compare(compiler, node):
        left = compiler.resolve_argument(node.left)
        right = compiler.resolve_argument(node.comparators[0])
        result = compiler.allocate_result()
        operator = type(node.ops[0])
        opcode = CompareHandler.COMPARE_OPCODE.get(operator)
        if opcode is None:
            raise CompilerError(f"Unsupported comparison operator: {operator.__name__}")
        compiler.program.emit(opcode.value, left, right, result)
        return result