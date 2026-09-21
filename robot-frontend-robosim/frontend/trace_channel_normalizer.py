import ast


TRACE_CHANNEL_APIS = {
    "GetTraceV2I2C",
    "GetTraceV2I2CState",
    "GetTraceV2I2CChxState",
}

ROBOSIM_TRACE_CHANNEL_MIN = 1
ROBOSIM_TRACE_CHANNEL_MAX = 7


class RoboSimTraceChannelNormalizer(ast.NodeTransformer):
    """Normalize RoboSim 1-based trace channels to canonical 0-based channels.

    RoboSim exposes trace channels 1..7. The frontend only normalizes source
    representation:

        RoboSim 1 -> canonical 0
        ...
        RoboSim 7 -> canonical 6

    H33 deliberately moves target availability out of the frontend. The
    compiler target contract decides whether a canonical channel exists on the
    selected target (for example 0..2 on ESP32 versus 0..6 in RoboSim).
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
        if isinstance(channel_arg, ast.Constant) and type(channel_arg.value) is int:
            channel = channel_arg.value
            if not ROBOSIM_TRACE_CHANNEL_MIN <= channel <= ROBOSIM_TRACE_CHANNEL_MAX:
                raise SyntaxError(
                    f"RoboSim API '{api_name}()' received invalid trace channel {channel}; "
                    "RoboSim trace channels are 1..7"
                )
            normalized = ast.Constant(value=channel - 1)
        else:
            # Representation normalization only. Target/resource safety remains
            # compiler-owned, so preserve a dynamic expression and let H33
            # reject it fail-closed until runtime bounds validation exists.
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
