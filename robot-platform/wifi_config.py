import os

Import("env")

# Inject local-only Wi-Fi/OTA credentials into the firmware build. Credentials
# are read from the process environment and are never stored in the repository.
ssid = os.getenv("ROBOT_WIFI_SSID", "")
password = os.getenv("ROBOT_WIFI_PASSWORD", "")
ota_password = os.getenv("ROBOT_OTA_PASSWORD", "")

# OTA builds must be explicitly provisioned. Never fall back to a shared/default
# credential because every classroom robot must have an intentional OTA secret.
if env.get("PIOENV") == "esp32dev_ota" and not ota_password:
    raise RuntimeError(
        "ROBOT_OTA_PASSWORD must be set for esp32dev_ota builds; "
        "no shared/default OTA credential is permitted"
    )

env.Append(CPPDEFINES=[
    ("ROBOT_WIFI_SSID", env.StringifyMacro(ssid)),
    ("ROBOT_WIFI_PASSWORD", env.StringifyMacro(password)),
    ("ROBOT_OTA_PASSWORD", env.StringifyMacro(ota_password)),
])
