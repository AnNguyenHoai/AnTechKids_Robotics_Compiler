# H26-OTA / H26-CLICK / H26-PV / H26-O

## Objective

Make the ESP32 deployment path practical for classroom use while keeping the existing USB path as the recovery path.

## OTA

The firmware exposes a network service when Wi-Fi credentials are supplied at build time. It uses a unique mDNS hostname (`robot-XXXXXX.local`), ArduinoOTA with an authentication password, and read-only HTTP endpoints:

- `GET /api/v1/info`
- `GET /api/v1/health`

PlatformIO provides the `espota` uploader for ESP32 and accepts IP addresses or mDNS host names as OTA upload targets.

## One-click deployment

`tools/deploy_robot.py` is the canonical host entry point:

```text
student.py
  -> rewrite
  -> compile
  -> infer capabilities
  -> deployment manifest
  -> validate manifest
  -> copy program.h into firmware
  -> build firmware
  -> USB or OTA upload
  -> health check in OTA mode
```

Examples:

```text
python tools/deploy_robot.py --input examples/mission.py --mode build
python tools/deploy_robot.py --input examples/mission.py --mode usb --port COM4 --ssid MyWiFi --wifi-password secret
python tools/deploy_robot.py --input examples/mission.py --mode ota --robot robot-A1B2C3.local --ssid MyWiFi --wifi-password secret
```

The student experience is intentionally reduced to one host command. A future RoboStudio UI can invoke the same tool/service without exposing compiler or PlatformIO details.

## Physical validation

`tools/validate_robot.py` provides a safe network-side gate. It verifies identity, ESP32 target, OTA support, and READY state. It does not command motors or sensors automatically.

When hardware is available, the operator must additionally verify:

1. BOOT / READY
2. motor forward/backward
3. left/right turn
4. sensor input
5. representative student-program behavior

The repository therefore distinguishes **software physical-validation gate PASS** from **real hardware acceptance**.

## Legacy cleanup

The historical `robot-platform/legacy/runtime_cpp_prototype/` remains outside the production `src_filter` and is explicitly non-production. Its deletion is intentionally deferred until the first real hardware validation confirms the canonical runtime path. No production code imports it.

After hardware acceptance, the next cleanup operation is to delete the archived prototype and remove any documentation references that still treat it as a supported implementation.

## Acceptance status

- Host-side OTA/deployment implementation: implemented
- One-click host flow: implemented
- Network readiness gate: implemented
- Real hardware validation: **pending hardware**
- Legacy prototype deletion: **blocked until hardware acceptance**
