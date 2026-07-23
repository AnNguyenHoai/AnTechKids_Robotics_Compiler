# runtime/hardware/esp32/logger.py
import sys
from ..interfaces import ILogger

class ESP32Logger(ILogger):
    def __init__(self, level: str = "INFO"):
        self.level = level.upper()

    def _log(self, level: str, msg: str):
        print(f"[{level}] {msg}", file=sys.stdout)

    def info(self, msg: str) -> None:
        if self.level in ("INFO", "DEBUG"):
            self._log("INFO", msg)

    def warn(self, msg: str) -> None:
        if self.level in ("WARN", "INFO", "DEBUG"):
            self._log("WARN", msg)

    def error(self, msg: str) -> None:
        self._log("ERROR", msg)

    def debug(self, msg: str) -> None:
        if self.level == "DEBUG":
            self._log("DEBUG", msg)