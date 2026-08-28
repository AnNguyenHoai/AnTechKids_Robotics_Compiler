#include "SerialCommandHandler.h"
#include "../Services/Robot/MotionConfig.h"
#include "../Services/Robot/RobotAPI.h"
#include "../Devices/SensorConfig.h"
#include "../Behavior/BehaviorScheduler.h"
#include <string.h>

// Sử dụng scheduler toàn cục từ main.ino
extern BehaviorScheduler scheduler;
extern bool useBehaviorEngine;

void SerialCommandHandler::setup() {
    Serial.println("SerialCommandHandler ready. Type 'help' for commands.");
    // Không khởi tạo scheduler ở đây (đã được khởi tạo trong main.ino)
}

void SerialCommandHandler::handle() {
    // DEBUG: in ra mỗi khi hàm được gọi
    static unsigned long lastPrint = 0;
    if (millis() - lastPrint > 5000) {
        Serial.println("[DEBUG] handle() called");
        lastPrint = millis();
    }

    RobotAPI::UpdateEncoders();

    if (!Serial.available()) return;
    String input = Serial.readStringUntil('\n');
    input.trim();
    if (input.length() == 0) return;

    // DEBUG: in ra những gì nhận được
    Serial.print("[DEBUG] Received: ");
    Serial.println(input);

    if (input.startsWith("help")) {
        Serial.println("Commands:");
        Serial.println("  help                - show this message");
        Serial.println("  config show         - show motion config");
        Serial.println("  config set <key> <value> - set motion config");
        Serial.println("  config save         - save motion config");
        Serial.println("  speed <left> <right> - set motor speeds directly");
        Serial.println("  sensor show         - show sensor config");
        Serial.println("  sensor set <key> <value> - set sensor config");
        Serial.println("  encoder show          - show live count/speed/RPM");
        Serial.println("  encoder reset [left|right|all] - reset count");
        Serial.println("  encoder cpr <left> <right> - set decoded counts per wheel revolution");
        Serial.println("  encoder invert <left|right> <0|1> - correct direction");
        Serial.println("  behavior list       - list registered behaviors");
        Serial.println("  behavior start      - start scheduler");
        Serial.println("  behavior stop       - stop scheduler");
        Serial.println("  behavior cancel     - cancel current behavior");
        Serial.println("  behavior status     - show scheduler status");
        Serial.println("  mode vm             - switch to VM execution mode");
        Serial.println("  mode behavior       - switch to Behavior Engine mode");
    }
    // ---------- Motion Config ----------
    else if (input.startsWith("config show")) {
        auto& cfg = RobotAPI::g_motionConfig;
        Serial.printf("wheelDiameter_mm: %.2f\n", cfg.wheelDiameter_mm);
        Serial.printf("wheelBase_mm: %.2f\n", cfg.wheelBase_mm);
        Serial.printf("speedScale: %.3f\n", cfg.speedScale);
        Serial.printf("leftMotorScale: %.3f\n", cfg.leftMotorScale);
        Serial.printf("rightMotorScale: %.3f\n", cfg.rightMotorScale);
        Serial.printf("minSpeed: %d\n", cfg.minSpeed);
        Serial.printf("maxSpeed: %d\n", cfg.maxSpeed);
        Serial.printf("turnCompensation: %.3f\n", cfg.turnCompensation);
        Serial.printf("pwmPerSpeed: %.3f\n", cfg.pwmPerSpeed);
    }
    else if (input.startsWith("config set ")) {
        String rest = input.substring(11);
        int space = rest.indexOf(' ');
        if (space == -1) {
            Serial.println("Invalid format. Use: config set key value");
            return;
        }
        String key = rest.substring(0, space);
        String valStr = rest.substring(space + 1);
        float value = valStr.toFloat();
        auto& cfg = RobotAPI::g_motionConfig;
        if (key == "speedScale") cfg.speedScale = value;
        else if (key == "leftMotorScale") cfg.leftMotorScale = value;
        else if (key == "rightMotorScale") cfg.rightMotorScale = value;
        else if (key == "turnCompensation") cfg.turnCompensation = value;
        else if (key == "pwmPerSpeed") cfg.pwmPerSpeed = value;
        else if (key == "wheelDiameter_mm") cfg.wheelDiameter_mm = value;
        else if (key == "wheelBase_mm") cfg.wheelBase_mm = value;
        else {
            Serial.printf("Unknown key: %s\n", key.c_str());
            return;
        }
        Serial.printf("Set %s to %.3f\n", key.c_str(), value);
    }
    else if (input.startsWith("config save")) {
        RobotAPI::saveMotionConfigToStorage();
        Serial.println("Config saved (placeholder).");
    }
    else if (input.startsWith("speed ")) {
        String rest = input.substring(6);
        int space = rest.indexOf(' ');
        if (space == -1) {
            Serial.println("Usage: speed left right");
            return;
        }
        int left = rest.substring(0, space).toInt();
        int right = rest.substring(space + 1).toInt();
        RobotAPI::setMotorsDirect(left, right);
    }
    // ---------- Sensor Config ----------
    else if (input.startsWith("sensor show")) {
        auto& cfg = g_sensorConfig;
        Serial.printf("ultrasonicTimeoutMs: %d\n", cfg.ultrasonicTimeoutMs);
        Serial.printf("touchDebounceMs: %d\n", cfg.touchDebounceMs);
        Serial.printf("lightGain: %.3f\n", cfg.lightGain);
        Serial.printf("lightOffset: %d\n", cfg.lightOffset);
        Serial.printf("lineInverted: %d\n", cfg.lineInverted);
        Serial.printf("colorOffset: %d\n", cfg.colorOffset);
    }
    else if (input.startsWith("sensor set ")) {
        String rest = input.substring(11);
        int space = rest.indexOf(' ');
        if (space == -1) {
            Serial.println("Invalid format. Use: sensor set key value");
            return;
        }
        String key = rest.substring(0, space);
        String valStr = rest.substring(space + 1);
        float value = valStr.toFloat();
        auto& cfg = g_sensorConfig;
        if (key == "lightGain") cfg.lightGain = value;
        else if (key == "lightOffset") cfg.lightOffset = (int)value;
        else if (key == "ultrasonicTimeoutMs") cfg.ultrasonicTimeoutMs = (uint32_t)value;
        else if (key == "touchDebounceMs") cfg.touchDebounceMs = (uint32_t)value;
        else if (key == "lineInverted") cfg.lineInverted = (value != 0);
        else if (key == "colorOffset") cfg.colorOffset = (int)value;
        else {
            Serial.printf("Unknown key: %s\n", key.c_str());
            return;
        }
        Serial.printf("Set %s to %.3f\n", key.c_str(), value);
    }
    // ---------- Encoder H24-D ----------
    else if (input == "encoder show") {
        RobotAPI::UpdateEncoders();
        for (int side = 0; side < 2; ++side) {
            const char* name = side == 0 ? "left" : "right";
            Serial.printf("encoder %s: count=%lld cps=%.2f rpm=%.2f cpr=%.3f inverted=%d\n",
                          name,
                          (long long)RobotAPI::GetEncoderCount(side),
                          RobotAPI::GetEncoderCountsPerSecond(side),
                          RobotAPI::GetEncoderRPM(side),
                          RobotAPI::GetEncoderCountsPerRevolution(side),
                          RobotAPI::GetEncoderInverted(side));
        }
    }
    else if (input.startsWith("encoder reset")) {
        String target = input.substring(String("encoder reset").length());
        target.trim();
        if (target.length() == 0 || target == "all") { RobotAPI::ResetEncoderCount(0); RobotAPI::ResetEncoderCount(1); }
        else if (target == "left") RobotAPI::ResetEncoderCount(0);
        else if (target == "right") RobotAPI::ResetEncoderCount(1);
        else { Serial.println("Usage: encoder reset [left|right|all]"); return; }
        Serial.println("Encoder count reset.");
    }
    else if (input.startsWith("encoder cpr ")) {
        String rest = input.substring(String("encoder cpr ").length());
        int space = rest.indexOf(' ');
        if (space < 0) { Serial.println("Usage: encoder cpr <left> <right>"); return; }
        float left = rest.substring(0, space).toFloat();
        float right = rest.substring(space + 1).toFloat();
        if (left <= 0.0f || right <= 0.0f) { Serial.println("CPR must be > 0."); return; }
        RobotAPI::SetEncoderCountsPerRevolution(0, left);
        RobotAPI::SetEncoderCountsPerRevolution(1, right);
        Serial.printf("Encoder CPR set: left=%.3f right=%.3f\n", left, right);
    }
    else if (input.startsWith("encoder invert ")) {
        String rest = input.substring(String("encoder invert ").length());
        int space = rest.indexOf(' ');
        if (space < 0) { Serial.println("Usage: encoder invert <left|right> <0|1>"); return; }
        String target = rest.substring(0, space);
        bool inverted = rest.substring(space + 1).toInt() != 0;
        if (target == "left") RobotAPI::SetEncoderInverted(0, inverted);
        else if (target == "right") RobotAPI::SetEncoderInverted(1, inverted);
        else { Serial.println("Target must be left or right."); return; }
        Serial.printf("Encoder %s inverted=%d\n", target.c_str(), inverted);
    }
    // ---------- Behavior ----------
    else if (input.startsWith("behavior list")) {
        auto& behaviors = scheduler.getBehaviors();
        Serial.printf("Total behaviors: %d\n", behaviors.size());
        for (size_t i = 0; i < behaviors.size(); i++) {
            Serial.printf("  %d: %s (status %d)\n", i, behaviors[i]->getName(), (int)behaviors[i]->getStatus());
        }
    }
    else if (input.startsWith("behavior start")) {
        scheduler.start();
        Serial.println("Scheduler started.");
    }
    else if (input.startsWith("behavior stop")) {
        scheduler.stopAll();
        Serial.println("Scheduler stopped.");
    }
    else if (input.startsWith("behavior cancel")) {
        scheduler.cancelCurrent();
        Serial.println("Current behavior cancelled.");
    }
    else if (input.startsWith("behavior status")) {
        scheduler.logState();
    }
    else if (input.startsWith("behavior run ")) {
        int idx = input.substring(13).toInt();
        scheduler.runSingle(idx);
    }
    // ---------- Mode Switching ----------
    else if (input.startsWith("mode vm")) {
        useBehaviorEngine = false;
        Serial.println("Switched to VM mode.");
    }
    else if (input.startsWith("mode behavior")) {
        useBehaviorEngine = true;
        Serial.println("Switched to Behavior Engine mode.");
    }
    else {
        Serial.printf("Unknown command: %s\n", input.c_str());
    }
}