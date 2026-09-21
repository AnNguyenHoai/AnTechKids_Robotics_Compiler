from ..generated.opcode import Opcode

class ServoHandler:
    @staticmethod
    def set_servo(compiler, node):
        # Stub: accepted by the language, intentionally emits no runtime bytecode.
        compiler.validate_argument_count(node, "set_servo", 2)

    @staticmethod
    def set_seering_engine(compiler, node):
        # Stub: accepted by the language, intentionally emits no runtime bytecode.
        compiler.validate_argument_count(node, "set_seering_engine", 2)

    @staticmethod
    def set_seering_engine_time(compiler, node):
        # Stub: accepted by the language, intentionally emits no runtime bytecode.
        compiler.validate_argument_count(node, "set_seering_engine_time", 3)
