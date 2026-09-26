from __future__ import annotations

import sys
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
ROBOSTUDIO = ROOT / "robostudio"
for path in (str(ROOT), str(ROBOSTUDIO)):
    if path not in sys.path:
        sys.path.insert(0, path)

from services.robot_discovery_service import (  # noqa: E402
    DISCOVERY_PORT,
    DISCOVERY_REQUEST,
    RobotDiscoveryClient,
    _is_usable_local_ipv4,
)


class _FakeSocket:
    def __init__(self) -> None:
        self.bound = None
        self.sent = []
        self.blocking = None
        self.closed = False

    def setsockopt(self, *args) -> None:
        pass

    def bind(self, address) -> None:
        self.bound = address

    def setblocking(self, value: bool) -> None:
        self.blocking = value

    def sendto(self, payload: bytes, address) -> None:
        self.sent.append((payload, address))

    def close(self) -> None:
        self.closed = True


class RobotDiscoveryResilienceTests(unittest.TestCase):
    def test_usable_ipv4_filter_rejects_non_lan_sources(self) -> None:
        self.assertTrue(_is_usable_local_ipv4("192.168.0.20"))
        self.assertTrue(_is_usable_local_ipv4("10.20.30.40"))
        self.assertFalse(_is_usable_local_ipv4("127.0.0.1"))
        self.assertFalse(_is_usable_local_ipv4("0.0.0.0"))
        self.assertFalse(_is_usable_local_ipv4("not-an-ip"))

    def test_discovery_broadcasts_from_every_local_adapter_plus_fallback(self) -> None:
        created: list[_FakeSocket] = []

        def fake_socket(*args, **kwargs):
            sock = _FakeSocket()
            created.append(sock)
            return sock

        with patch("services.robot_discovery_service.socket.socket", side_effect=fake_socket), \
             patch("services.robot_discovery_service.select.select", return_value=([], [], [])):
            robots = RobotDiscoveryClient(timeout=0.01).discover(
                ["192.168.0.20", "10.0.0.5", "127.0.0.1"]
            )

        self.assertEqual(robots, [])
        self.assertEqual(len(created), 3)
        self.assertEqual(
            [sock.bound for sock in created],
            [("192.168.0.20", 0), ("10.0.0.5", 0), ("", 0)],
        )
        for sock in created:
            self.assertEqual(
                sock.sent,
                [(DISCOVERY_REQUEST, ("255.255.255.255", DISCOVERY_PORT))],
            )
            self.assertFalse(sock.blocking)
            self.assertTrue(sock.closed)


if __name__ == "__main__":
    unittest.main()
