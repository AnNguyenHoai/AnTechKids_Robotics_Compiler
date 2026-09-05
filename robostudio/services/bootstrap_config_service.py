from __future__ import annotations

import sys
from pathlib import Path

# The test suite imports `ui.robot_tab` directly. In that execution mode
# Python starts with `tests/` on sys.path, so repository-level `tools/` is not
# automatically importable. Resolve the repository root from this module and
# expose it before importing the canonical bootstrap helper.
_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

import tools.bootstrap_config as bootstrap_config

ROOT = _ROOT
ARDUINO_SKETCH = ROOT / "robot-platform" / "main"
ARDUINO_BOOTSTRAP_HEADER = (
    ARDUINO_SKETCH / "include" / "generated" / "generated_bootstrap_config.h"
)


class BootstrapConfigService:
    """Generate and validate local-only Wi-Fi/OTA bootstrap data."""

    def __init__(self, root: Path | None = None):
        self.root = root or ROOT
        self.arduino_sketch = self.root / "robot-platform" / "main"
        self.arduino_bootstrap_header = (
            self.arduino_sketch / "include" / "generated" / "generated_bootstrap_config.h"
        )

    def generate(self, ssid: str, wifi_password: str, ota_password: str,
                 output: Path | None = None) -> Path:
        if not ssid.strip():
            raise ValueError("Wi-Fi SSID is required.")
        if not ota_password:
            raise ValueError("OTA password is required for first-flash bootstrap.")
        output = output or (self.root / ".robostudio" / "bootstrap" / "robot_bootstrap.json")
        output.parent.mkdir(parents=True, exist_ok=True)

        try:
            config = bootstrap_config.make_config(ssid, wifi_password, ota_password)
            output.write_text(
                __import__("json").dumps(config, indent=2) + "\n", encoding="utf-8"
            )
            bootstrap_config.write_arduino_header(config, self.arduino_bootstrap_header)
        except (OSError, ValueError) as exc:
            raise RuntimeError(
                str(exc) or "Unable to generate bootstrap config."
            ) from exc
        return output

    def arduino_sketch_path(self) -> Path:
        return self.arduino_sketch

    def arduino_header_path(self) -> Path:
        return self.arduino_bootstrap_header

    def open_arduino_sketch(self) -> tuple[bool, str]:
        """Open the robot sketch with Arduino IDE, with OS fallback."""
        import os
        import shutil
        import subprocess

        sketch = self.arduino_sketch
        main_ino = sketch / "main.ino"
        if not main_ino.is_file():
            return False, f"Arduino sketch not found: {main_ino}"

        candidates: list[str] = []
        configured = os.getenv("ARDUINO_IDE", "").strip()
        if configured:
            candidates.append(configured)
        for command in ("arduino-ide", "arduino"):
            found = shutil.which(command)
            if found:
                candidates.append(found)

        if os.name == "nt":
            local = os.getenv("LOCALAPPDATA", "")
            program_files = os.getenv("PROGRAMFILES", "")
            program_files_x86 = os.getenv("PROGRAMFILES(X86)", "")
            candidates.extend([
                str(Path(local) / "Programs" / "Arduino IDE" / "Arduino IDE.exe") if local else "",
                str(Path(program_files) / "Arduino IDE" / "Arduino IDE.exe") if program_files else "",
                str(Path(program_files_x86) / "Arduino IDE" / "Arduino IDE.exe") if program_files_x86 else "",
                str(Path(program_files) / "Arduino IDE" / "arduino.exe") if program_files else "",
                str(Path(program_files_x86) / "Arduino IDE" / "arduino.exe") if program_files_x86 else "",
            ])

        for candidate in candidates:
            if not candidate or not Path(candidate).is_file():
                continue
            try:
                subprocess.Popen([candidate, str(main_ino)], cwd=str(sketch))
                return True, f"Arduino IDE opened: {main_ino}"
            except OSError:
                continue

        try:
            if os.name == "nt":
                os.startfile(str(main_ino))
            elif shutil.which("open"):
                subprocess.Popen(["open", str(main_ino)])
            elif shutil.which("xdg-open"):
                subprocess.Popen(["xdg-open", str(main_ino)])
            else:
                return False, "Arduino IDE executable was not found."
            return True, f"Opened Arduino sketch: {main_ino}"
        except OSError as exc:
            return False, f"Unable to open Arduino sketch: {exc}"

    def validate(self, path: Path) -> bool:
        try:
            bootstrap_config.validate_config(path.resolve())
        except ValueError as exc:
            raise ValueError(str(exc)) from exc
        return True
