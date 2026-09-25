#include "include/generated/generated_device_config.h"

#include "src/Services/VM/ProgramLoader.h"
#include "src/Services/VM/VM.h"
#include "src/Services/VM/VMRuntimeTelemetry.h"
#include "src/Services/Robot/RobotAPI.h"
#include "src/Logger/BootLogger.h"
#include "src/Diagnostic/Diagnostic.h"
#include "src/Communication/SerialCommandHandler.h"
#include "src/Communication/RobotNetworkService.h"

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
#if ROBOT_FEATURE_IMU
#include "src/Sensor/IMUSensor.h"
#include "src/Sensor/SensorID.h"
#endif
#include "src/Services/Motion/HeadingEstimator.h"
#include "src/Services/Motion/HeadingController.h"

// ============================================================
// DIAGNOSTIC: Uncomment the line below to enable manual-start mode
// ============================================================
//#define DIAGNOSTIC_MANUAL_START   // <--- BẬT MACRO

VM vm;
Program program;
const int STABILITY_ITERATIONS = 1;
int executionCounter = 0;

// VM-RT G: keep VM work bounded so serial/network/OTA/sensors/motion and
// diagnostics regain control every firmware cycle. This value is deliberately
// conservative; runtime tuning belongs to the instrumentation work in #310.
static constexpr uint16_t VM_WORK_UNITS_PER_FIRMWARE_CYCLE = 4;

BehaviorScheduler scheduler;
bool useBehaviorEngine = false;

HeadingEstimator g_headingEstimator;
bool g_robotReady = false;
bool g_manualStartEnabled = false;
bool g_vmStarted = true;
bool g_vmTerminalReported = false;

void setup() {
    Serial.begin(115200);
    while (!Serial) { }

    BootLogger::log("BOOT", "Power On");

    RobotAPI::Initialize();
    BootLogger::log("BOOT", "Hardware Ready");

    Diagnostic::runAll();
    BootLogger::log("BOOT", "Diagnostics Complete");

    if (!ProgramLoader::LoadFromGenerated(program)) {
        BootLogger::log("ERROR", "Failed to load program. Halted.");
        while (1) { }
    }
    BootLogger::log("BOOT", "Binary Loaded");

    vm.LoadProgram(&program);

#ifdef DIAGNOSTIC_MANUAL_START
    g_manualStartEnabled = true;
    g_vmStarted = false;
    vm.SetRunning(false);
    BootLogger::log("VM-DIAG", "Waiting for manual execution (type 'run')");
#else
    BootLogger::log("BOOT", "VM Ready");
#endif

    SerialCommandHandler::setup();
    BootLogger::log("BOOT", "Serial Handler Ready");

    DevelopmentConsole::instance().begin();
    DevelopmentConsole::instance().setEnabled(false);
    BootLogger::log("BOOT", "Development Console ready (disabled by default)");

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

#if ROBOT_FEATURE_IMU
    g_headingEstimator.reset();
    BootLogger::log("IMU", "Heading Estimator reset");

    BootLogger::log("IMU", "Starting automatic gyro calibration...");
    BootLogger::log("IMU", "Keep robot completely still!");
    RobotAPI::Stop();

    auto* imu = static_cast<IMUSensor*>(SensorManager::instance().getSensor(SensorID::IMU));
    if (imu && imu->isReady()) {
        int result = imu->calibrateGyro(500);
        if (result == 0) {
            MPU6050Bias bias = imu->getBias();
            BootLogger::logFormat("IMU", "Calibration SUCCESS. Bias X=%.3f Y=%.3f Z=%.3f deg/s", bias.bx, bias.by, bias.bz);
            g_headingEstimator.reset();
            BootLogger::log("Heading", "Estimator reset to 0 deg");
            RobotAPI::resetHeadingController();
            BootLogger::log("Heading", "Controller reset");
            g_robotReady = true;
            BootLogger::log("Robot", "READY");
        } else if (result == 1) {
            BootLogger::log("IMU", "Calibration FAILED: UNSTABLE");
            g_robotReady = false;
        } else {
            BootLogger::log("IMU", "Calibration FAILED: communication error");
            g_robotReady = false;
        }
    } else {
        BootLogger::log("IMU", "Sensor not available - calibration FAILED");
        g_robotReady = false;
    }

    if (!g_robotReady) {
        BootLogger::log("ERROR", "System halted due to IMU calibration failure");
        while (1) {
            delay(1000);
            Serial.println("[ERROR] IMU calibration failed. Please reset or use 'imu calibrate' manually.");
        }
    }
#else
    g_robotReady = true;
    BootLogger::log("IMU", "Disabled by hardware configuration");
    BootLogger::log("Robot", "READY (no IMU / no heading hold)");
#endif

    RobotNetworkService::begin(g_robotReady);
    if (RobotNetworkService::isReady()) {
        BootLogger::logFormat("BOOT", "Network Ready: %s.local", RobotNetworkService::hostname());
    }

    BootLogger::log("EXEC", "System Ready. Type 'help' for commands.");
    BootLogger::log("INFO", "Default mode: VM. Type 'mode behavior' to switch.");
}

void loop() {
    uint32_t start = micros();

    // Firmware-cycle order is intentional: service the control plane first so
    // stop/abort/OTA can be observed before any new student-code work begins.
    const bool vmRunningBeforeControl = vm.IsRunning();
    const uint32_t controlServiceStartUs = micros();
    SerialCommandHandler::handle();
    RobotNetworkService::update();
    if (vmRunningBeforeControl && !vm.IsRunning()) {
        // Upper-bound request-to-observation window for stop/abort initiated by
        // the control-plane service phase. Qualification can aggregate max/last.
        VMRuntimeTelemetry::RecordStopLatency(micros() - controlServiceStartUs);
    }

    // During OTA, do not execute student code or drive motors. The network
    // service owns the firmware update transaction and the robot reboots when
    // the new image has been committed successfully.
    if (RobotNetworkService::isUpdateInProgress()) {
        RobotAPI::Stop();
        DiagnosticsManager::instance().recordLoopTime(micros() - start);
        delay(1);
        return;
    }

    // Platform inputs and output-control state are refreshed before RunSlice.
    // RunSlice then owns the lazy line-sensor snapshot for exactly that VM
    // control slice, so repeated line consumers share one coherent L/C/R set.
    SensorManager::instance().updateAll();
    DiagnosticsManager::instance().updateSensors();

    if (g_robotReady) {
#if ROBOT_FEATURE_IMU
        auto* imu = static_cast<IMUSensor*>(SensorManager::instance().getSensor(SensorID::IMU));
        if (imu && imu->isReady() && imu->isCalibrated()) {
            IMUSample sample;
            if (imu->getLatestSample(sample)) {
                g_headingEstimator.update(sample);
            }
        }
#endif
        RobotAPI::updateMotion();
    } else {
        RobotAPI::Stop();
    }

    DevelopmentConsole::instance().update();

    if (useBehaviorEngine) {
        scheduler.update();
    } else {
        bool runVmSlice = false;
#ifdef DIAGNOSTIC_MANUAL_START
        runVmSlice = g_vmStarted && vm.IsRunning();
#else
        runVmSlice = vm.IsRunning();
#endif

        if (runVmSlice) {
            const VMRunSliceBudget budget{VM_WORK_UNITS_PER_FIRMWARE_CYCLE};
            const VMRunSliceResult sliceResult = vm.RunSlice(budget);
            VMRuntimeTelemetry::RecordSlice(sliceResult);
            VMRuntimeTelemetry::PrintLatestJson();
        }

        if (vm.IsRunning()) {
            // A restarted/manual-started VM begins a fresh terminal-report epoch.
            g_vmTerminalReported = false;
        } else if (!g_vmTerminalReported) {
            g_vmTerminalReported = true;
#ifdef DIAGNOSTIC_MANUAL_START
            if (g_vmStarted) {
#else
            if (true) {
#endif
                uint8_t err = vm.GetErrorCode();
                if (err != 0) {
                    // Faulted student code must not trap the firmware in a
                    // private halt loop. Stop outputs, report once, and keep
                    // platform services alive on subsequent firmware cycles.
                    RobotAPI::Stop();
                    BootLogger::logFormat("ERROR", "VM stopped with error code: %d", err);
                } else {
                    executionCounter++;
                    BootLogger::logFormat("EXEC", "Execution #%d finished", executionCounter);

                    if (executionCounter < STABILITY_ITERATIONS) {
                        BootLogger::log("STABILITY", "Restarting VM...");
                        vm.Reset();
                        vm.LoadProgram(&program);
                        g_vmTerminalReported = false;
#ifdef DIAGNOSTIC_MANUAL_START
                        vm.SetRunning(false);
                        g_vmStarted = false;
                        BootLogger::log("VM-DIAG", "Waiting for manual execution again");
#endif
                    } else {
                        // Remain in the normal firmware loop after VM
                        // completion so serial/network/OTA/diagnostics remain
                        // serviceable instead of entering a nested while(1).
                        RobotAPI::Stop();
                        BootLogger::log("STABILITY", "VM stability test completed.");
                    }
                }
            }
        }
    }

    uint32_t elapsed = micros() - start;
    DiagnosticsManager::instance().recordLoopTime(elapsed);
}
