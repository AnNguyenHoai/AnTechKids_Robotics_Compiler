#!/usr/bin/env python3
"""Validate evidence emitted by the production offline first-flash gate.

The expensive operational check is executed by BUILD_PRODUCTION_ZIP.cmd itself.
This CI test makes the evidence a named release gate without recompiling the
firmware a second time.
"""
from __future__ import annotations

import json
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
REPORT = ROOT / ".build" / "production" / "offline-first-flash-report.json"
LOG = ROOT / ".build" / "production" / "offline-first-flash.log"


def check(label: str, condition: bool) -> None:
    if not condition:
        raise AssertionError(label)
    print(f"PASS: {label}")


def main() -> int:
    check("offline first-flash report exists", REPORT.is_file())
    report = json.loads(REPORT.read_text(encoding="utf-8"))
    check(
        "offline first-flash schema is stable",
        report.get("schema") == "antechkids.robostudio.packaged-platformio-offline-first-flash"
        and report.get("schema_version") == 3,
    )
    check("offline first-flash status is PASS", report.get("status") == "PASS")
    check("bootstrap environment is exercised", report.get("environment") == "esp32dev_bootstrap")
    check("network fallback is forbidden", report.get("network_fallback_allowed") is False)
    check(
        "no dependency provisioning was observed",
        report.get("dependency_provisioning_observed") is False,
    )
    check(
        "PlatformIO package installation metadata was verified",
        report.get("package_install_metadata_verified") is True,
    )
    check("physical first-flash payload files were verified", report.get("first_flash_payload_verified") is True)
    payload = report.get("first_flash_payload", {})
    check(
        "Arduino esp32 variant header is part of the first-flash contract",
        isinstance(payload, dict)
        and payload.get("variant") == "esp32"
        and any(str(path).endswith("variants/esp32/pins_arduino.h") for path in payload.get("required_files", [])),
    )
    count = int(report.get("verified_package_count", 0))
    packages = report.get("verified_packages", [])
    check("required PlatformIO package set is non-empty", count > 0 and len(packages) == count)
    check(
        "every required package carries archived .piopm metadata",
        all(str(item.get("piopm", "")).endswith("/.piopm") for item in packages),
    )
    if os.name == "nt":
        alias = str(report.get("windows_short_dependency_alias", "")).strip()
        platforms = str(report.get("platforms_dir", "")).strip()
        package_dir = str(report.get("packages_dir", "")).strip()
        check("Windows first-flash exercised a spaced user-state scenario", report.get("spaced_profile_scenario_verified") is True)
        check("Windows first-flash records short dependency alias", bool(alias))
        check("Windows dependency alias contains no whitespace", report.get("dependency_alias_whitespace_free") is True and not any(char.isspace() for char in alias))
        check("Windows platforms resolve through short alias", bool(platforms) and Path(alias) in Path(platforms).parents)
        check("Windows packages resolve through short alias", bool(package_dir) and Path(alias) in Path(package_dir).parents)
        check("Windows platform dependency path contains no whitespace", not any(char.isspace() for char in platforms))
        check("Windows package dependency path contains no whitespace", not any(char.isspace() for char in package_dir))
    check("offline first-flash produced firmware", int(report.get("firmware_size", 0)) > 0)
    check("USB upload dependency target was exercised", report.get("usb_upload_dependency_probe") is True)
    check("USB upload probe reached uploader", report.get("usb_upload_probe_reached_uploader") is True)
    check("USB upload probe records invalid test port", bool(str(report.get("usb_upload_probe_port", "")).strip()))
    check("offline first-flash log exists", LOG.is_file())
    log = LOG.read_text(encoding="utf-8", errors="replace").casefold()
    forbidden = (
        "tool manager: installing",
        "platform manager: installing",
        "library manager: installing",
        "downloading...",
        "downloading ",
    )
    check("offline first-flash log contains no install/download fallback", not any(x in log for x in forbidden))
    check("offline first-flash log includes USB upload dependency probe", "usb upload dependency probe" in log)
    print(f"B2.7 packaged PlatformIO offline first-flash: PASS ({count} packages)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
