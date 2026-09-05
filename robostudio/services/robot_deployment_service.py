"""RoboStudio robot deployment orchestration.

The UI delegates the canonical compile/build/OTA pipeline to
``tools/deploy_robot.py`` instead of duplicating PlatformIO logic.
"""
from __future__ import annotations

import os
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path

from services.robot_discovery_service import RobotDiscoveryClient, RobotInfo

ROOT = Path(__file__).resolve().parents[2]


@dataclass(frozen=True)
class DeploymentResult:
    success: bool
    output: str
    error: str | None = None
    verified_robot: RobotInfo | None = None


class RobotDeploymentService:
    def __init__(self, root: Path | None = None):
        self.root = root or ROOT
        self.discovery = RobotDiscoveryClient()

    def deploy_ota(self, code: str, robot: RobotInfo, wifi_ssid: str,
                   wifi_password: str, ota_password: str) -> DeploymentResult:
        """Compile, build, OTA-upload and verify the selected robot."""
        if not robot.ota:
            return DeploymentResult(False, "", "Selected robot does not advertise OTA support.")
        if not robot.network_ready:
            return DeploymentResult(False, "", "Selected robot is not network-ready.")
        if not wifi_ssid.strip():
            return DeploymentResult(False, "", "Wi-Fi SSID is required for OTA deployment.")
        if not ota_password:
            return DeploymentResult(False, "", "OTA password is required for OTA deployment.")
        if not code.strip():
            return DeploymentResult(False, "", "No student program is available to deploy.")

        fd, temp_name = tempfile.mkstemp(prefix="robostudio_", suffix=".py", text=True)
        os.close(fd)
        source = Path(temp_name)
        try:
            source.write_text(code, encoding="utf-8")
            env = os.environ.copy()
            env["ROBOT_WIFI_SSID"] = wifi_ssid.strip()
            env["ROBOT_WIFI_PASSWORD"] = wifi_password
            env["ROBOT_OTA_PASSWORD"] = ota_password

            command = [
                sys.executable,
                str(self.root / "tools" / "deploy_robot.py"),
                "--input", str(source),
                "--mode", "ota",
                "--robot", robot.ip,
                "--ssid", wifi_ssid.strip(),
            ]
            completed = subprocess.run(
                command, cwd=self.root, env=env, capture_output=True,
                text=True, encoding="utf-8", errors="replace",
            )
            output = (completed.stdout or "") + (("\n" + completed.stderr) if completed.stderr else "")
            if completed.returncode != 0:
                return DeploymentResult(False, output, "OTA deployment failed.")

            # Verify identity after reboot. Prefer the discovered hostname, then
            # fall back to the last known IP if mDNS is unavailable on the host.
            verified = None
            verification_error = None
            for host in (robot.hostname, robot.ip):
                try:
                    verified = self.discovery.get_info(host)
                    break
                except Exception as exc:
                    verification_error = exc
            if verified is None:
                return DeploymentResult(False, output,
                    f"Deployment verification failed: {verification_error}")
            if verified.device_id != robot.device_id:
                return DeploymentResult(False, output,
                    f"Deployment verification failed: expected {robot.device_id}, found {verified.device_id}.",
                    verified)
            if not verified.ready:
                return DeploymentResult(False, output, "Robot rebooted but is not ready.", verified)
            return DeploymentResult(True, output, verified_robot=verified)
        except OSError as exc:
            return DeploymentResult(False, "", f"Unable to start deployment: {exc}")
        finally:
            try:
                source.unlink()
            except OSError:
                pass
