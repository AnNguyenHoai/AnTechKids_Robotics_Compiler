"""RoboStudio build service using the application-owned compiler contract."""
from __future__ import annotations

import json
import os
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Tuple

try:  # package import used by tests/integration
    from ..domain.hardware_config_service import HardwareConfigService
    from ..domain.hardware_requirement_validator import HardwareRequirementValidator
except ImportError:  # desktop entry point exposes robostudio/ as import root
    from domain.hardware_config_service import HardwareConfigService
    from domain.hardware_requirement_validator import HardwareRequirementValidator

from tools.runtime_paths import application_root, is_frozen, python_command


@dataclass
class BuildResult:
    success: bool
    output: str
    error: Optional[str] = None


class BuildService:
    def __init__(self, config_path: Optional[Path] = None):
        self._explicit_config_path = Path(config_path) if config_path is not None else None
        if config_path is None:
            packaged = application_root() / "config" / "config.json"
            source = Path(__file__).parent.parent / "config" / "config.json"
            config_path = packaged if packaged.is_file() else source
        self.config = self._load_config(Path(config_path))

    def _load_config(self, config_path: Path) -> dict:
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {"compiler_command": "robot"}

    def validate_hardware(self, code: str) -> Optional[str]:
        """Validate against the same user hardware state edited by RoboStudio.

        Explicit config paths retain the historical sibling ``hardware.json``
        behavior for tests/integration. Normal application usage delegates to
        ``HardwareConfigService`` so external user state wins over immutable
        packaged defaults.
        """
        if self._explicit_config_path is not None:
            config_service = HardwareConfigService(
                self._explicit_config_path.parent / "hardware.json"
            )
        else:
            config_service = HardwareConfigService()
        config = config_service.load()
        result = HardwareRequirementValidator.validate(code, config)
        return None if result.valid else result.format_errors()

    def _compiler_bridge(self) -> Path:
        packaged = application_root() / "compiler" / "robostudio_bridge.py"
        if packaged.is_file():
            return packaged
        if is_frozen():
            raise FileNotFoundError(
                f"Application-owned compiler contract is missing: {packaged}"
            )
        repository = (
            Path(__file__).resolve().parents[2]
            / "robot-compiler"
            / "compiler"
            / "robostudio_bridge.py"
        )
        if repository.is_file():
            return repository
        raise FileNotFoundError(f"Compiler contract not found: {repository}")

    def _get_command_with_env(self) -> Tuple[List[str], Dict[str, str]]:
        """Return the deterministic application-owned compiler command.

        ``compiler_command`` is retained in config for backward compatibility,
        but production never resolves it through PATH or the repository CLI.
        The stable bridge is the only compiler entry point used by RoboStudio.
        """
        bridge = self._compiler_bridge()
        return python_command(str(bridge)), {}

    def get_command(self, code: str) -> Tuple[List[str], Dict[str, str], str]:
        hardware_error = self.validate_hardware(code)
        if hardware_error:
            raise ValueError(hardware_error)

        source = tempfile.NamedTemporaryFile(
            mode="w", suffix=".py", delete=False, encoding="utf-8"
        )
        source.write(code)
        source.close()
        temp_path = source.name

        output_path = Path(temp_path).with_suffix(".h")
        report_path = output_path.with_suffix(".json")
        request_path = output_path.with_suffix(".request.json")
        request_path.write_text(
            json.dumps(
                {
                    "source": temp_path,
                    "output": str(output_path),
                    "report": str(report_path),
                    "source_kind": "robosim-python",
                }
            ),
            encoding="utf-8",
        )
        cmd_parts, env_override = self._get_command_with_env()
        cmd = cmd_parts + ["--request", str(request_path)]
        env = os.environ.copy()
        env["PYTHONIOENCODING"] = "utf-8"
        env.update(env_override)
        return cmd, env, temp_path

    def build(self, code: str) -> BuildResult:
        hardware_error = self.validate_hardware(code)
        if hardware_error:
            return BuildResult(False, hardware_error, hardware_error)

        # Compiler scratch state belongs to the OS/user temp area, never the
        # immutable application directory. The child CWD follows that external
        # workspace so relative compiler writes cannot mutate the release.
        with tempfile.TemporaryDirectory(prefix="robostudio-build-") as temp_dir:
            workspace = Path(temp_dir)
            source = workspace / "program.py"
            output = workspace / "program.h"
            report = workspace / "compile_report.json"
            request = workspace / "request.json"
            source.write_text(code, encoding="utf-8")
            request.write_text(
                json.dumps(
                    {
                        "source": str(source),
                        "output": str(output),
                        "report": str(report),
                        "source_kind": "robosim-python",
                    }
                ),
                encoding="utf-8",
            )

            try:
                cmd_parts, env_override = self._get_command_with_env()
                env = os.environ.copy()
                env["PYTHONIOENCODING"] = "utf-8"
                env.update(env_override)
                proc = subprocess.run(
                    cmd_parts + ["--request", str(request)],
                    capture_output=True,
                    text=True,
                    encoding="utf-8",
                    errors="replace",
                    env=env,
                    cwd=str(workspace),
                )
                output_text = proc.stdout
                if proc.stderr:
                    output_text += "\n" + proc.stderr
                if proc.returncode == 0 and output.exists():
                    output_text += f"\n[OK] Header: {output}\n"
                return BuildResult(
                    proc.returncode == 0,
                    output_text,
                    proc.stderr if proc.returncode != 0 else None,
                )
            except (FileNotFoundError, OSError) as exc:
                return BuildResult(False, f"Compiler runtime error: {exc}", str(exc))
            except Exception as exc:
                return BuildResult(False, f"Unexpected error: {exc}", str(exc))
