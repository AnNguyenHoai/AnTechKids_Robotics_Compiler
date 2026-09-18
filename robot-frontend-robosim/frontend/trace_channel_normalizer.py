import ast


TRACE_CHANNEL_APIS = {
    "GetTraceV2I2C",
    "GetTraceV2I2CState",
    "GetTraceV2I2CChxState",
}

ROBOSIM_TRACE_CHANNEL_MIN = 1
ROBOSIM_TRACE_CHANNEL_MAX = 7
REAL_TRACE_CHANNEL_MIN = 0
REAL_TRACE_CHANNEL_MAX = 2


class RoboSimTraceChannelNormalizer(ast.NodeTransformer):
    """Normalize RoboSim 1-based trace channels to real-robot 0-based channels.

    RoboSim exposes trace channels 1..7, while the current real robot exposes
    only channels 0..2. Therefore only RoboSim channels 1..3 can be compiled
    for the real target:

        RoboSim 1 -> real 0
        RoboSim 2 -> real 1
        RoboSim 3 -> real 2

    Channels 4..7 are valid in RoboSim but do not exist on the real target and
    must fail compilation instead of being silently clamped or wrapped.
    """

    def visit_Call(self, node):
        node = self.generic_visit(node)

        if not self._is_trace_channel_call(node):
            return node

        api_name = node.func.attr
        if len(node.args) != 2:
            # Keep argument-count diagnostics owned by RoboSimTransformer.
            return node

        channel_arg = node.args[1]
        if not (isinstance(channel_arg, ast.Constant) and type(channel_arg.value) is int):
            raise SyntaxError(
                f"RoboSim API '{api_name}()' requires a literal trace channel for "
                "real-robot compilation; supported RoboSim channels are 1..3 "
                "(mapped to real channels 0..2)"
            )

        channel = channel_arg.value
        if not ROBOSIM_TRACE_CHANNEL_MIN <= channel <= ROBOSIM_TRACE_CHANNEL_MAX:
            raise SyntaxError(
                f"RoboSim API '{api_name}()' received invalid trace channel {channel}; "
                "RoboSim trace channels are 1..7"
            )

        if channel > REAL_TRACE_CHANNEL_MAX + 1:
            raise SyntaxError(
                f"RoboSim trace channel {channel} is not available on the real robot; "
                "supported RoboSim channels are 1..3 (mapped to real channels 0..2)"
            )

        normalized = ast.Constant(value=channel - 1)
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
