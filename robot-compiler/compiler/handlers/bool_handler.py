import ast
from ..error import CompilerError
from ..generated.opcode import Opcode


class BoolHandler:
    """Lower RoboSim boolean expressions to canonical control flow.

    RoboSim intentionally normalizes boolean-expression results to integer
    ``0`` or ``1``.  This preserves the existing compiler/runtime contract and
    differs from CPython's value-propagating ``and``/``or`` semantics.

    Truthiness follows the VM contract: zero is false, non-zero is true.
    ``and`` and ``or`` short-circuit left-to-right, and ``not`` evaluates its
    operand exactly once before normalizing the inverted result.
    """

    @staticmethod
    def bool_op(compiler, node):
        if isinstance(node.op, ast.And):
            return BoolHandler._compile_and(compiler, node)
        if isinstance(node.op, ast.Or):
            return BoolHandler._compile_or(compiler, node)
        raise CompilerError(f"Unsupported boolean operator: {type(node.op).__name__}")

    @staticmethod
    def logical_not(compiler, node):
        operand = compiler.compile_expression(node.operand)
        result = compiler.allocate_result()
        operand_false_label = compiler.program.new_label()
        end_label = compiler.program.new_label()

        compiler.program.emit_jump_if_false(
            Opcode.JumpIfFalse.value,
            operand,
            operand_false_label,
        )
        compiler.program.emit(Opcode.LoadConst.value, result, 0)
        compiler.program.emit_jump(Opcode.Jump.value, end_label)

        compiler.program.emit_label(operand_false_label)
        compiler.program.emit(Opcode.LoadConst.value, result, 1)

        compiler.program.emit_label(end_label)
        return result

    @staticmethod
    def _compile_and(compiler, node):
        result = compiler.allocate_result()
        false_label = compiler.program.new_label()
        end_label = compiler.program.new_label()

        for expr in node.values:
            # Use the canonical expression compiler instead of NodeVisitor so
            # nested arithmetic, calls, unary expressions and BoolOps are all
            # valid operands of another BoolOp.
            value = compiler.compile_expression(expr)
            compiler.program.emit_jump_if_false(
                Opcode.JumpIfFalse.value,
                value,
                false_label,
            )

        compiler.program.emit(Opcode.LoadConst.value, result, 1)
        compiler.program.emit_jump(Opcode.Jump.value, end_label)

        compiler.program.emit_label(false_label)
        compiler.program.emit(Opcode.LoadConst.value, result, 0)

        compiler.program.emit_label(end_label)
        return result

    @staticmethod
    def _compile_or(compiler, node):
        result = compiler.allocate_result()
        true_label = compiler.program.new_label()
        end_label = compiler.program.new_label()

        for expr in node.values:
            value = compiler.compile_expression(expr)
            compiler.program.emit_jump_if_true(
                Opcode.JumpIfTrue.value,
                value,
                true_label,
            )

        compiler.program.emit(Opcode.LoadConst.value, result, 0)
        compiler.program.emit_jump(Opcode.Jump.value, end_label)

        compiler.program.emit_label(true_label)
        compiler.program.emit(Opcode.LoadConst.value, result, 1)

        compiler.program.emit_label(end_label)
        return result
