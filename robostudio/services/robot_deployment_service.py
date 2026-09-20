"""RoboStudio robot deployment orchestration.

The UI delegates the canonical compile/build/USB/OTA pipeline to
``tools/deploy_robot.py``. First-flash bootstrap is deliberately a separate
operation because it provisions a new robot before normal LAN discovery.

Deployment subprocesses are streamed through Qt-safe callbacks so the UI can
show live PlatformIO output instead of appearing frozen during a build/upload.

Only one destructive/building robot deployment may run inside a RoboStudio
process at a time. The UI has separate workers for first-flash and OTA, so this
service-level guard is the final safety boundary if both controls are triggered
close together.
"""
from __future__ import annotations

import json
import os
import tempfile
import threading
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Iterable

from services.robot_discovery_service import RobotDiscoveryClient, RobotInfo
from tools import runtime_paths
from tools.deployment_runtime import DeploymentRuntimeError, python_command, run_process

DeploymentOutputCallback = Callable[[str], None]

_DEPLOYMENT_OPERATION_LOCK = threading.Lock()
_DEPLOYMENT_BUSY_MESSAGE = (
    "Another robot deployment is already in progress. Wait for the current "
    "First-Flash or OTA operation to finish before starting another deployment."
)


def deployment_operation_busy() -> bool:
    """Return whether this RoboStudio process already owns the deployment lane."""
    return _DEPLOYMENT_OPERATION_LOCK.locked()


def windows_serial_port_busy_error(port: str) -> str | None:
    """Return an actionable diagnostic when Windows cannot open ``port`` exclusively.

    QSerialPort and PlatformIO/esptool both require exclusive ownership of a
    Windows COM device. A Serial Console left connected to the same robot can
    therefore make a first-flash fail only after an expensive firmware build.
    Probe the handle before spawning the deployment child instead. This helper
    intentionally does not manipulate Qt objects from the worker thread.
    """
    if os.name != "nt":
        return None

    value = (port or "").strip()
    if not value:
        return None

    try:
        import ctypes
        from ctypes import wintypes

        kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
        create_file = kernel32.CreateFileW
        create_file.argtypes = (
            wintypes.LPCWSTR,
            wintypes.DWORD,
            wintypes.DWORD,
            wintypes.LPVOID,
            wintypes.DWORD,
            wintypes.DWORD,
            wintypes.HANDLE,
        )
        create_file.restype = wintypes.HANDLE
        close_handle = kernel32.CloseHandle
        close_handle.argtypes = (wintypes.HANDLE,)
        close_handle.restype = wintypes.BOOL

        generic_read = 0x80000000
        generic_write = 0x40000000
        open_existing = 3
        device_path = value if value.startswith("\\\\.\\") else f"\\\\.\\{value}"
        handle = create_file(
            device_path,
            generic_read | generic_write,
            0,  # no sharing: match PlatformIO/QSerialPort ownership semantics
            None,
            open_existing,
            0,
            None,
        )
        invalid_handle = wintypes.HANDLE(-1).value
        if handle == invalid_handle:
            error_code = ctypes.get_last_error()
            return (
                f"Serial port {value} is busy or unavailable (Windows error {error_code}). "
                "If the RoboStudio USB Serial Console is connected to this port, click Disconnect first; "
                "also close any other serial monitor using the robot, then retry First-Flash."
            )
        close_handle(handle)
        return None
    except (AttributeError, OSError, ValueError) as exc:
        return f"Unable to verify exclusive access to serial port {value}: {exc}"


@dataclass(frozen=True)
class DeploymentResult:
    success: bool
    output: str
    error: str | None = None
    verified_robot: RobotInfo | None = None


def select_unique_new_robot(
    known_device_ids: set[str] | None, robots: Iterable[RobotInfo]
) -> RobotInfo | None:
    """Return one newly appeared robot only when the pre-flash baseline is known.

    During first-flash a classroom can already contain many online robots. The
    USB upload itself has no LAN ``device_id`` mapping, so RoboStudio may only
    auto-bind the result when a successful pre-flash discovery established the
    existing identities and the post-flash scan contains exactly one new one.
    A missing baseline is ambiguous and must never be interpreted as an empty
    classroom.
    """
    if known_device_ids is None:
        return None
    new_by_id = {
        robot.device_id: robot
        for robot in robots
        if robot.device_id not in known_device_ids
    }
    if len(new_by_id) != 1:
        return None
    return next(iter(new_by_id.values()))


class RobotDeploymentService:
    def __init__(self, root: Path | None = None):
        # In a frozen/PyInstaller build ``__file__`` can point at the temporary
        # bundle extraction tree. Production deployment assets live beside the
        # installed/extracted RoboStudio executable, so use the canonical
        # application root unless a test/integration caller explicitly supplies
        # a root.
        self.root = (
            Path(root).expanduser().resolve()
            if root is not None
            else runtime_paths.application_root()
        )
        self.discovery = RobotDiscoveryClient()

    def _deployment_cwd(self) -> Path:
        """Return external writable process state, never the immutable release."""
        packaged = (
            runtime_paths.is_frozen()
            or os.environ.get(runtime_paths.RUNTIME_MODE_ENV) == "packaged"
            or os.environ.get(runtime_paths.DEPENDENCY_MODE_ENV) == "artifact-closed"
        )
        cwd = runtime_paths.prepare_user_data_root(
            application_root_override=self.root,
            enforce_external=packaged,
        ) / "deployment"
        cwd.mkdir(parents=True, exist_ok=True)
        return cwd

    def _runtime_tool(self, name: str) -> Path:
        path = self.root / "tools" / name
        if not path.is_file():
            raise DeploymentRuntimeError(
                f"Packaged RoboStudio deployment tool is missing: {path}"
            )
        return path

    def generate_bootstrap_config(self, ssid: str, wifi_password: str,
                                  ota_password: str, output: Path) -> Path:
        if not ssid.strip():
            raise ValueError("Wi-Fi SSID is required.")
        if not ota_password:
            raise ValueError("OTA password is required for first-flash bootstrap.")
        try:
            command = python_command(
                str(self._runtime_tool("bootstrap_config.py")),
                "generate",
                "--ssid", ssid.strip(),
                "--password", wifi_password,
                "--ota-password", ota_password,
                "--output", str(output),
            )
            completed = run_process(command, cwd=self._deployment_cwd(), timeout=300.0)
        except DeploymentRuntimeError as exc:
            raise RuntimeError(str(exc)) from exc
        if completed.returncode != 0:
            raise RuntimeError(
                completed.output.strip() or "Unable to generate bootstrap config."
            )
        return output

    def flash_first_robot(self, config_path: Path, usb_port: str = "",
                          on_output: DeploymentOutputCallback | None = None) -> DeploymentResult:
        """Build and USB-flash a first-boot firmware containing bootstrap data."""
        if not _DEPLOYMENT_OPERATION_LOCK.acquire(blocking=False):
            return DeploymentResult(False, "", _DEPLOYMENT_BUSY_MESSAGE)
        try:
            return self._flash_first_robot_locked(config_path, usb_port, on_output)
        finally:
            _DEPLOYMENT_OPERATION_LOCK.release()

    def _flash_first_robot_locked(
        self,
        config_path: Path,
        usb_port: str,
        on_output: DeploymentOutputCallback | None,
    ) -> DeploymentResult:
        config_path = config_path.resolve()
        if not config_path.is_file():
            return DeploymentResult(False, "", f"Bootstrap config not found: {config_path}")
        usb_port = usb_port.strip()
        if not usb_port:
            return DeploymentResult(
                False,
                "",
                "Select a detected USB/COM port before first-flash. RoboStudio never guesses a port.",
            )

        serial_error = windows_serial_port_busy_error(usb_port)
        if serial_error:
            return DeploymentResult(False, "", serial_error)

        try:
            config = json.loads(config_path.read_text(encoding="utf-8"))
            if config.get("type") != "antechkids.robot.bootstrap":
                return DeploymentResult(False, "", "Invalid bootstrap config type.")
            if config.get("schema_version") != 1:
                return DeploymentResult(False, "", "Unsupported bootstrap config schema.")
        except (OSError, json.JSONDecodeError) as exc:
            return DeploymentResult(False, "", f"Invalid bootstrap config: {exc}")

        # H30: snapshot identities already visible on the LAN. ``None`` means
        # discovery failed, which is different from a successful empty scan.
        # Without a trustworthy baseline automatic identity binding is disabled.
        known_device_ids: set[str] | None = None
        try:
            known_device_ids = {robot.device_id for robot in self.discovery.discover()}
        except Exception:
            # The USB flash can still succeed. Post-flash discovery may be used
            # for visibility, but identity binding requires manual selection.
            pass

        try:
            command = python_command(
                str(self._runtime_tool("deploy_robot.py")),
                "--mode", "bootstrap",
                "--bootstrap-config", str(config_path),
                "--port", usb_port,
            )
            completed = run_process(
                command,
                cwd=self._deployment_cwd(),
                env=os.environ.copy(),
                timeout=360.0,
                on_output=on_output,
            )
        except DeploymentRuntimeError as exc:
            return DeploymentResult(False, "", str(exc))

        output = completed.output
        if completed.returncode != 0:
            return DeploymentResult(False, output, "First-flash failed.")

        # The robot has just rebooted and may need a few seconds to associate.
        # Discovery is product-level verification; do not claim one arbitrary
        # robot merely because PlatformIO accepted the USB upload.
        deadline = time.monotonic() + 20.0
        while time.monotonic() < deadline:
            try:
                robots = self.discovery.discover()
                verified = select_unique_new_robot(known_device_ids, robots)
                if verified is not None:
                    return DeploymentResult(True, output, verified_robot=verified)
            except Exception:
                pass
            time.sleep(1.0)

        return DeploymentResult(
            True,
            output,
            "First-flash upload completed; RoboStudio could not uniquely identify "
            "the newly flashed robot on the LAN. Click Discover and select it by identity.",
        )

    def deploy_ota(self, code: str, robot: RobotInfo, wifi_ssid: str,
                   wifi_password: str, ota_password: str,
                   on_output: DeploymentOutputCallback | None = None) -> DeploymentResult:
        """Compile, build, OTA-upload and verify the selected robot."""
        if not _DEPLOYMENT_OPERATION_LOCK.acquire(blocking=False):
            return DeploymentResult(False, "", _DEPLOYMENT_BUSY_MESSAGE)
        try:
            return self._deploy_ota_locked(
                code, robot, wifi_ssid, wifi_password, ota_password, on_output
            )
        finally:
            _DEPLOYMENT_OPERATION_LOCK.release()

    def _deploy_ota_locked(
        self,
        code: str,
        robot: RobotInfo,
        wifi_ssid: str,
        wifi_password: str,
        ota_password: str,
        on_output: DeploymentOutputCallback | None,
    ) -> DeploymentResult:
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

        # Student source is temporary user/process state. It is deliberately not
        # created under the immutable application root.
        fd, temp_name = tempfile.mkstemp(prefix="robostudio_", suffix=".py", text=True)
        os.close(fd)
        source = Path(temp_name)
        try:
            source.write_text(code, encoding="utf-8")
            env = os.environ.copy()
            env["ROBOT_WIFI_SSID"] = wifi_ssid.strip()
            env["ROBOT_WIFI_PASSWORD"] = wifi_password
            env["ROBOT_OTA_PASSWORD"] = ota_password

            command = python_command(
                str(self._runtime_tool("deploy_robot.py")),
                "--input", str(source),
                "--mode", "ota",
                "--robot", robot.ip,
                "--ssid", wifi_ssid.strip(),
            )
            try:
                completed = run_process(
                    command,
                    cwd=self._deployment_cwd(),
                    env=env,
                    timeout=360.0,
                    on_output=on_output,
                )
            except DeploymentRuntimeError as exc:
                return DeploymentResult(False, "", str(exc))

            output = completed.output
            if completed.returncode != 0:
                return DeploymentResult(False, output, "OTA deployment failed.")

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
        except (OSError, DeploymentRuntimeError) as exc:
            return DeploymentResult(False, "", f"Unable to start deployment: {exc}")
        finally:
            try:
                source.unlink()
            except OSError:
                pass
