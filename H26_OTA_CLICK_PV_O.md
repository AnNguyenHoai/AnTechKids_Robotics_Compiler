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

The student experience is intentionally reduced to one host command. A future RoboStudio UI can invoke the same tool/service without exposing compiler or PlatformIO details.

## Physical validation

`tools/validate_robot.py` provides a safe network-side gate. It verifies identity, ESP32 target, OTA support, and READY state. It does not command motors or sensors automatically.

Real hardware validation of the canonical runtime/deployment path has now been completed before H26-O. The accepted path is therefore proven on the target robot hardware, while the repository still keeps physical behavior verification separate from host-side tests.

## Legacy cleanup

The historical `robot-platform/legacy/runtime_cpp_prototype/` has been retired after real ESP32 hardware validation confirmed the canonical runtime/deployment path. The older `robot-platform/deploy.py` flow and its dedicated `deploy_program.py` sample have also been retired because `tools/deploy_robot.py` is now the canonical deployment entry point.

`tools/flash.py` remains available as a low-level/recovery primitive; it is not a second student-facing deployment workflow.

## Acceptance status

- Host-side OTA/deployment implementation: implemented
- One-click host flow: implemented
- Network readiness gate: implemented
- Real hardware validation: **completed**
- Legacy prototype deletion: **completed**
- Legacy deployment-script retirement: **completed**
