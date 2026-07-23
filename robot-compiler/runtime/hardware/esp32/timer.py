# runtime/hardware/esp32/timer.py
import time
from ..interfaces import ITimer

class ESP32Timer(ITimer):
    def delay(self, ms: int) -> None:
        time.sleep(ms / 1000.0)

    def millis(self) -> int:
        return int(time.time() * 1000)

    def micros(self) -> int:
        return int(time.time() * 1_000_000)