#include "RobotIdentity.h"

#include <WiFi.h>
#include "../generated/generated_device_config.h"

namespace {
String g_deviceId;
String g_hostname;
String g_displayName;
bool g_initialized = false;

void ensureInitialized() {
    if (g_initialized) {
        return;
    }

    uint64_t efuseMac = ESP.getEfuseMac();
    char idBuffer[13];
    snprintf(idBuffer, sizeof(idBuffer), "%012llX", efuseMac);

    g_deviceId = String("robot-") + idBuffer;
    g_hostname = String("robot-") + String(idBuffer + 6);
    g_displayName = String("AnTechKids Robot ") + String(idBuffer + 6);
    g_initialized = true;
}

String boolJson(bool value) {
    return value ? "true" : "false";
}
}

namespace RobotIdentity {

const char* deviceId() {
    ensureInitialized();
    return g_deviceId.c_str();
}

const char* hostname() {
    ensureInitialized();
    return g_hostname.c_str();
}

const char* displayName() {
    ensureInitialized();
    return g_displayName.c_str();
}

const char* target() {
    return "esp32";
}

const char* firmwareVersion() {
#ifdef ROBOT_FIRMWARE_VERSION
    return ROBOT_FIRMWARE_VERSION;
#else
    return "dev";
#endif
}

String capabilitiesJson() {
    return String("{\"motor\":") + boolJson(ROBOT_FEATURE_MOTOR) +
           ",\"encoder\":" + boolJson(ROBOT_FEATURE_ENCODER) +
           ",\"line_sensor\":" + boolJson(ROBOT_FEATURE_LINE_SENSOR) +
           ",\"ultrasonic\":" + boolJson(ROBOT_FEATURE_ULTRASONIC) +
           ",\"imu\":" + boolJson(ROBOT_FEATURE_IMU) +
           ",\"servo\":" + boolJson(ROBOT_FEATURE_SERVO) +
           ",\"buzzer\":" + boolJson(ROBOT_FEATURE_BUZZER) + "}";
}

String infoJson(bool ready, bool otaReady) {
    ensureInitialized();
    String body = "{\"protocol\":\"antechkids.robot.v1\",\"device_id\":\"" +
                  g_deviceId + "\",\"name\":\"" + g_displayName +
                  "\",\"hostname\":\"" + g_hostname +
                  "\",\"ip\":\"" + WiFi.localIP().toString() +
                  "\",\"target\":\"" + target() +
                  "\",\"firmware\":\"" + firmwareVersion() +
                  "\",\"ready\":" + boolJson(ready) +
                  ",\"ota\":" + boolJson(otaReady) +
                  ",\"capabilities\":" + capabilitiesJson() + "}";
    return body;
}

}
