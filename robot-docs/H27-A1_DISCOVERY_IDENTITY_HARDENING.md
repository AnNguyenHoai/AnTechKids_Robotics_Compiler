# H27-A.1 — Discovery & Identity Hardening

## Objective

Harden the H27-A Robot Discovery & Device Identity prototype without changing student program execution, motor behavior, VM behavior, or the existing physical Golden Path.

## Canonical identity contract

`antechkids.robot.v1` remains the protocol identifier and schema version `1` is explicit.

Each robot exposes:

- `device_id`: stable `robot-<12 uppercase hex>` identifier derived from the ESP32 eFuse MAC;
- `hostname`: deterministic `robot-<last 6 hex>.local` host name;
- `name`: human-readable robot name;
- `target` and `firmware`;
- `robot_ready`: hardware/runtime readiness;
- `network_ready`: network service readiness;
- `ready`: backward-compatible aggregate (`robot_ready && network_ready`);
- `ota`: OTA service readiness;
- `capabilities`: generated hardware capability map.

No Wi-Fi or OTA credential is exposed by discovery or `/api/v1/info`.

## Discovery hardening

The UDP discovery protocol remains on port `4210` with the existing V1 request/response prefixes. The firmware now retries binding after transient failures and stops the UDP socket when Wi-Fi is lost. Malformed/oversized discovery packets are ignored without affecting robot execution.

The host discovery tool validates protocol version, required fields, device-id/hostname shape, IP address, readiness booleans, and capability types before accepting a record. Records remain de-duplicated by `device_id`.

## OTA credential policy

The shared `robot-ota` default is removed. OTA is enabled only when a non-empty `ROBOT_OTA_PASSWORD` is explicitly provisioned. The `esp32dev_ota` PlatformIO environment fails early when the OTA credential is missing.

This keeps local development/builds possible while preventing an accidentally deployed firmware from silently using a repository-wide default OTA password.

## Network readiness

`RobotNetworkService` separates network readiness, OTA readiness, robot readiness, and OTA-update-in-progress state. The existing `ready` health field remains as an aggregate for compatibility with the current deployment path.

## Deployment contract alignment

The one-click deployment tool now records `esp32dev` for build/USB and `esp32dev_ota` for OTA in the deployment manifest, matching the actual PlatformIO environment used for deployment.

## Validation

H27-A.1 host-side tests verify the hardened identity, discovery, readiness, retry, OTA credential, and deployment-environment contracts. Physical discovery remains a hardware acceptance activity and is not claimed by host-side tests.
