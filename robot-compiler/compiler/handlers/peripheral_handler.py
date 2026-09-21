from ..generated.opcode import Opcode

class PeripheralHandler:
    @staticmethod
    def set_mp3_play(compiler, node):
        compiler.validate_argument_count(node, "set_mp3_play", 1)
        index = compiler.resolve_argument(node.args[0])
        compiler.program.emit(Opcode.SetMp3Play.value, index, 0, 0)

    @staticmethod
    def set_lizard(compiler, node):
        # Stub: accepted by the language, intentionally emits no runtime bytecode.
        compiler.validate_argument_count(node, "set_lizard", 1)
