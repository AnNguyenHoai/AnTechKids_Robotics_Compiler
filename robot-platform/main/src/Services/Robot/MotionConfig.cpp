#include "MotionConfig.h"
#include <Preferences.h>

namespace RobotAPI {

MotionConfig g_motionConfig;

static const char* NAMESPACE = "motion";

void loadDefaultMotionConfig() {
    g_motionConfig.wheelDiameter_mm = 65.0f;
    g_motionConfig.wheelBase_mm = 140.0f;
    g_motionConfig.speedScale = 1.0f;
    g_motionConfig.leftMotorScale = 1.0f;
    g_motionConfig.rightMotorScale = 1.0f;
    g_motionConfig.minSpeed = 0;
    g_motionConfig.maxSpeed = 100;
    g_motionConfig.turnCompensation = 1.0f;
    g_motionConfig.pwmPerSpeed = 2.55f;
}

void loadMotionConfigFromStorage() {
    Preferences prefs;
    if (!prefs.begin(NAMESPACE, false)) {
        loadDefaultMotionConfig();
        return;
    }
    g_motionConfig.wheelDiameter_mm = prefs.getFloat("wheelDiameter", 65.0f);
    g_motionConfig.wheelBase_mm = prefs.getFloat("wheelBase", 140.0f);
    g_motionConfig.speedScale = prefs.getFloat("speedScale", 1.0f);
    g_motionConfig.leftMotorScale = prefs.getFloat("leftScale", 1.0f);
    g_motionConfig.rightMotorScale = prefs.getFloat("rightScale", 1.0f);
    g_motionConfig.minSpeed = prefs.getInt("minSpeed", 0);
    g_motionConfig.maxSpeed = prefs.getInt("maxSpeed", 100);
    g_motionConfig.turnCompensation = prefs.getFloat("turnComp", 1.0f);
    g_motionConfig.pwmPerSpeed = prefs.getFloat("pwmPerSpeed", 2.55f);
    prefs.end();
}

void saveMotionConfigToStorage() {
    Preferences prefs;
    if (!prefs.begin(NAMESPACE, false)) {
        return;
    }
    prefs.putFloat("wheelDiameter", g_motionConfig.wheelDiameter_mm);
    prefs.putFloat("wheelBase", g_motionConfig.wheelBase_mm);
    prefs.putFloat("speedScale", g_motionConfig.speedScale);
    prefs.putFloat("leftScale", g_motionConfig.leftMotorScale);
    prefs.putFloat("rightScale", g_motionConfig.rightMotorScale);
    prefs.putInt("minSpeed", g_motionConfig.minSpeed);
    prefs.putInt("maxSpeed", g_motionConfig.maxSpeed);
    prefs.putFloat("turnComp", g_motionConfig.turnCompensation);
    prefs.putFloat("pwmPerSpeed", g_motionConfig.pwmPerSpeed);
    prefs.end();
}

} // namespace RobotAPI