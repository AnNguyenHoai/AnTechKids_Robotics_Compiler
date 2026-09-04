import os

Import("env")

# Inject local-only Wi-Fi/OTA credentials into the firmware build. Credentials
# are read from the process environment and are never stored in the repository.
ssid = os.getenv("ROBOT_WIFI_SSID", "")
password = os.getenv("ROBOT_WIFI_PASSWORD", "")
ota_password = os.getenv("ROBOT_OTA_PASSWORD", "robot-ota")

env.Append(CPPDEFINES=[
    ("ROBOT_WIFI_SSID", env.StringifyMacro(ssid)),
    ("ROBOT_WIFI_PASSWORD", env.StringifyMacro(password)),
    ("ROBOT_OTA_PASSWORD", env.StringifyMacro(ota_password)),
])
