import ast
from ..error import CompilerError

class CompareHandler:

    COMPARE_OPCODE = {

        ast.Eq: "CompareEQ",

        ast.NotEq: "CompareNE",

        ast.Lt: "CompareLT",

        ast.LtE: "CompareLE",

        ast.Gt: "CompareGT",

        ast.GtE: "CompareGE",

    }

    @staticmethod

      
    def compare(
        compiler,
        node
    ):
        left = compiler.resolve_argument(node.left)

        right = compiler.resolve_argument(node.comparators[0])

        result = compiler.allocate_result()

        operator = type(node.ops[0])

        opcode_name = CompareHandler.COMPARE_OPCODE.get(operator)

        if opcode_name is None:
            raise CompilerError(
                f"Unsupported comparison operator: {operator.__name__}"
            )

        opcode = compiler.opcodes.get(opcode_name)

        compiler.program.emit(
            opcode,
            left,
            right,
            result
        )
        return result