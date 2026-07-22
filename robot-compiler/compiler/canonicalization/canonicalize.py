from ..passes import CompilerPass, PassContext, PassResult
from ..ir import IRValue, ValueKind, IROpcode


class CanonicalizationPass(CompilerPass):
    name = "Canonicalization"

    def run(self, context: PassContext) -> PassResult:
        program = context.program
        for func in program.functions:
            for block in func.blocks:
                for ins in block.instructions:
                    self._canonicalize_instruction(ins)
        return PassResult.ok()

    def _canonicalize_instruction(self, ins):
        # Normalize direction strings to lowercase
        # For MOVE_RUN and MOVE_RUN_TIME, the first operand is direction
        if ins.opcode in (IROpcode.MOVE_RUN, IROpcode.MOVE_RUN_TIME):
            if ins.operands:
                dir_op = ins.operands[0]
                if dir_op.kind == ValueKind.STRING:
                    # Convert to lowercase
                    dir_str = dir_op.value.lower()
                    # Replace with new IRValue (immutable)
                    ins.operands[0] = IRValue.string(dir_str)

        # Normalize boolean constants (0/1)
        # Could be extended

        # Ensure WAIT duration is positive (if float or int)
        if ins.opcode == IROpcode.WAIT and ins.operands:
            dur = ins.operands[0]
            if dur.kind in (ValueKind.INTEGER, ValueKind.FLOAT):
                val = dur.value
                if val < 0:
                    # Could emit warning, but for now set to 0
                    if dur.kind == ValueKind.INTEGER:
                        ins.operands[0] = IRValue.integer(0)
                    else:
                        ins.operands[0] = IRValue.float(0.0)