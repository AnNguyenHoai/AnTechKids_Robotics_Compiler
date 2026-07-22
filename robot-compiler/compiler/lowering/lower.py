from ..passes import CompilerPass, PassContext, PassResult
from ..ir import IRValue, ValueKind, IROpcode


class LoweringPass(CompilerPass):
    name = "Lowering"

    def run(self, context: PassContext) -> PassResult:
        program = context.program
        for func in program.functions:
            for block in func.blocks:
                for ins in block.instructions:
                    self._lower_instruction(ins)
        return PassResult.ok()

    def _lower_instruction(self, ins):
        # Currently, Platform IR is already low-level enough.
        # This pass can transform high-level calls if needed.
        # For now, we just ensure operands are in a canonical form.
        # Example: replace string direction with enum (not implemented yet)

        # Could convert MOVE_RUN with string to an enum constant
        # For future extension
        pass