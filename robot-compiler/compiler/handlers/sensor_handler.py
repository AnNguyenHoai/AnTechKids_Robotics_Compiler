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

    @staticmethod
    def get_trace_value(compiler, node):
        compiler.validate_argument_count(node, "get_trace_value", 2)
        port = compiler.resolve_argument(node.args[0])
        channel = compiler.resolve_argument(node.args[1])
        dest = compiler.allocate_temp()
        compiler.program.emit(Opcode.GetTraceValue.value, port, channel, dest)
        return dest

    @staticmethod
    def get_trace_state(compiler, node):
        compiler.validate_argument_count(node, "get_trace_state", 2)
        port = compiler.resolve_argument(node.args[0])
        channel = compiler.resolve_argument(node.args[1])
        dest = compiler.allocate_temp()
        compiler.program.emit(Opcode.GetTraceState.value, port, channel, dest)
        return dest

    @staticmethod
    def get_trace_raw(compiler, node):
        compiler.validate_argument_count(node, "get_trace_raw", 1)
        port = compiler.resolve_argument(node.args[0])
        dest = compiler.allocate_temp()
        compiler.program.emit(Opcode.GetTraceRaw.value, port, 0, dest)
        return dest

    @staticmethod
    def get_light_sensor_data(compiler, node):
        compiler.validate_argument_count(node, "get_light_sensor_data", 1)
        dest = compiler.allocate_temp()
        # Dummy: always return 0
        compiler.program.emit(Opcode.LoadConst.value, dest, 0)
        return dest