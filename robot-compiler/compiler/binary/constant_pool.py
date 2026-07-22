# compiler/binary/constant_pool.py
from typing import List, Any
from .model import ConstantPool
from ..isa import ISAProgram, OperandKind

class ConstantPoolBuilder:
    @staticmethod
    def build(program: ISAProgram) -> ConstantPool:
        constants = []
        seen = set()
        for func in program.functions:
            for ins in func.instructions:
                for op in ins.operands:
                    if op.kind == OperandKind.STRING:
                        s = op.as_string()
                        if s not in seen:
                            seen.add(s)
                            constants.append(s)
        # Có thể mở rộng với các loại hằng khác (int, float, bool) sau này
        return ConstantPool(constants)