#include "SerialCommandHandler.h"
#include "../Services/Robot/MotionConfig.h"
#include "../Services/Robot/RobotAPI.h"
#include "../Devices/SensorConfig.h"
#include "../Behavior/BehaviorScheduler.h"
#include "../Diagnostics/DiagnosticsManager.h"
#include "../Sensor/SensorManager.h"
#include "../Sensor/TCRT5000.h"
#include <string.h>
#include "../Diagnostics/Console/DevelopmentConsole.h"



extern BehaviorScheduler scheduler;
extern bool useBehaviorEngine;

void SerialCommandHandler::setup() {
    Serial.println("SerialCommandHandler ready. Type 'help' for commands.");
}

void SerialCommandHandler::handle() {
    if (!Serial.available()) return;
    String input = Serial.readStringUntil('\n');
    input.trim();
    if (input.length() == 0) return;

    if (input.startsWith("help")) {
        Serial.println("Commands:");
        Serial.println("  help                - show this message");
        Serial.println("  config show         - show motion config");
        Serial.println("  config set <key> <value> - set motion config");
        Serial.println("  config save         - save motion config");
        Serial.println("  speed <left> <right> - set motor speeds directly");
        Serial.println("  sensor show         - show sensor config");
        Serial.println("  sensor set <key> <value> - set sensor config");
        Serial.println("  behavior list       - list registered behaviors");
        Serial.println("  behavior start      - start scheduler");
        Serial.println("  behavior stop       - stop scheduler");
        Serial.println("  behavior cancel     - cancel current behavior");
        Serial.println("  behavior status     - show scheduler status");
        Serial.println("  mode vm             - switch to VM execution mode");
        Serial.println("  mode behavior       - switch to Behavior Engine mode");
        Serial.println("  diagnostics (diag)  - print sensor and runtime diagnostics");
        Serial.println("  diag raw            - print raw sensor values and detected state");
        Serial.println("  diag init           - print sensor initialization status");
        Serial.println("  console on/off       - enable/disable realtime console");
        Serial.println("  console rate <hz>    - set refresh rate (1-50 Hz)");
        Serial.println("  console              - show console status");
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
    // ---------- Diagnostics ----------
    else if (input.startsWith("diagnostics") || input.startsWith("diag")) {
        // Nếu có thêm từ khóa "raw" hoặc "init"
        if (input.startsWith("diag raw")) {
            auto& mgr = SensorManager::instance();
            auto left = mgr.getSensor(SensorID::LineLeft);
            auto center = mgr.getSensor(SensorID::LineCenter);
            auto right = mgr.getSensor(SensorID::LineRight);

            if (left) {
                auto l = static_cast<TCRT5000*>(left);
                l->update();
                Serial.printf("[RAW] Left  : raw=%d, detected=%d\n", l->rawLevel(), l->isLineDetected() ? 1 : 0);
            }
            if (center) {
                auto c = static_cast<TCRT5000*>(center);
                c->update();
                Serial.printf("[RAW] Center: raw=%d, detected=%d\n", c->rawLevel(), c->isLineDetected() ? 1 : 0);
            }
            if (right) {
                auto r = static_cast<TCRT5000*>(right);
                r->update();
                Serial.printf("[RAW] Right : raw=%d, detected=%d\n", r->rawLevel(), r->isLineDetected() ? 1 : 0);
            }
        }
        else if (input.startsWith("diag init")) {
            // Kiểm tra trạng thái khởi tạo sensor
            auto& mgr = SensorManager::instance();
            auto left = mgr.getSensor(SensorID::LineLeft);
            auto center = mgr.getSensor(SensorID::LineCenter);
            auto right = mgr.getSensor(SensorID::LineRight);
            Serial.println("[INIT] Sensor pointers:");
            Serial.printf("  Left  : %s\n", left ? "OK" : "NULL");
            Serial.printf("  Center: %s\n", center ? "OK" : "NULL");
            Serial.printf("  Right : %s\n", right ? "OK" : "NULL");
        }
        // ---------- Development Console ----------
        else if (input.startsWith("console on")) {
            DevelopmentConsole::instance().setEnabled(true);
            Serial.println("Console enabled.");
        }
        else if (input.startsWith("console off")) {
            DevelopmentConsole::instance().setEnabled(false);
            Serial.println("Console disabled.");
        }
        else if (input.startsWith("console rate ")) {
            int rate = input.substring(13).toInt();
            if (rate >= 1 && rate <= 50) {
                DevelopmentConsole::instance().setRefreshRateHz(rate);
                Serial.printf("Console rate set to %d Hz\n", rate);
            } else {
                Serial.println("Rate must be between 1 and 50 Hz.");
            }
        }
        else if (input.startsWith("console")) {
            bool en = DevelopmentConsole::instance().isEnabled();
            uint8_t rate = DevelopmentConsole::instance().getRefreshRateHz();
            Serial.printf("Console: %s, rate: %d Hz\n", en ? "ON" : "OFF", rate);
        }
        else {
            // Mặc định in diagnostics
            DiagnosticsManager::instance().printReport();
        }
    }
    else {
        Serial.printf("Unknown command: %s\n", input.c_str());
    }
}