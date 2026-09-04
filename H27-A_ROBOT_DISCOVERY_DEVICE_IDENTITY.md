# H27-A — Robot Discovery & Device Identity

## Objective

Make a robot discoverable on the local LAN without requiring the user to know its IP address or serial port, and expose a stable device identity that RoboStudio can use for selection and future deployment sessions.

## Identity contract

Each ESP32 derives a stable `device_id` from its eFuse MAC address. The same suffix is used for a deterministic hostname and a human-readable display name.

Example:

```text
Device ID:   robot-A1B2C3D4E5F6
Hostname:    robot-D4E5F6.local
Display name: AnTechKids Robot D4E5F6
Target:      esp32
```

The identity payload uses protocol version `antechkids.robot.v1` and includes target, firmware version, readiness, OTA availability, and generated hardware capabilities.

## LAN discovery protocol

Discovery uses UDP port `4210` so the host does not need to know the robot IP address.

Request:

```text
ANTECHKIDS_ROBOT_DISCOVER_V1
```

Response:

```text
ANTECHKIDS_ROBOT_INFO_V1
<JSON identity payload>
```

The responder ignores unknown requests and does not move motors or alter the running student program.

## Host discovery

Run:

```bash
python tools/discover_robot.py
```

The tool broadcasts the request, collects responses for a bounded timeout, de-duplicates by `device_id`, and prints JSON records. Exit code `0` means at least one robot was discovered; exit code `1` means none were found.

## Scope boundary

H27-A owns discovery and identity only. It does not assign a robot to a student, create a deployment session, or upload a program. Those concerns belong to subsequent H27 tasks.

## Security / safety boundary

Discovery is read-only. OTA authentication remains owned by `RobotNetworkService`/ArduinoOTA. Discovery must not expose Wi-Fi credentials or OTA passwords.

## Validation

Host-side H27-A contract tests verify:

- identity fields and protocol version;
- stable device-id/hostname implementation;
- UDP discovery request/response contract;
- integration with the network service;
- host discovery client behavior.

Real hardware validation should additionally confirm that two or more physical robots can be discovered on the same classroom LAN and that each robot reports a unique `device_id`.
