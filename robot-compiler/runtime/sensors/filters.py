# runtime/sensors/filters.py
from collections import deque
from typing import List, Any

class MovingAverageFilter:
    def __init__(self, window_size: int = 5):
        self.window_size = window_size
        self._buffer = deque(maxlen=window_size)

    def filter(self, value: float) -> float:
        self._buffer.append(value)
        if len(self._buffer) == 0:
            return 0.0
        return sum(self._buffer) / len(self._buffer)

class MedianFilter:
    def __init__(self, window_size: int = 5):
        self.window_size = window_size
        self._buffer = deque(maxlen=window_size)

    def filter(self, value: float) -> float:
        self._buffer.append(value)
        if len(self._buffer) == 0:
            return 0.0
        sorted_vals = sorted(self._buffer)
        mid = len(sorted_vals) // 2
        return sorted_vals[mid]

class ThresholdFilter:
    def __init__(self, threshold: float = 0.5, hysteresis: float = 0.1):
        self.threshold = threshold
        self.hysteresis = hysteresis
        self._last_state = False

    def filter(self, value: float) -> bool:
        if value >= self.threshold + self.hysteresis:
            self._last_state = True
        elif value <= self.threshold - self.hysteresis:
            self._last_state = False
        # else keep last state
        return self._last_state