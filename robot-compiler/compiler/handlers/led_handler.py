from ..generated.opcode import Opcode

class LedHandler:
    @staticmethod
    def set_3c_led(compiler, node):
        compiler.validate_argument_count(node, "set_3c_led", 2)
        port = compiler.resolve_argument(node.args[0])
        state = compiler.resolve_argument(node.args[1])
        compiler.program.emit(Opcode.Set3CLed.value, port, state, 0)

    @staticmethod
    def set_light_sensor_led(compiler, node):
        compiler.validate_argument_count(node, "set_light_sensor_led", 2)
        port = compiler.resolve_argument(node.args[0])
        state = compiler.resolve_argument(node.args[1])
        compiler.program.emit(Opcode.SetLightSensorLed.value, port, state, 0)