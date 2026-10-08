import ast


TRACE_CHANNEL_APIS = {
    "GetTraceV2I2C",
    "GetTraceV2I2CState",
    "GetTraceV2I2CChxState",
}

ROBOSIM_TRACE_CHANNEL_MIN = 1
ROBOSIM_TRACE_CHANNEL_MAX = 7

# Physical/public Line5 contract:
#   0=Left, 1=Center, 2=Right, 3=Far Left, 4=Far Right.
#
# RoboSim exposes seven logical trace positions. ESP32 has five physical eyes,
# so the physical rewrite uses an explicit center-preserving ADAPTED projection:
#   RoboSim 1,2 -> Far Left
#   RoboSim 3   -> Left
#   RoboSim 4   -> Center
#   RoboSim 5   -> Right
#   RoboSim 6,7 -> Far Right
#
# This is intentionally lossy and must never be interpreted as seven
# independent physical sensors.
ESP32_LINE5_PROJECTION = {
    1: 3,
    2: 3,
    3: 0,
    4: 1,
    5: 2,
    6: 4,
    7: 4,
}


def _integer_literal_value(node):
    """Return an integer source literal value, including unary +/- forms."""
    if isinstance(node, ast.Constant) and type(node.value) is int:
        return node.value

    if (
        isinstance(node, ast.UnaryOp)
        and isinstance(node.operand, ast.Constant)
        and type(node.operand.value) is int
    ):
        if isinstance(node.op, ast.USub):
            return -node.operand.value
        if isinstance(node.op, ast.UAdd):
            return node.operand.value

    return None


class RoboSimTraceChannelNormalizer(ast.NodeTransformer):
    """Normalize RoboSim trace channels for the selected target.

    RoboSim source always accepts 1..7.

    Simulation/default:
        RoboSim 1..7 -> canonical 0..6

    ESP32 physical:
        RoboSim 1..7 -> projected Line5 physical channels 0..4.

    Standard Robot API callers are unaffected because this normalizer runs only
    in the RoboSim frontend rewrite path.
    """

    def __init__(self, target="robosim"):
        super().__init__()
        self.target = target

    def visit_Call(self, node):
        node = self.generic_visit(node)

        if not self._is_trace_channel_call(node):
            return node

        api_name = node.func.attr
        if len(node.args) != 2:
            return node

        channel_arg = node.args[1]
        channel = _integer_literal_value(channel_arg)
        if channel is not None:
            if not ROBOSIM_TRACE_CHANNEL_MIN <= channel <= ROBOSIM_TRACE_CHANNEL_MAX:
                raise SyntaxError(
                    f"RoboSim API '{api_name}()' received invalid trace channel {channel}; "
                    "RoboSim trace channels are 1..7"
                )
            if self.target == "esp32":
                normalized = ast.Constant(value=ESP32_LINE5_PROJECTION[channel])
            else:
                normalized = ast.Constant(value=channel - 1)
        else:
            # Dynamic ESP32 projection is deliberately not guessed. Preserve a
            # dynamic expression and let H33 reject it fail-closed until a
            # runtime projection/bounds contract exists.
            normalized = ast.BinOp(
                left=channel_arg,
                op=ast.Sub(),
                right=ast.Constant(value=1),
            )

        node.args[1] = ast.copy_location(normalized, channel_arg)
        return node

    @staticmethod
    def _is_trace_channel_call(node):
        return (
            isinstance(node.func, ast.Attribute)
            and isinstance(node.func.value, ast.Name)
            and node.func.value.id == "rcu"
            and node.func.attr in TRACE_CHANNEL_APIS
        )
