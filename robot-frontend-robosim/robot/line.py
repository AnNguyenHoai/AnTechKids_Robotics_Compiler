"""
AUTO GENERATED FILE – Line API
"""

def line_basis(speed: int) -> None:
    """
    Basic line following step (adjust motors based on sensor mask)

    Args:
        speed (int):
    """
    pass

def line_follow(speed: int) -> None:
    """
    Follow line continuously until lost

    Args:
        speed (int):
    """
    pass

def line_stop() -> None:
    """
    Stop line following (stop motors)

    """
    pass

def line_intersection_stop(speed: int, type: int) -> None:
    """
    Stop at line intersection

    Args:
        speed (int):
        type (int):
    """
    pass

def line_turn_encounterline(speed: int, angle: int, direction: int) -> None:
    """
    Turn until line encountered

    Args:
        speed (int):
        angle (int):
        direction (int):
    """
    pass

def line_for_bmp(speed: int, degree: int) -> None:
    """
    Follow line for a given degree (time-based approximation)

    Args:
        speed (int):
        degree (int):
    """
    pass

