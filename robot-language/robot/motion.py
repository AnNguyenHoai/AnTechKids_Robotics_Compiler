"""
AUTO GENERATED FILE – Motion API
"""

def forward(speed: int) -> None:
    """
    Move robot forward

    Args:
        speed (int):
    """
    pass

def backward(speed: int) -> None:
    """
    Move robot backward

    Args:
        speed (int):
    """
    pass

def turn_left(speed: int) -> None:
    """
    Rotate robot left

    Args:
        speed (int):
    """
    pass

def turn_right(speed: int) -> None:
    """
    Rotate robot right

    Args:
        speed (int):
    """
    pass

def set_motor_speed(left_speed: int, right_speed: int) -> None:
    """
    Set motor speeds independently

    Args:
        left_speed (int):
        right_speed (int):
    """
    pass

def set_move_initialize(left_motor: int, right_motor: int, reverse: string) -> None:
    """
    Configure drive motors (left/right ports and reverse mode)

    Args:
        left_motor (int):
        right_motor (int):
        reverse (string):
    """
    pass

def set_move_run_angle(direction: string, speed: int, angle: int) -> None:
    """
    Move for a specified angle (wheel rotation or chassis turn)

    Args:
        direction (string):
        speed (int):
        angle (int):
    """
    pass

