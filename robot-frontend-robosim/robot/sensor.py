"""
AUTO GENERATED FILE – Sensor API
"""

def read_ultrasonic() -> None:
    """
    Read ultrasonic distance in cm

    """
    pass

def read_touch(port: int) -> None:
    """
    Read touch sensor state (0/1)

    Args:
        port (int):
    """
    pass

def read_light(channel: int) -> None:
    """
    Read light sensor raw value (0-1023)

    Args:
        channel (int):
    """
    pass

def read_color() -> None:
    """
    Read color sensor (placeholder)

    """
    pass

def read_line(channel: int) -> None:
    """
    Read line sensor (0=white, 1=dark)

    Args:
        channel (int):
    """
    pass

def get_trace_value(port: int, channel: int) -> None:
    """
    Get trace sensor value (0/50/100 based on line detection)

    Args:
        port (int):
        channel (int):
    """
    pass

def get_trace_state(port: int, channel: int) -> None:
    """
    Get trace sensor state (boolean)

    Args:
        port (int):
        channel (int):
    """
    pass

def get_trace_raw(port: int) -> None:
    """
    Get raw bitmask of all 3 trace sensors

    Args:
        port (int):
    """
    pass

