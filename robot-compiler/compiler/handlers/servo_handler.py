from ..generated.opcode import Opcode

class ServoHandler:
    @staticmethod
    def set_servo(compiler, node):
        compiler.validate_argument_count(node, "set_servo", 2)
        compiler.program.emit(Opcode.Nop.value, 0, 0, 0)

    @staticmethod
    def set_seering_engine(compiler, node):
        compiler.validate_argument_count(node, "set_seering_engine", 2)
        compiler.program.emit(Opcode.Nop.value, 0, 0, 0)

    @staticmethod
    def set_seering_engine_time(compiler, node):
        compiler.validate_argument_count(node, "set_seering_engine_time", 3)
        compiler.program.emit(Opcode.Nop.value, 0, 0, 0)