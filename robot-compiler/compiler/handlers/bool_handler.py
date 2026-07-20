import ast
from ..error import CompilerError
from ..generated.opcode import Opcode

class BoolHandler:
    @staticmethod
    def bool_op(compiler, node):
        if isinstance(node.op, ast.And):
            return BoolHandler._compile_and(compiler, node)
        raise CompilerError(f"Unsupported boolean operator: {type(node.op).__name__}")

    @staticmethod
    def _compile_and(compiler, node):
        result = compiler.allocate_result()
        false_label = compiler.program.new_label()
        end_label = compiler.program.new_label()

        for expr in node.values:
            value = compiler.visit(expr)
            compiler.program.emit_jump_if_false(Opcode.JumpIfFalse.value, value, false_label)

        compiler.program.emit(Opcode.LoadConst.value, result, 1)
        compiler.program.emit_jump(Opcode.Jump.value, end_label)

        compiler.program.emit_label(false_label)
        compiler.program.emit(Opcode.LoadConst.value, result, 0)
        compiler.program.emit_label(end_label)
        return result