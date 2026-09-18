from __future__ import annotations

import os
import shutil
import sys
from pathlib import Path

# Some legacy RoboStudio entry points add ``robostudio/`` rather than the
# repository/application root to sys.path. Keep the canonical tools package
# importable without deriving mutable paths from the caller CWD.
_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

import tools.bootstrap_config as bootstrap_config
from tools import runtime_paths

ROOT = _ROOT


class BootstrapConfigService:
    """Generate first-flash data without mutating the application payload.

    The firmware/Arduino sketch shipped with RoboStudio is an immutable
    template. Any generated bootstrap header and any sketch opened for manual
    editing live in a writable copy below ``ROBOSTUDIO_STATE_ROOT``.
    """

    def __init__(self, root: Path | None = None, state_root: Path | None = None):
        self.root = Path(root or runtime_paths.application_root()).expanduser().resolve()
        packaged = (
            runtime_paths.is_frozen()
            or os.environ.get(runtime_paths.RUNTIME_MODE_ENV) == "packaged"
            or os.environ.get(runtime_paths.DEPENDENCY_MODE_ENV) == "artifact-closed"
        )
        self.state_root = Path(
            state_root
            or runtime_paths.user_data_root(
                application_root_override=self.root,
                enforce_external=packaged,
            )
        ).expanduser().resolve()

        packaged_sketch = self.root / "firmware" / "robot-platform" / "main"
        source_sketch = self.root / "robot-platform" / "main"
        self.template_sketch = packaged_sketch if packaged_sketch.is_dir() else source_sketch

        self.bootstrap_root = self.state_root / "bootstrap"
        self.arduino_sketch = self.bootstrap_root / "arduino-sketch"
        self.arduino_bootstrap_header = (
            self.arduino_sketch / "include" / "generated" / "generated_bootstrap_config.h"
        )

    def _ensure_external_path(self, path: Path, *, label: str) -> Path:
        """Reject packaged writes that overlap the immutable application tree."""
        candidate = Path(path).expanduser().resolve()
        packaged = (
            runtime_paths.is_frozen()
            or os.environ.get(runtime_paths.RUNTIME_MODE_ENV) == "packaged"
            or os.environ.get(runtime_paths.DEPENDENCY_MODE_ENV) == "artifact-closed"
        )
        if packaged:
            try:
                candidate.relative_to(self.root)
            except ValueError:
                pass
            else:
                raise RuntimeError(
                    f"{label} must be outside the packaged RoboStudio application: {candidate}"
                )
        return candidate

    def _prepare_arduino_workspace(self, *, refresh: bool) -> Path:
        """Materialize a writable copy of the read-only Arduino sketch template."""
        if not self.template_sketch.is_dir():
            raise RuntimeError(f"Arduino sketch template not found: {self.template_sketch}")
        destination = self._ensure_external_path(
            self.arduino_sketch, label="Arduino bootstrap workspace"
        )
        try:
            if refresh and destination.exists():
                if not destination.is_dir():
                    raise OSError("workspace exists but is not a directory")
                shutil.rmtree(destination)
            if not destination.exists():
                destination.parent.mkdir(parents=True, exist_ok=True)
                shutil.copytree(
                    self.template_sketch,
                    destination,
                    ignore=shutil.ignore_patterns(
                        ".git", ".venv", ".pio", "__pycache__", ".pytest_cache"
                    ),
                )
        except OSError as exc:
            raise RuntimeError(
                f"Unable to prepare writable Arduino bootstrap workspace: {exc}"
            ) from exc
        return destination

    def generate(
        self,
        ssid: str,
        wifi_password: str,
        ota_password: str,
        output: Path | None = None,
    ) -> Path:
        if not ssid.strip():
            raise ValueError("Wi-Fi SSID is required.")
        if not ota_password:
            raise ValueError("OTA password is required for first-flash bootstrap.")

        output = self._ensure_external_path(
            output or (self.bootstrap_root / "robot_bootstrap.json"),
            label="Bootstrap configuration",
        )
        try:
            workspace = self._prepare_arduino_workspace(refresh=True)
            header = workspace / "include" / "generated" / "generated_bootstrap_config.h"
            output.parent.mkdir(parents=True, exist_ok=True)
            config = bootstrap_config.make_config(ssid, wifi_password, ota_password)
            output.write_text(
                __import__("json").dumps(config, indent=2) + "\n", encoding="utf-8"
            )
            bootstrap_config.write_arduino_header(config, header)
        except (OSError, ValueError, RuntimeError) as exc:
            raise RuntimeError(str(exc) or "Unable to generate bootstrap config.") from exc
        return output

    def arduino_sketch_path(self) -> Path:
        """Return the writable Arduino sketch, materializing it when necessary."""
        return self._prepare_arduino_workspace(refresh=False)

    def arduino_header_path(self) -> Path:
        """Return the generated header path under external state."""
        self._prepare_arduino_workspace(refresh=False)
        return self.arduino_bootstrap_header

    def open_arduino_sketch(self) -> tuple[bool, str]:
        """Open the writable external sketch with the default Arduino application."""
        import shutil as _shutil
        import subprocess

        try:
            sketch = self._prepare_arduino_workspace(refresh=False)
        except RuntimeError as exc:
            return False, str(exc)
        main_ino = sketch / "main.ino"
        if not main_ino.is_file():
            return False, f"Arduino sketch not found: {main_ino}"

        candidates: list[str] = []
        configured = os.getenv("ARDUINO_IDE", "").strip()
        if configured:
            candidates.append(configured)
        for command in ("arduino-ide", "arduino"):
            found = _shutil.which(command)
            if found:
                candidates.append(found)

        if os.name == "nt":
            local = os.getenv("LOCALAPPDATA", "")
            program_files = os.getenv("PROGRAMFILES", "")
            program_files_x86 = os.getenv("PROGRAMFILES(X86)", "")
            candidates.extend(
                [
                    str(Path(local) / "Programs" / "Arduino IDE" / "Arduino IDE.exe")
                    if local
                    else "",
                    str(Path(program_files) / "Arduino IDE" / "Arduino IDE.exe")
                    if program_files
                    else "",
                    str(Path(program_files_x86) / "Arduino IDE" / "Arduino IDE.exe")
                    if program_files_x86
                    else "",
                    str(Path(program_files) / "Arduino IDE" / "arduino.exe")
                    if program_files
                    else "",
                    str(Path(program_files_x86) / "Arduino IDE" / "arduino.exe")
                    if program_files_x86
                    else "",
                ]
            )

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
            elif _shutil.which("open"):
                subprocess.Popen(["open", str(main_ino)])
            elif _shutil.which("xdg-open"):
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
