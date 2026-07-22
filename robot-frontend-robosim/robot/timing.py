"""
Timing API

This module defines the Standard Robot API for timing control.

Time conversion (e.g., seconds to milliseconds) must be handled by
the frontend layer. This API only accepts milliseconds.
"""


def wait(milliseconds: int) -> None:
    """
    Wait (delay) for the specified duration.

    This is a blocking delay. The robot will pause execution for
    the specified number of milliseconds before continuing to the
    next instruction.

    Args:
        milliseconds: Delay duration in milliseconds.

    Important:
        - Unit is milliseconds, NOT seconds.
        - Frontends must convert seconds to milliseconds before calling.
        - Example: wait(1000) delays for 1 second.

    Example:
        forward(80)
        wait(500)   # Wait 0.5 seconds
        stop()
    """
    # Stub implementation.
    # The compiler will replace this with bytecode.
    # The VM will call RobotAPI::Wait(ms) which executes delay().
    pass