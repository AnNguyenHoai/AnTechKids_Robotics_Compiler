"""RoboStudio-side robot discovery client.

Consumes the H27-A discovery/identity protocol and returns validated
RobotInfo records to the UI. The module has no Qt dependency so it is also
usable from tests and future non-GUI clients.
"""
from __future__ import annotations

import ipaddress
import json
import select
import socket
import time
from dataclasses import dataclass, field
from typing import Any, Iterable

from domain.compatibility import (
    LEGACY_UNVERSIONED_FIRMWARE_GENERATION,
    normalize_firmware_generation,
)

DISCOVERY_PORT = 4210
DISCOVERY_REQUEST = b"ANTECHKIDS_ROBOT_DISCOVER_V1"
DISCOVERY_RESPONSE_PREFIX = "ANTECHKIDS_ROBOT_INFO_V1"
DISCOVERY_SCHEMA = 1
DISCOVERY_TIMEOUT_SECONDS = 1.5


class RobotDiscoveryError(RuntimeError):
    """Raised when discovery cannot be performed."""


@dataclass(frozen=True)
class RobotInfo:
    device_id: str
    name: str
    hostname: str
    ip: str
    target: str
    firmware: str
    robot_ready: bool
    network_ready: bool
    ready: bool
    ota: bool
    capabilities: dict[str, bool] = field(default_factory=dict)
    compatibility_generation: int = LEGACY_UNVERSIONED_FIRMWARE_GENERATION
    schema_version: int = DISCOVERY_SCHEMA
    protocol: str = "antechkids.robot.v1"

    @property
    def display_label(self) -> str:
        return self.name or self.hostname or self.device_id


def _required_string(data: dict[str, Any], key: str) -> str:
    value = data.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"missing/invalid {key}")
    return value.strip()


def serialize_robot_info(info: RobotInfo) -> dict[str, Any]:
    """Serialize one validated identity snapshot using the canonical H27/H35 schema."""
    return {
        "protocol": info.protocol,
        "schema_version": info.schema_version,
        "compatibility_generation": info.compatibility_generation,
        "device_id": info.device_id,
        "name": info.name,
        "hostname": info.hostname,
        "ip": info.ip,
        "target": info.target,
        "firmware": info.firmware,
        "robot_ready": info.robot_ready,
        "network_ready": info.network_ready,
        "ready": info.ready,
        "ota": info.ota,
        "capabilities": dict(info.capabilities),
    }


def validate_robot_info(data: Any, source_ip: str | None = None) -> RobotInfo:
    """Validate the canonical H27-A identity payload and H35 generation.

    Pre-H35 firmware did not advertise ``compatibility_generation``. H35 maps
    that single historical absence to generation 0 so it can be upgraded. Any
    malformed explicit generation still fails closed.
    """
    if not isinstance(data, dict):
        raise ValueError("identity payload must be an object")
    if data.get("protocol") != "antechkids.robot.v1":
        raise ValueError("unsupported robot protocol")
    if data.get("schema_version") != DISCOVERY_SCHEMA:
        raise ValueError("unsupported robot identity schema")

    device_id = _required_string(data, "device_id")
    name = _required_string(data, "name")
    hostname = _required_string(data, "hostname")
    target = _required_string(data, "target")
    firmware = _required_string(data, "firmware")
    compatibility_generation = normalize_firmware_generation(
        data.get("compatibility_generation")
    )

    ip = data.get("ip")
    if not isinstance(ip, str) or not ip.strip():
        ip = source_ip or ""
    if not ip:
        raise ValueError("missing/invalid ip")

    for key in ("robot_ready", "network_ready", "ready", "ota"):
        if not isinstance(data.get(key), bool):
            raise ValueError(f"missing/invalid {key}")

    capabilities = data.get("capabilities")
    if not isinstance(capabilities, dict) or any(
        not isinstance(key, str) or not isinstance(value, bool)
        for key, value in capabilities.items()
    ):
        raise ValueError("missing/invalid capabilities")

    return RobotInfo(
        device_id=device_id,
        name=name,
        hostname=hostname,
        ip=ip.strip(),
        target=target,
        firmware=firmware,
        robot_ready=data["robot_ready"],
        network_ready=data["network_ready"],
        ready=data["ready"],
        ota=data["ota"],
        capabilities=dict(capabilities),
        compatibility_generation=compatibility_generation,
        schema_version=data["schema_version"],
        protocol=data["protocol"],
    )


def _is_usable_local_ipv4(value: str) -> bool:
    """Return whether ``value`` can be used as a LAN discovery source address."""
    try:
        address = ipaddress.ip_address(value)
    except ValueError:
        return False
    return (
        address.version == 4
        and not address.is_loopback
        and not address.is_unspecified
        and not address.is_multicast
    )


def local_ipv4_addresses() -> tuple[str, ...]:
    """Best-effort IPv4 interface discovery without platform-specific packages.

    Windows can have Wi-Fi, Ethernet, VPN and Hyper-V adapters simultaneously.
    A single unbound limited broadcast is allowed to leave through only one
    route, so RoboStudio explicitly opens a discovery socket for every usable
    source address it can identify. The route-probe socket does not transmit
    application data; UDP connect only asks the OS which source address it
    would use.
    """
    addresses: set[str] = set()
    for host in (socket.gethostname(), socket.getfqdn()):
        try:
            records = socket.getaddrinfo(host, None, socket.AF_INET, socket.SOCK_DGRAM)
        except OSError:
            continue
        for record in records:
            value = record[4][0]
            if _is_usable_local_ipv4(value):
                addresses.add(value)

    probe = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        probe.connect(("192.0.2.1", 9))
        value = probe.getsockname()[0]
        if _is_usable_local_ipv4(value):
            addresses.add(value)
    except OSError:
        pass
    finally:
        probe.close()

    return tuple(sorted(addresses))


def _decode_discovery_packet(packet: bytes, source_ip: str) -> RobotInfo | None:
    try:
        text = packet.decode("utf-8").strip()
        prefix, payload = text.split("\n", 1)
        if prefix != DISCOVERY_RESPONSE_PREFIX:
            return None
        return validate_robot_info(json.loads(payload), source_ip)
    except (UnicodeDecodeError, ValueError, json.JSONDecodeError):
        return None


class RobotDiscoveryClient:
    """Discover robots on the local LAN using the H27-A UDP protocol."""

    def __init__(self, port: int = DISCOVERY_PORT, timeout: float = DISCOVERY_TIMEOUT_SECONDS):
        self.port = port
        self.timeout = timeout

    def _open_probe_socket(self, local_ip: str | None) -> socket.socket:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            if local_ip:
                sock.bind((local_ip, 0))
            else:
                sock.bind(("", 0))
            sock.setblocking(False)
            sock.sendto(DISCOVERY_REQUEST, ("255.255.255.255", self.port))
            return sock
        except Exception:
            sock.close()
            raise

    def discover(self, local_addresses: Iterable[str] | None = None) -> list[RobotInfo]:
        """Broadcast on every usable IPv4 source and collect unique valid robots.

        ``local_addresses`` is primarily a deterministic test seam. Normal
        callers leave it unset so addresses are discovered from the host. An
        additional unbound socket remains as a compatibility fallback for
        hosts where interface enumeration is incomplete.
        """
        robots: dict[str, RobotInfo] = {}
        addresses = tuple(local_addresses) if local_addresses is not None else local_ipv4_addresses()
        bind_addresses: list[str | None] = []
        for value in addresses:
            if _is_usable_local_ipv4(value) and value not in bind_addresses:
                bind_addresses.append(value)
        bind_addresses.append(None)

        sockets: list[socket.socket] = []
        errors: list[str] = []
        try:
            for local_ip in bind_addresses:
                try:
                    sockets.append(self._open_probe_socket(local_ip))
                except OSError as exc:
                    label = local_ip or "default route"
                    errors.append(f"{label}: {exc}")

            if not sockets:
                detail = "; ".join(errors) or "no usable IPv4 socket"
                raise RobotDiscoveryError(f"Robot discovery could not open a UDP probe: {detail}")

            deadline = time.monotonic() + self.timeout
            while sockets:
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    break
                try:
                    readable, _, _ = select.select(sockets, [], [], remaining)
                except (OSError, ValueError) as exc:
                    raise RobotDiscoveryError(f"Robot discovery receive failed: {exc}") from exc
                if not readable:
                    break
                for sock in readable:
                    while True:
                        try:
                            packet, address = sock.recvfrom(4096)
                        except BlockingIOError:
                            break
                        except OSError:
                            break
                        info = _decode_discovery_packet(packet, address[0])
                        if info is not None:
                            robots[info.device_id] = info
        finally:
            for sock in sockets:
                sock.close()

        return sorted(robots.values(), key=lambda robot: robot.display_label.lower())

    def get_info(self, host: str, timeout: float = 2.0) -> RobotInfo:
        """Fetch and validate identity from a specific robot."""
        import urllib.request
        url = f"http://{host}/api/v1/info"
        try:
            with urllib.request.urlopen(url, timeout=timeout) as response:
                data = json.loads(response.read().decode("utf-8"))
        except (OSError, ValueError, json.JSONDecodeError) as exc:
            raise RobotDiscoveryError(f"Unable to read robot info from {host}: {exc}") from exc
        return validate_robot_info(data, host)
