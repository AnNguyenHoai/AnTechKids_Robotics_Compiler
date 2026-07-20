import ast

from ..error import CompilerError


class BoolHandler:

    @staticmethod
    def bool_op(compiler, node):

        if isinstance(node.op, ast.And):
            return BoolHandler._compile_and(
                compiler,
                node
            )

        raise CompilerError(
            f"Unsupported boolean operator: {type(node.op).__name__}"
        )

    @staticmethod
    def _compile_and(compiler, node):

        #
        # Allocate result
        #
        result = compiler.allocate_result()

        #
        # Labels
        #
        false_label = compiler.program.new_label()

        end_label = compiler.program.new_label()

        #
        # Evaluate every expression
        #
        for expr in node.values:

            value = compiler.visit(expr)

            compiler.program.emit_jump_if_false(

                compiler.opcodes.get("JumpIfFalse"),

                value,

                false_label

            )

        #
        # All expressions are true
        #
        compiler.program.emit(

            compiler.opcodes.get("LoadConst"),

            result,

            1

        )

        compiler.program.emit_jump(

            compiler.opcodes.get("Jump"),

            end_label

        )

        #
        # False branch
        #
        compiler.program.emit_label(
            false_label
        )

        compiler.program.emit(

            compiler.opcodes.get("LoadConst"),

            result,

            0

        )

        #
        # End
        #
        compiler.program.emit_label(
            end_label
        )

        return result