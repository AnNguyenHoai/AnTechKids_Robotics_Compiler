"""
RobotOpcodeRegistry – metadata for opcodes.
"""

from ..isa import RobotOpcode


class RobotOpcodeRegistry:
    @staticmethod
    def get_opcode_number(opcode: RobotOpcode) -> int:
        return opcode.value

    @staticmethod
    def get_opcode_by_number(num: int) -> RobotOpcode:
        try:
            return RobotOpcode(num)
        except ValueError:
            raise ValueError(f"Invalid opcode number: {num}")

    @staticmethod
    def get_operand_count(opcode: RobotOpcode) -> int:
        # For simplicity, return a fixed value; can be extended later
        return 0

    @staticmethod
    def get_mnemonic(opcode: RobotOpcode) -> str:
        return opcode.name

    @staticmethod
    def get_description(opcode: RobotOpcode) -> str:
        return f"{opcode.name} instruction"