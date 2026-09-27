#!/usr/bin/env python3
"""Receive qualification-only LINE-REG UDP broadcast records and save raw logs."""
from __future__ import annotations

import argparse
import socket
from pathlib import Path

DEFAULT_PORT = 4211
MAX_PACKET = 4096


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Capture LINE-REG UDP diagnostics")
    parser.add_argument("--bind", default="0.0.0.0", help="local interface to bind")
    parser.add_argument("--port", type=int, default=DEFAULT_PORT, help="UDP listen port")
    parser.add_argument("--output", required=True, help="output .log path")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind((args.bind, args.port))
    sock.settimeout(1.0)

    print(f"Listening for LINE-REG UDP packets on {args.bind}:{args.port}")
    print(f"Saving raw records to {output}")
    print("Press Ctrl+C to stop.")

    try:
        with output.open("a", encoding="utf-8", buffering=1) as log:
            while True:
                try:
                    payload, sender = sock.recvfrom(MAX_PACKET)
                except socket.timeout:
                    continue

                text = payload.decode("utf-8", errors="replace")
                for raw_line in text.splitlines():
                    line = raw_line.strip()
                    if not line or "[LINE-REG]" not in line:
                        continue
                    print(f"{sender[0]}:{sender[1]} {line}")
                    # Keep the file format identical to the existing Serial log
                    # so current LINE-REG analysis can consume it unchanged.
                    log.write(line + "\n")
    except KeyboardInterrupt:
        print(f"\nCapture stopped. Log saved to {output}")
        return 0
    finally:
        sock.close()


if __name__ == "__main__":
    raise SystemExit(main())
