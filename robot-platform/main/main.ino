#include "src/Services/VM/ProgramLoader.h"
#include "src/Services/VM/VM.h"
#include "src/Services/Robot/RobotAPI.h"
#include "src/Logger/BootLogger.h"
#include "src/Diagnostic/Diagnostic.h"
#include "src/Communication/SerialCommandHandler.h"

// === Behavior Engine ===
#include "src/Behavior/BehaviorScheduler.h"
#include "src/Behavior/MoveForwardBehavior.h"
#include "src/Behavior/MoveBackwardBehavior.h"
#include "src/Behavior/TurnLeftBehavior.h"
#include "src/Behavior/TurnRightBehavior.h"
#include "src/Behavior/StopBehavior.h"
#include "src/Behavior/WaitBehavior.h"
#include "src/Behavior/TouchStopBehavior.h"
#include "src/Behavior/ObstacleStopBehavior.h"
#include "src/Behavior/LineDetectBehavior.h"
#include "src/Behavior/LightTriggerBehavior.h"
#include "src/Behavior/ColorDetectBehavior.h"

// === Diagnostics ===
#include "src/Diagnostics/DiagnosticsManager.h"
#include "src/Sensor/SensorManager.h"
#include "src/Diagnostics/Console/DevelopmentConsole.h"

// === IMU & Heading ===
#include "src/Sensor/IMUSensor.h"
#include "src/Sensor/SensorID.h"
#include "src/Services/Motion/HeadingEstimator.h"
#include "src/Services/Motion/HeadingController.h"

// VM
VM vm;
Program program;
const int STABILITY_ITERATIONS = 1;
int executionCounter = 0;

// Behavior Engine
BehaviorScheduler scheduler;
bool useBehaviorEngine = false;

// Heading Estimator (global instance)
HeadingEstimator g_headingEstimator;

// === Robot Ready State ===
bool g_robotReady = false;

void setup() {
    Serial.begin(115200);
    while (!Serial) { }

    BootLogger::log("BOOT", "Power On");

    // 1. Hardware Initialization
    RobotAPI::Initialize();
    BootLogger::log("BOOT", "Hardware Ready");

    // 2. Diagnostics
    Diagnostic::runAll();
    BootLogger::log("BOOT", "Diagnostics Complete");

    // 3. Load Program for VM
    if (!ProgramLoader::LoadFromGenerated(program)) {
        BootLogger::log("ERROR", "Failed to load program. Halted.");
        while (1) { }
    }
    BootLogger::log("BOOT", "Binary Loaded");

    vm.LoadProgram(&program);
    BootLogger::log("BOOT", "VM Ready");

    // 4. Serial Command Handler
    SerialCommandHandler::setup();
    BootLogger::log("BOOT", "Serial Handler Ready");

    DevelopmentConsole::instance().begin();
    DevelopmentConsole::instance().setEnabled(false);
    BootLogger::log("BOOT", "Development Console ready (disabled by default)");

    // 5. Initialize Behavior Scheduler with default behaviors
    scheduler.addBehavior(new MoveForwardBehavior(50, 2000));
    scheduler.addBehavior(new TouchStopBehavior(0, 50));
    scheduler.addBehavior(new WaitBehavior(1000));
    scheduler.addBehavior(new TurnLeftBehavior(50, 500));
    scheduler.addBehavior(new StopBehavior());
    scheduler.addBehavior(new ObstacleStopBehavior(50, 20));
    scheduler.addBehavior(new LineDetectBehavior(0, 50));
    scheduler.addBehavior(new LightTriggerBehavior(0, 500, 50));
    scheduler.addBehavior(new ColorDetectBehavior(0, 50));
    
    BootLogger::log("BOOT", "Behavior Scheduler initialized with 9 behaviors");

    // 6. Reset Heading Estimator
    g_headingEstimator.reset();
    BootLogger::log("BOOT", "Heading Estimator reset");

    // ============================================================
    // 7. AUTOMATIC IMU CALIBRATION (blocking)
    // ============================================================
    BootLogger::log("IMU", "Starting automatic gyro calibration...");
    BootLogger::log("IMU", "Keep robot completely still!");

    // Ensure motors are stopped
    RobotAPI::Stop();

    // Get IMU sensor
    auto* imu = static_cast<IMUSensor*>(SensorManager::instance().getSensor(SensorID::IMU));
    if (imu && imu->isReady()) {
        int result = imu->calibrateGyro(500);
        if (result == 0) {
            MPU6050Bias bias = imu->getBias();
            BootLogger::logFormat("IMU", "Calibration SUCCESS. Bias X=%.3f Y=%.3f Z=%.3f deg/s",
                                  bias.bx, bias.by, bias.bz);
            // Reset heading estimator
            g_headingEstimator.reset();
            BootLogger::log("Heading", "Estimator reset to 0 deg");
            // Reset heading controller
            RobotAPI::resetHeadingController();
            BootLogger::log("Heading", "Controller reset");
            g_robotReady = true;
            BootLogger::log("Robot", "READY");
        } else if (result == 1) {
            BootLogger::log("IMU", "Calibration FAILED: UNSTABLE (robot moved too much)");
            BootLogger::log("Robot", "NOT READY - Motors disabled");
            g_robotReady = false;
        } else {
            BootLogger::log("IMU", "Calibration FAILED: communication error");
            BootLogger::log("Robot", "NOT READY - Motors disabled");
            g_robotReady = false;
        }
    } else {
        BootLogger::log("IMU", "Sensor not available - calibration FAILED");
        BootLogger::log("Robot", "NOT READY - Motors disabled");
        g_robotReady = false;
    }

    // If calibration failed, stay in error state
    if (!g_robotReady) {
        BootLogger::log("ERROR", "System halted due to IMU calibration failure");
        while (1) {
            delay(1000);
            Serial.println("[ERROR] IMU calibration failed. Please reset or use 'imu calibrate' manually.");
        }
    }

    BootLogger::log("EXEC", "System Ready. Type 'help' for commands.");
    BootLogger::log("INFO", "Default mode: VM. Type 'mode behavior' to switch.");
}

void loop() {
    uint32_t start = micros();

    // Xử lý lệnh Serial
    SerialCommandHandler::handle();

    // Cập nhật tất cả sensor (cho diagnostics và các lần đọc sau)
    SensorManager::instance().updateAll();

    // Cập nhật thống kê diagnostics
    DiagnosticsManager::instance().updateSensors();

    // ---- Cập nhật Heading từ IMU (chỉ khi robot ready) ----
    if (g_robotReady) {
        auto* imu = static_cast<IMUSensor*>(SensorManager::instance().getSensor(SensorID::IMU));
        if (imu && imu->isReady() && imu->isCalibrated()) {
            IMUSample sample;
            if (imu->getLatestSample(sample)) {
                g_headingEstimator.update(sample);
            }
        }
        // Cập nhật Heading Hold Controller
        RobotAPI::updateMotion();
    } else {
        // Ensure motors stay stopped if not ready
        RobotAPI::Stop();
    }

    DevelopmentConsole::instance().update();

    if (useBehaviorEngine) {
        // === Chạy Behavior Engine ===
        scheduler.update();
    } else {
        // === Chạy VM ===
        if (vm.IsRunning()) {
            vm.Step();
        } else {
            uint8_t err = vm.GetErrorCode();
            if (err != 0) {
                BootLogger::logFormat("ERROR", "VM stopped with error code: %d", err);
                while (1) { }
            }
            executionCounter++;
            BootLogger::logFormat("EXEC", "Execution #%d finished", executionCounter);

            if (executionCounter < STABILITY_ITERATIONS) {
                BootLogger::log("STABILITY", "Restarting VM...");
                vm.Reset();
                vm.LoadProgram(&program);
            } else {
                BootLogger::log("STABILITY", "VM stability test completed.");
                while (1) {
                    SerialCommandHandler::handle();
                    delay(30);
                }
            }
        }
    }

    uint32_t elapsed = micros() - start;
    DiagnosticsManager::instance().recordLoopTime(elapsed);
}