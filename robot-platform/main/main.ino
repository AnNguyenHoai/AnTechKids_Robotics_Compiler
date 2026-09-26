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

// === Diagnostics / Sensors ===
#include "src/Diagnostics/DiagnosticsManager.h"
#include "src/Sensor/SensorManager.h"
#include "src/Sensor/LineSensorSnapshot.h"
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
//#define DIAGNOSTIC_MANUAL_START

VM vm;
Program program;
const int STABILITY_ITERATIONS = 1;
int executionCounter = 0;

// Common reactive programs can expand to roughly 19-22 cheap bytecode work
// units when multiple branches fire. Use the smallest headroom that keeps those
// generic sensor/decision/actuator chains in one slice, while retaining the
// independent short wall-clock ceiling as the hard anti-starvation guard.
//
// VM_MAX_SLICE_DURATION_US is an engineering scheduling ceiling, NOT an
// approved physical-qualification threshold. #325 remains the evidence owner.
static constexpr uint16_t VM_WORK_UNITS_PER_FIRMWARE_CYCLE = 24;
static constexpr uint32_t VM_MAX_SLICE_DURATION_US = 2000;

// Background network work is cooperatively budgeted between indivisible
// Arduino/WiFi calls. Whole-cycle telemetry records any single-call outlier.
static constexpr uint32_t ROBOT_NETWORK_SERVICE_BUDGET_US = 500;

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
    VMRuntimeTelemetry::Reset();

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
    const uint32_t start = micros();

    // Once OTA owns the robot, actuator safety takes priority and the network
    // transaction may run without the normal background budget until reboot.
    if (RobotNetworkService::isUpdateInProgress()) {
        RobotAPI::Stop();
        RobotNetworkService::update(0);
        const uint32_t end = micros();
        VMRuntimeTelemetry::RecordFirmwareCycle(start, 0, end);
        DiagnosticsManager::instance().recordLoopTime(end - start);
        delay(1);
        return;
    }

    // CONTROL-CRITICAL PHASE
    // One firmware cycle owns one coherent line-sensor snapshot. Sampling is
    // deliberately ahead of serial/network background work so a fresh line
    // observation can reach the VM and actuator with minimum software delay.
    LineSensorSnapshot::BeginCycle();
    SensorManager::instance().updateAll();
    const auto& cycleLineSnapshot = LineSensorSnapshot::Current();
    const uint32_t lineSampleTimestampUs =
        cycleLineSnapshot.valid ? cycleLineSnapshot.timestampUs : 0u;

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
            const VMRunSliceBudget budget{
                VM_WORK_UNITS_PER_FIRMWARE_CYCLE,
                VM_MAX_SLICE_DURATION_US
            };
            const VMRunSliceResult sliceResult = vm.RunSlice(budget);
            VMRuntimeTelemetry::RecordSlice(sliceResult);
            // Never print per-slice JSON here. Qualification telemetry is RAM
            // buffered and dumped only after VM motion has stopped.
        }

        if (vm.IsRunning()) {
            g_vmTerminalReported = false;
        } else if (!g_vmTerminalReported) {
            g_vmTerminalReported = true;
#ifdef DIAGNOSTIC_MANUAL_START
            if (g_vmStarted) {
#else
            if (true) {
#endif
                RobotAPI::Stop();
                VMRuntimeTelemetry::PrintBufferedJson();

                uint8_t err = vm.GetErrorCode();
                if (err != 0) {
                    BootLogger::logFormat("ERROR", "VM stopped with error code: %d", err);
                } else {
                    executionCounter++;
                    BootLogger::logFormat("EXEC", "Execution #%d finished", executionCounter);

                    if (executionCounter < STABILITY_ITERATIONS) {
                        BootLogger::log("STABILITY", "Restarting VM...");
                        vm.Reset();
                        vm.LoadProgram(&program);
                        VMRuntimeTelemetry::Reset();
                        g_vmTerminalReported = false;
#ifdef DIAGNOSTIC_MANUAL_START
                        vm.SetRunning(false);
                        g_vmStarted = false;
                        BootLogger::log("VM-DIAG", "Waiting for manual execution again");
#endif
                    } else {
                        BootLogger::log("STABILITY", "VM stability test completed.");
                    }
                }
            }
        }
    }

    // Diagnostics observe the same cached L/C/R values sampled at cycle start.
    DiagnosticsManager::instance().updateSensors();
    LineSensorSnapshot::EndCycle();

    // BACKGROUND PHASE
    // Serial input is byte-budgeted/non-blocking and network work is
    // cooperatively budgeted between indivisible library calls. These services
    // therefore cannot sit between a fresh line sample and this cycle's VM
    // decision/actuator command.
    const bool vmRunningBeforeBackground = vm.IsRunning();
    const uint32_t backgroundStartUs = micros();
    SerialCommandHandler::handle();
    RobotNetworkService::update(ROBOT_NETWORK_SERVICE_BUDGET_US);
    if (vmRunningBeforeBackground && !vm.IsRunning()) {
        VMRuntimeTelemetry::RecordStopLatency(micros() - backgroundStartUs);
    }
    DevelopmentConsole::instance().update();

    const uint32_t end = micros();
    VMRuntimeTelemetry::RecordFirmwareCycle(start, lineSampleTimestampUs, end);
    DiagnosticsManager::instance().recordLoopTime(end - start);
}
