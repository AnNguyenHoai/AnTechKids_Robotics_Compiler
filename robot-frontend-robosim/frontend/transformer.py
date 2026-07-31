import ast
from frontend.mapping import ROBOSIM_API, SENSOR_API_MAPPING


class RoboSimTransformer(ast.NodeTransformer):
    """Transform RoboSim AST to Standard Robot API AST."""

    # ----------------------------------------------------------------------
    # Remove 'import rcu' and 'import _thread' statements
    # ----------------------------------------------------------------------

    def visit_Import(self, node):
        new_names = [alias for alias in node.names if alias.name not in ('rcu', '_thread')]
        if new_names:
            node.names = new_names
            return node
        return None

    def visit_ImportFrom(self, node):
        if node.module in ('rcu', '_thread'):
            return None
        return node

    # ----------------------------------------------------------------------
    # Transform expressions: function calls
    # ----------------------------------------------------------------------

    def visit_Expr(self, node):
        self.generic_visit(node)

        # Handle rcu.SetMoveRunSecond -> forward, wait, stop
        if (isinstance(node.value, ast.Call)
                and isinstance(node.value.func, ast.Attribute)
                and node.value.func.attr == "SetMoveRunSecond"
                and isinstance(node.value.func.value, ast.Name)
                and node.value.func.value.id == "rcu"):
            return self._handle_move_run_second(node.value)

        # Handle rcu.SetMoveRun -> forward/backward/turn_left/turn_right
        if (isinstance(node.value, ast.Call)
                and isinstance(node.value.func, ast.Attribute)
                and node.value.func.attr == "SetMoveRun"
                and isinstance(node.value.func.value, ast.Name)
                and node.value.func.value.id == "rcu"):
            return self._handle_move_run(node.value)

        # Handle rcu.SetMoveStop -> stop()
        if (isinstance(node.value, ast.Call)
                and isinstance(node.value.func, ast.Attribute)
                and node.value.func.attr == "SetMoveStop"
                and isinstance(node.value.func.value, ast.Name)
                and node.value.func.value.id == "rcu"):
            return ast.Expr(
                ast.Call(
                    func=ast.Name(id="stop", ctx=ast.Load()),
                    args=[],
                    keywords=[]
                )
            )

        # Handle rcu.SetWaitForTime -> wait(milliseconds)
        if (isinstance(node.value, ast.Call)
                and isinstance(node.value.func, ast.Attribute)
                and node.value.func.attr == "SetWaitForTime"
                and isinstance(node.value.func.value, ast.Name)
                and node.value.func.value.id == "rcu"):
            arg = node.value.args[0]
            if isinstance(arg, ast.Constant) and isinstance(arg.value, (int, float)):
                ms = int(arg.value * 1000)
                wait_arg = ast.Constant(value=ms)
            else:
                wait_arg = ast.BinOp(left=arg, op=ast.Mult(), right=ast.Constant(value=1000))
            return ast.Expr(
                ast.Call(
                    func=ast.Name(id="wait", ctx=ast.Load()),
                    args=[wait_arg],
                    keywords=[]
                )
            )

        # Handle _thread.start_new_thread(func, ()) -> func()
        if (isinstance(node.value, ast.Call)
                and isinstance(node.value.func, ast.Attribute)
                and isinstance(node.value.func.value, ast.Name)
                and node.value.func.value.id == '_thread'
                and node.value.func.attr == 'start_new_thread'):
            return self._handle_thread_start(node.value)

        # Handle rcu.SetMoveSpeed(left, right) -> set_motor_speed(left, right)
        if (isinstance(node.value, ast.Call)
                and isinstance(node.value.func, ast.Attribute)
                and node.value.func.attr == "SetMoveSpeed"
                and isinstance(node.value.func.value, ast.Name)
                and node.value.func.value.id == "rcu"):
            return self._handle_move_speed(node.value)

        # Handle rcu.SetServo(port, angle) -> set_servo(port, angle)
        if (isinstance(node.value, ast.Call)
                and isinstance(node.value.func, ast.Attribute)
                and node.value.func.attr == "SetServo"
                and isinstance(node.value.func.value, ast.Name)
                and node.value.func.value.id == "rcu"):
            return self._handle_simple_call(node.value, "set_servo", 2)

        # Handle rcu.Set3CLed(port, state) -> set_3c_led(port, state)
        if (isinstance(node.value, ast.Call)
                and isinstance(node.value.func, ast.Attribute)
                and node.value.func.attr == "Set3CLed"
                and isinstance(node.value.func.value, ast.Name)
                and node.value.func.value.id == "rcu"):
            return self._handle_simple_call(node.value, "set_3c_led", 2)

        # Handle rcu.SetLightSensorLed(port, state) -> set_light_sensor_led(port, state)
        if (isinstance(node.value, ast.Call)
                and isinstance(node.value.func, ast.Attribute)
                and node.value.func.attr == "SetLightSensorLed"
                and isinstance(node.value.func.value, ast.Name)
                and node.value.func.value.id == "rcu"):
            return self._handle_simple_call(node.value, "set_light_sensor_led", 2)

        # Handle rcu.SetMotorStraightAngle(left_port, right_port, speed, angle) -> set_motor_straight_angle(...)
        if (isinstance(node.value, ast.Call)
                and isinstance(node.value.func, ast.Attribute)
                and node.value.func.attr == "SetMotorStraightAngle"
                and isinstance(node.value.func.value, ast.Name)
                and node.value.func.value.id == "rcu"):
            return self._handle_simple_call(node.value, "set_motor_straight_angle", 4)

        # Handle rcu.line_intersection_stop(speed, type) -> line_intersection_stop(speed, type)
        if (isinstance(node.value, ast.Call)
                and isinstance(node.value.func, ast.Attribute)
                and node.value.func.attr == "line_intersection_stop"
                and isinstance(node.value.func.value, ast.Name)
                and node.value.func.value.id == "rcu"):
            return self._handle_simple_call(node.value, "line_intersection_stop", 2)

        # Handle rcu.SetMp3Play(index) -> set_mp3_play(index)
        if (isinstance(node.value, ast.Call)
                and isinstance(node.value.func, ast.Attribute)
                and node.value.func.attr == "SetMp3Play"
                and isinstance(node.value.func.value, ast.Name)
                and node.value.func.value.id == "rcu"):
            return self._handle_simple_call(node.value, "set_mp3_play", 1)
        
        return node

    def _handle_simple_call(self, call, target_name, expected_args):
        """Helper to transform a simple RoboSim call to canonical."""
        if len(call.args) != expected_args:
            raise SyntaxError(f"{call.func.attr}() expects exactly {expected_args} argument(s)")
        return ast.Expr(
            ast.Call(
                func=ast.Name(id=target_name, ctx=ast.Load()),
                args=call.args,
                keywords=[]
            )
        )
    
        return node

    # ----------------------------------------------------------------------
    # Transform all calls, including nested ones
    # ----------------------------------------------------------------------

    def visit_Call(self, node):
        # First, visit child nodes to transform any nested RoboSim calls
        node = self.generic_visit(node)

        # Check if this is a RoboSim sensor API call
        if (isinstance(node.func, ast.Attribute)
                and isinstance(node.func.value, ast.Name)
                and node.func.value.id == 'rcu'):
            attr = node.func.attr
            mapping = SENSOR_API_MAPPING.get(attr)
            if mapping:
                return self._transform_sensor_call(node, attr, mapping)

        return node

    # ----------------------------------------------------------------------
    # Helper methods
    # ----------------------------------------------------------------------

    def _handle_move_run_second(self, call):
        direction = call.args[0].value
        speed = call.args[1]
        seconds = call.args[2]

        if isinstance(seconds, ast.Constant) and isinstance(seconds.value, (int, float)):
            ms = int(seconds.value * 1000)
            wait_arg = ast.Constant(value=ms)
        else:
            wait_arg = ast.BinOp(left=seconds, op=ast.Mult(), right=ast.Constant(value=1000))

        forward_call = ast.Call(
            func=ast.Name(id=ROBOSIM_API.get(direction, direction), ctx=ast.Load()),
            args=[speed],
            keywords=[]
        )
        wait_call = ast.Call(
            func=ast.Name(id="wait", ctx=ast.Load()),
            args=[wait_arg],
            keywords=[]
        )
        stop_call = ast.Call(
            func=ast.Name(id="stop", ctx=ast.Load()),
            args=[],
            keywords=[]
        )

        return [
            ast.Expr(forward_call),
            ast.Expr(wait_call),
            ast.Expr(stop_call)
        ]

    def _handle_move_run(self, call):
        direction = call.args[0].value
        speed = call.args[1]
        func_name = ROBOSIM_API.get(direction, direction)
        return ast.Expr(
            ast.Call(
                func=ast.Name(id=func_name, ctx=ast.Load()),
                args=[speed],
                keywords=[]
            )
        )

    def _handle_thread_start(self, call):
        func = call.args[0]
        return ast.Expr(
            ast.Call(
                func=func,
                args=[],
                keywords=[]
            )
        )

    def _transform_sensor_call(self, node, attr, mapping):
        """Transform a RoboSim sensor call based on mapping."""
        expected = mapping["expected_args"]
        actual = len(node.args)
        if actual != expected:
            raise SyntaxError(
                f"RoboSim API '{attr}()' expects exactly {expected} argument(s), got {actual}"
            )

        target_name = mapping["target"]
        arg_indices = mapping["arg_indices"]
        args = [node.args[i] for i in arg_indices if i < len(node.args)]

        return ast.Call(
            func=ast.Name(id=target_name, ctx=ast.Load()),
            args=args,
            keywords=[]
        )
    def _handle_move_speed(self, call):
        if len(call.args) != 2:
            raise SyntaxError("SetMoveSpeed expects exactly 2 arguments")
        left = call.args[0]
        right = call.args[1]
        return ast.Expr(
            ast.Call(
                func=ast.Name(id="set_motor_speed", ctx=ast.Load()),
                args=[left, right],
                keywords=[]
            )
        )