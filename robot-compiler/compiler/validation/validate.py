from typing import Set
from ..passes import CompilerPass, PassContext, PassResult
from ..ir import IRProgram, IRFunction, IRBasicBlock, IRInstruction, IROpcode
from ..diagnostics.diagnostic import Severity, Diagnostic
from ..ir.source_location import SourceLocation


class ValidationPass(CompilerPass):
    name = "Validation"

    def run(self, context: PassContext) -> PassResult:
        program = context.program
        diag = context.diagnostics
        ok = True

        # 1. Program must have at least one function
        if not program.functions:
            diag.error("Program has no functions")
            ok = False

        # 2. Check each function
        func_names: Set[str] = set()
        for func in program.functions:
            # Function names must be unique
            if func.name in func_names:
                diag.error(f"Duplicate function name: {func.name}")
                ok = False
            func_names.add(func.name)

            # 3. Function must have at least one block
            if not func.blocks:
                diag.error(f"Function '{func.name}' has no basic blocks")
                ok = False

            # 4. Check each block
            for block in func.blocks:
                # 5. Block must not be empty (except maybe future)
                if block.is_empty():
                    diag.warning(f"Block '{block.label or '(unnamed)'}' is empty in function '{func.name}'")
                    # Not an error, but warning

                # 6. Check instructions
                for ins in block.instructions:
                    self._validate_instruction(ins, func.name, diag)

        # If errors, return failure
        if diag.has_errors():
            return PassResult(False, diag.diagnostics)
        return PassResult.ok()

    def _validate_instruction(self, ins: IRInstruction, func_name: str, diag):
        # Validate opcode
        if not isinstance(ins.opcode, IROpcode):
            diag.error(f"Invalid opcode type in function '{func_name}'", ins.location)
            return

        # Validate operands based on opcode
        required_operands = self._required_operands(ins.opcode)
        if len(ins.operands) < required_operands:
            diag.error(
                f"Instruction {ins.opcode.name} expects at least {required_operands} operands, got {len(ins.operands)}",
                ins.location
            )

        # Validate that operands are IRValue
        for op in ins.operands:
            # Could add type checks later
            pass

    def _required_operands(self, opcode: IROpcode) -> int:
        # Minimum number of operands required
        if opcode in (IROpcode.MOVE_RUN, IROpcode.WAIT, IROpcode.CALL, IROpcode.JUMP):
            return 1
        if opcode in (IROpcode.MOVE_RUN_TIME, IROpcode.JUMP_IF_FALSE, IROpcode.JUMP_IF_TRUE):
            return 2
        # MOVE_STOP, RETURN have 0
        return 0