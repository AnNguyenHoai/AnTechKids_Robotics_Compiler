from ..generated.opcode import Opcode

class SensorHandler:
    @staticmethod
    def read_ultrasonic(compiler, node):
        compiler.validate_argument_count(node, "read_ultrasonic", 0)
        dest = compiler.allocate_temp()
        compiler.program.emit(Opcode.ReadUltrasonic.value, dest, 0, 0)
        return dest

    @staticmethod
    def read_touch(compiler, node):
        compiler.validate_argument_count(node, "read_touch", 1)
        port = compiler.resolve_argument(node.args[0])
        dest = compiler.allocate_temp()
        compiler.program.emit(Opcode.ReadTouch.value, port, dest, 0)
        return dest

    @staticmethod
    def read_light(compiler, node):
        compiler.validate_argument_count(node, "read_light", 1)
        channel = compiler.resolve_argument(node.args[0])
        dest = compiler.allocate_temp()
        compiler.program.emit(Opcode.ReadLight.value, channel, dest, 0)
        return dest

    @staticmethod
    def read_color(compiler, node):
        compiler.validate_argument_count(node, "read_color", 0)
        dest = compiler.allocate_temp()
        compiler.program.emit(Opcode.ReadColor.value, dest, 0, 0)
        return dest

    @staticmethod
    def read_line(compiler, node):
        compiler.validate_argument_count(node, "read_line", 1)
        channel = compiler.resolve_argument(node.args[0])
        dest = compiler.allocate_temp()
        compiler.program.emit(Opcode.ReadLine.value, channel, dest, 0)
        return dest