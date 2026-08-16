#include "SerialCommandHandler.h"
#include "../Services/Robot/MotionConfig.h"
#include "../Services/Robot/RobotAPI.h"
#include "../Devices/SensorConfig.h"
#include "../Behavior/BehaviorScheduler.h"
#include "../Diagnostics/DiagnosticsManager.h"
#include "../Sensor/SensorManager.h"
#include "../Sensor/TCRT5000.h"
#include "../Sensor/IMUSensor.h"
#include "../Sensor/SensorID.h"
#include "../Diagnostics/Console/DevelopmentConsole.h"
#include "../Services/Motion/HeadingEstimator.h"
#include "../Services/Motion/HeadingController.h"
#include "../Sensor/Ultrasonic.h"   // thêm include cho Ultrasonic

#include <string.h>

extern BehaviorScheduler scheduler;
extern bool useBehaviorEngine;
extern HeadingEstimator g_headingEstimator;

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
        Serial.println("  behavior run <idx>  - run a single behavior by index");
        Serial.println("  mode vm             - switch to VM execution mode");
        Serial.println("  mode behavior       - switch to Behavior Engine mode");
        Serial.println("  diagnostics (diag)  - print sensor and runtime diagnostics");
        Serial.println("  diag raw            - print raw sensor values and detected state");
        Serial.println("  diag init           - print sensor initialization status");
        Serial.println("  console on/off       - enable/disable realtime console");
        Serial.println("  console rate <hz>    - set refresh rate (1-50 Hz)");
        Serial.println("  console              - show console status");
        Serial.println("  motor calib show               - show calibration values and example");
        Serial.println("  motor calib set left <val>     - set left motor scale (0.50-1.50)");
        Serial.println("  motor calib set right <val>    - set right motor scale (0.50-1.50)");
        Serial.println("  motor calib reset              - reset both scales to 1.0");
        Serial.println("  motor calib test <speed>       - run motors at effective speed and display");
        Serial.println("  imu status          - show IMU status and configuration");
        Serial.println("  imu read            - read and display current IMU data");
        Serial.println("  imu calibrate       - perform gyroscope bias calibration (robot must be still)");
        Serial.println("  heading status      - show current relative heading and gyro info");
        Serial.println("  heading control     - show heading hold controller status");
        Serial.println("  robot status        - show robot ready state and IMU status");
        Serial.println("  ultra diag          - show ultrasonic diagnostic statistics");
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
        int cmd = 50;
        int leftEff = cmd * cfg.speedScale * cfg.leftMotorScale;
        int rightEff = cmd * cfg.speedScale * cfg.rightMotorScale;
        leftEff = constrain(leftEff, -100, 100);
        rightEff = constrain(rightEff, -100, 100);
        Serial.printf("Example command %d -> effective L=%d, R=%d\n", cmd, leftEff, rightEff);
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
        else if (key == "leftMotorScale") {
            if (value < MIN_MOTOR_SCALE || value > MAX_MOTOR_SCALE) {
                Serial.printf("Error: leftMotorScale must be between %.2f and %.2f\n", MIN_MOTOR_SCALE, MAX_MOTOR_SCALE);
                return;
            }
            cfg.leftMotorScale = value;
        }
        else if (key == "rightMotorScale") {
            if (value < MIN_MOTOR_SCALE || value > MAX_MOTOR_SCALE) {
                Serial.printf("Error: rightMotorScale must be between %.2f and %.2f\n", MIN_MOTOR_SCALE, MAX_MOTOR_SCALE);
                return;
            }
            cfg.rightMotorScale = value;
        }
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
        Serial.println("Config saved.");
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
            auto& mgr = SensorManager::instance();
            auto left = mgr.getSensor(SensorID::LineLeft);
            auto center = mgr.getSensor(SensorID::LineCenter);
            auto right = mgr.getSensor(SensorID::LineRight);
            Serial.println("[INIT] Sensor pointers:");
            Serial.printf("  Left  : %s\n", left ? "OK" : "NULL");
            Serial.printf("  Center: %s\n", center ? "OK" : "NULL");
            Serial.printf("  Right : %s\n", right ? "OK" : "NULL");
        }
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
            DiagnosticsManager::instance().printReport();
        }
    }
    // ---------- Motor Calibration ----------
    else if (input.startsWith("motor calib show")) {
        auto& cfg = RobotAPI::g_motionConfig;
        Serial.println("--- Motor Calibration ---");
        Serial.printf("leftMotorScale  : %.3f\n", cfg.leftMotorScale);
        Serial.printf("rightMotorScale : %.3f\n", cfg.rightMotorScale);
        Serial.printf("speedScale      : %.3f\n", cfg.speedScale);
        int cmd = 50;
        int leftEff = cmd * cfg.speedScale * cfg.leftMotorScale;
        int rightEff = cmd * cfg.speedScale * cfg.rightMotorScale;
        leftEff = constrain(leftEff, -100, 100);
        rightEff = constrain(rightEff, -100, 100);
        Serial.printf("Example command %d -> effective L=%d, R=%d\n", cmd, leftEff, rightEff);
    }
    else if (input.startsWith("motor calib set left ")) {
        float val = input.substring(21).toFloat();
        if (val < MIN_MOTOR_SCALE || val > MAX_MOTOR_SCALE) {
            Serial.printf("Error: leftMotorScale must be between %.2f and %.2f\n", MIN_MOTOR_SCALE, MAX_MOTOR_SCALE);
        } else {
            RobotAPI::g_motionConfig.leftMotorScale = val;
            Serial.printf("leftMotorScale set to %.3f\n", val);
        }
    }
    else if (input.startsWith("motor calib set right ")) {
        float val = input.substring(22).toFloat();
        if (val < MIN_MOTOR_SCALE || val > MAX_MOTOR_SCALE) {
            Serial.printf("Error: rightMotorScale must be between %.2f and %.2f\n", MIN_MOTOR_SCALE, MAX_MOTOR_SCALE);
        } else {
            RobotAPI::g_motionConfig.rightMotorScale = val;
            Serial.printf("rightMotorScale set to %.3f\n", val);
        }
    }
    else if (input.startsWith("motor calib reset")) {
        RobotAPI::g_motionConfig.leftMotorScale = 1.0f;
        RobotAPI::g_motionConfig.rightMotorScale = 1.0f;
        Serial.println("Motor calibration reset to 1.0");
    }
    else if (input.startsWith("motor calib test ")) {
        int speed = input.substring(17).toInt();
        if (speed < -100 || speed > 100) {
            Serial.println("Error: speed must be between -100 and 100");
        } else {
            auto& cfg = RobotAPI::g_motionConfig;
            int leftEff = speed * cfg.speedScale * cfg.leftMotorScale;
            int rightEff = speed * cfg.speedScale * cfg.rightMotorScale;
            leftEff = constrain(leftEff, -100, 100);
            rightEff = constrain(rightEff, -100, 100);
            Serial.printf("Command: %d, effective left: %d, right: %d\n", speed, leftEff, rightEff);
            RobotAPI::setMotorsDirect(leftEff, rightEff);
            Serial.println("Motors running at effective speeds. Use 'speed 0 0' to stop.");
        }
    }
    // ---------- IMU ----------
    else if (input.startsWith("imu status")) {
        auto* imu = static_cast<IMUSensor*>(SensorManager::instance().getSensor(SensorID::IMU));
        if (!imu) {
            Serial.println("IMU sensor not available.");
            return;
        }
        Serial.println("--- IMU Status ---");
        Serial.printf("Initialized: %s\n", imu->isReady() ? "YES" : "NO");
        Serial.printf("Calibrated : %s\n", imu->isCalibrated() ? "YES" : "NO");
        Serial.printf("Address    : 0x%02X\n", imu->getAddress());
        Serial.printf("Robot Ready: %s\n", RobotAPI::isRobotReady() ? "YES" : "NO");
        MPU6050Bias bias = imu->getBias();
        Serial.printf("Bias X     : %.3f deg/s\n", bias.bx);
        Serial.printf("Bias Y     : %.3f deg/s\n", bias.by);
        Serial.printf("Bias Z     : %.3f deg/s\n", bias.bz);
        Serial.println("---");
    }
    else if (input.startsWith("imu read")) {
        auto* imu = static_cast<IMUSensor*>(SensorManager::instance().getSensor(SensorID::IMU));
        if (!imu || !imu->isReady()) {
            Serial.println("IMU sensor not ready.");
            return;
        }
        MPU6050AccelData accel;
        MPU6050GyroData gyro;
        float temp = 0.0f;
        if (imu->readAccel(accel) && imu->readGyro(gyro)) {
            temp = imu->readTemperature();
            Serial.printf("Accel  X=%.3f g  Y=%.3f g  Z=%.3f g\n", accel.ax, accel.ay, accel.az);
            Serial.printf("Gyro   X=%.3f deg/s  Y=%.3f deg/s  Z=%.3f deg/s\n", gyro.gx, gyro.gy, gyro.gz);
            Serial.printf("Temp   %.2f °C\n", temp);
        } else {
            Serial.println("Failed to read IMU data.");
        }
    }
    else if (input.startsWith("imu calibrate")) {
        auto* imu = static_cast<IMUSensor*>(SensorManager::instance().getSensor(SensorID::IMU));
        if (!imu || !imu->isReady()) {
            Serial.println("IMU sensor not ready.");
            return;
        }
        Serial.println("Starting gyroscope calibration. Keep robot completely still!");
        int result = imu->calibrateGyro(500);
        if (result == 0) {
            MPU6050Bias bias = imu->getBias();
            Serial.printf("Calibration SUCCESS. Bias: X=%.3f Y=%.3f Z=%.3f deg/s\n",
                          bias.bx, bias.by, bias.bz);
            g_headingEstimator.reset();
            RobotAPI::resetHeadingController();
            Serial.println("Heading estimator and controller reset.");
        } else if (result == 1) {
            Serial.println("Calibration FAILED: UNSTABLE (robot moved too much)");
        } else {
            Serial.println("Calibration FAILED: communication error");
        }
    }
    // ---------- Heading ----------
    else if (input.startsWith("heading status")) {
        Serial.println("--- Heading Status ---");
        Serial.printf("Initialized : %s\n", g_headingEstimator.isInitialized() ? "YES" : "NO");
        Serial.printf("Heading     : %.2f deg\n", g_headingEstimator.getHeadingDeg());
        Serial.printf("Gyro Z      : %.2f deg/s\n", g_headingEstimator.getLastGyroZ());
        Serial.printf("dt          : %.3f s\n", g_headingEstimator.getLastDt());
        Serial.printf("Timestamp   : %lu\n", g_headingEstimator.getLastTimestamp());
        auto* imu = static_cast<IMUSensor*>(SensorManager::instance().getSensor(SensorID::IMU));
        if (imu) {
            Serial.printf("IMU Calibrated: %s\n", imu->isCalibrated() ? "YES" : "NO");
        }
        Serial.println("---");
    }
    else if (input.startsWith("heading control")) {
        auto* imu = static_cast<IMUSensor*>(SensorManager::instance().getSensor(SensorID::IMU));
        bool imuCalibrated = (imu && imu->isReady() && imu->isCalibrated());

        Serial.println("--- Heading Control ---");
        Serial.printf("State         : %s\n", RobotAPI::isHeadingHoldActive() ? "HOLDING" : "DISABLED");
        Serial.printf("Robot Ready   : %s\n", RobotAPI::isRobotReady() ? "YES" : "NO");
        Serial.printf("IMU Calibrated: %s\n", imuCalibrated ? "YES" : "NO");
        Serial.printf("Target        : %.2f deg\n", RobotAPI::getHeadingTarget());
        Serial.printf("Current       : %.2f deg\n", g_headingEstimator.getHeadingDeg());
        Serial.printf("Error         : %.2f deg\n", RobotAPI::getHeadingError());
        Serial.printf("Correction    : %.2f\n", RobotAPI::getHeadingCorrection());
        Serial.printf("Kp            : %.3f\n", RobotAPI::getHeadingKp());
        Serial.printf("Ki            : %.3f\n", RobotAPI::getHeadingKi());
        Serial.printf("Kd            : %.3f\n", RobotAPI::getHeadingKd());
        Serial.printf("MaxCorrection : %.1f\n", RobotAPI::getHeadingMaxCorrection());
        Serial.printf("Heading Hold  : %s\n", RobotAPI::isHeadingHoldEnabled() ? "ENABLED" : "DISABLED");
        Serial.printf("Effective L   : %d\n", RobotAPI::getEffectiveLeft());
        Serial.printf("Effective R   : %d\n", RobotAPI::getEffectiveRight());
        Serial.println("-----------------------");
    }
    // ---------- Robot Status ----------
    else if (input.startsWith("robot status")) {
        auto* imu = static_cast<IMUSensor*>(SensorManager::instance().getSensor(SensorID::IMU));
        Serial.println("--- Robot Status ---");
        Serial.printf("Robot Ready  : %s\n", RobotAPI::isRobotReady() ? "YES" : "NO");
        if (imu) {
            Serial.printf("IMU Ready    : %s\n", imu->isReady() ? "YES" : "NO");
            Serial.printf("IMU Calibrated: %s\n", imu->isCalibrated() ? "YES" : "NO");
            MPU6050Bias bias = imu->getBias();
            Serial.printf("Bias Z       : %.3f deg/s\n", bias.bz);
        } else {
            Serial.println("IMU: NOT AVAILABLE");
        }
        Serial.printf("Heading      : %.2f deg\n", g_headingEstimator.getHeadingDeg());
        Serial.printf("Heading Hold : %s\n", RobotAPI::isHeadingHoldActive() ? "ACTIVE" : "INACTIVE");
        Serial.println("-------------------");
    }
    // Phần lệnh ultra diag (thay thế đoạn cũ)
    else if (input.startsWith("ultra diag")) {
        Serial.println("--- Ultrasonic Diagnostics ---");
        auto sensor = SensorManager::instance().getSensor(SensorID::Ultrasonic);
        if (sensor) {
            auto us = static_cast<Ultrasonic*>(sensor);
            us->update();
            Serial.printf("Healthy              : %s\n", us->healthy() ? "YES" : "NO");
            Serial.printf("Consecutive Timeouts : %d\n", us->getConsecutiveTimeouts());
            Serial.printf("Last Distance        : %.1f cm\n", us->distanceCm());
        } else {
            Serial.println("Ultrasonic sensor not available.");
        }
        uint32_t total = RobotAPI::getUltraReadCount();
        uint32_t fails = RobotAPI::getUltraFailCount();
        Serial.printf("Total Reads   : %lu\n", total);
        Serial.printf("Fail Reads    : %lu\n", fails);
        Serial.printf("Fail Rate     : %.1f%%\n", total > 0 ? 100.0f * fails / total : 0.0f);
        Serial.printf("Current Speed : %d\n", RobotAPI::getCurrentBaseSpeed());
        Serial.printf("Direction     : %d\n", RobotAPI::getCurrentDirection());
        Serial.println("-----------------------------");
    }
    else {
        Serial.printf("Unknown command: %s\n", input.c_str());
    }
}