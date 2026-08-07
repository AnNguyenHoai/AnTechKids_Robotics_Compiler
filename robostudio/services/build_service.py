"""
BuildService – compiles RoboSim code via robot CLI
Provides command generation and sync build (for legacy).
"""

import subprocess
import tempfile
import os
import shutil
import sys
from pathlib import Path
from dataclasses import dataclass
from typing import Optional, List, Tuple, Dict
import json


@dataclass
class BuildResult:
    success: bool
    output: str
    error: Optional[str] = None


class BuildService:
    def __init__(self, config_path: Optional[Path] = None):
        if config_path is None:
            config_path = Path(__file__).parent.parent / "config" / "config.json"
        self.config = self._load_config(config_path)

    def _load_config(self, config_path: Path) -> dict:
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {
                "compiler_command": "robot",
                "firmware_project": ""
            }

    def get_command(self, code: str) -> Tuple[List[str], Dict[str, str], str]:
        """
        Generate the command list, environment, and temporary file path.
        Returns (cmd_list, env_dict, temp_file_path).
        The caller is responsible for deleting the temp file.
        """
        # Write code to temp file
        temp_file = tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False, encoding="utf-8")
        temp_file.write(code)
        temp_path = temp_file.name
        temp_file.close()

        cmd_parts, env_override = self._get_command_with_env()
        cmd = cmd_parts + ["build", "-f", temp_path, "--copy"]

        env = os.environ.copy()
        env["PYTHONIOENCODING"] = "utf-8"
        if env_override:
            env.update(env_override)

        return cmd, env, temp_path

    def build(self, code: str) -> BuildResult:
        """
        Sync build (blocking) – kept for backward compatibility.
        """
        # Use the same logic as before
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False, encoding="utf-8") as f:
            f.write(code)
            temp_path = f.name

        try:
            cmd_parts, env_override = self._get_command_with_env()
            cmd = cmd_parts + ["build", "-f", temp_path, "--copy"]
            env = os.environ.copy()
            env["PYTHONIOENCODING"] = "utf-8"
            if env_override:
                env.update(env_override)

            proc = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                env=env,
                cwd=os.getcwd()
            )

            output = proc.stdout
            if proc.stderr:
                output += "\n" + proc.stderr

            return BuildResult(
                success=(proc.returncode == 0),
                output=output,
                error=proc.stderr if proc.returncode != 0 else None
            )
        except FileNotFoundError:
            return BuildResult(
                success=False,
                output="Error: 'robot' command not found.\n"
                       "Please ensure Robot CLI is installed and in PATH, "
                       "or set 'compiler_command' in config/config.json.\n"
                       "To install: cd robot-cli && pip install -e ."
            )
        except Exception as e:
            return BuildResult(
                success=False,
                output=f"Unexpected error: {str(e)}"
            )
        finally:
            try:
                os.unlink(temp_path)
            except:
                pass

    def _get_command_with_env(self) -> Tuple[List[str], Dict[str, str]]:
        """Return (command_parts, env_override) for the robot CLI."""
        cmd = self.config.get("compiler_command", "robot")
        env_override = {}

        if isinstance(cmd, list):
            return cmd, env_override

        if os.path.isabs(cmd):
            return [cmd], env_override

        if shutil.which(cmd):
            return [cmd], env_override

        # Try to locate robot-cli inside the repository
        repo_root = Path(__file__).parent.parent.parent
        cli_path = repo_root / "robot-cli" / "robot" / "cli.py"
        if cli_path.exists():
            env_override["PYTHONPATH"] = str(repo_root) + os.pathsep + env_override.get("PYTHONPATH", "")
            return [sys.executable, "-m", "robot.cli"], env_override

        # Fallback
        return [cmd], env_override