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
        and report.get("schema_version") == 2,
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
        check("Windows first-flash records short dependency alias", bool(alias))
        check("Windows platforms resolve through short alias", bool(platforms) and Path(alias) in Path(platforms).parents)
        check("Windows packages resolve through short alias", bool(package_dir) and Path(alias) in Path(package_dir).parents)
    check("offline first-flash produced firmware", int(report.get("firmware_size", 0)) > 0)
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
    print(f"B2.7 packaged PlatformIO offline first-flash: PASS ({count} packages)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
