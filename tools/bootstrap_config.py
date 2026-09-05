#!/usr/bin/env python3
"""Generate and validate the first-flash Wi-Fi bootstrap artifact.

The artifact is intentionally local-only. It is consumed by PlatformIO at
build time and must never be committed to the repository.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

SCHEMA_VERSION = 1
ARTIFACT_TYPE = "antechkids.robot.bootstrap"


def _validate_ssid(value: str) -> str:
    value = value.strip()
    if not value:
        raise ValueError("Wi-Fi SSID must not be empty")
    if len(value.encode("utf-8")) > 32:
        raise ValueError("Wi-Fi SSID must be at most 32 UTF-8 bytes")
    return value


def _validate_password(value: str) -> str:
    if len(value.encode("utf-8")) > 63:
        raise ValueError("Wi-Fi password must be at most 63 UTF-8 bytes")
    return value


def _validate_ota_password(value: str) -> str:
    if not value:
        raise ValueError("OTA password is required for first-flash bootstrap")
    if len(value.encode("utf-8")) > 63:
        raise ValueError("OTA password must be at most 63 UTF-8 bytes")
    return value


def make_config(ssid: str, password: str, ota_password: str) -> dict:
    return {
        "type": ARTIFACT_TYPE,
        "schema_version": SCHEMA_VERSION,
        "wifi": {"ssid": _validate_ssid(ssid), "password": _validate_password(password)},
        "ota": {"password": _validate_ota_password(ota_password)},
    }


def validate_config(path: Path) -> dict:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"invalid bootstrap config: {exc}") from exc
    if not isinstance(data, dict) or data.get("type") != ARTIFACT_TYPE:
        raise ValueError("unsupported bootstrap config type")
    if data.get("schema_version") != SCHEMA_VERSION:
        raise ValueError("unsupported bootstrap schema version")
    wifi = data.get("wifi")
    ota = data.get("ota")
    if not isinstance(wifi, dict) or not isinstance(ota, dict):
        raise ValueError("bootstrap config requires wifi and ota objects")
    _validate_ssid(str(wifi.get("ssid", "")))
    _validate_password(str(wifi.get("password", "")))
    _validate_ota_password(str(ota.get("password", "")))
    return data


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate/validate first-flash Wi-Fi bootstrap data")
    sub = parser.add_subparsers(dest="command", required=True)

    generate = sub.add_parser("generate")
    generate.add_argument("--ssid", required=True)
    generate.add_argument("--password", default="")
    generate.add_argument("--ota-password", required=True)
    generate.add_argument("--output", required=True, type=Path)

    validate = sub.add_parser("validate")
    validate.add_argument("--input", required=True, type=Path)

    args = parser.parse_args()
    try:
        if args.command == "generate":
            config = make_config(args.ssid, args.password, args.ota_password)
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(json.dumps(config, indent=2) + "\n", encoding="utf-8")
            print(f"BOOTSTRAP CONFIG READY: {args.output}")
        else:
            validate_config(args.input)
            print("BOOTSTRAP CONFIG VALID")
        return 0
    except ValueError as exc:
        print(f"BOOTSTRAP CONFIG ERROR: {exc}")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
