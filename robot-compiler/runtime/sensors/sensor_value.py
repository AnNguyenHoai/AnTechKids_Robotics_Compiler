# runtime/sensors/sensor_value.py
from dataclasses import dataclass
from typing import Optional, Any
import time

@dataclass
class SensorValue:
    """Encapsulates a sensor reading with metadata."""
    raw: Any                     # raw value from hardware
    normalized: float            # normalized value (0.0 to 1.0)
    timestamp: float = None      # time of reading (optional)
    valid: bool = True
    quality: float = 1.0         # 0.0 to 1.0

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = time.time()