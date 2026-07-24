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

// VM
VM vm;
Program program;
const int STABILITY_ITERATIONS = 2;
int executionCounter = 0;

// Behavior Engine
BehaviorScheduler scheduler;
bool useBehaviorEngine = false;  // Mặc định chạy VM

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

    // 5. Initialize Behavior Scheduler with default behaviors
    // (có thể thêm bất kỳ behavior nào muốn chạy)
    // Các behavior này sẽ được dùng với lệnh "behavior start" hoặc "behavior run"
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

    BootLogger::log("EXEC", "System Ready. Type 'help' for commands.");
    BootLogger::log("INFO", "Default mode: VM. Type 'mode behavior' to switch.");
}

void loop() {
    // Xử lý lệnh Serial
    SerialCommandHandler::handle();

    if (useBehaviorEngine) {
        // === Chạy Behavior Engine ===
        scheduler.update();
        if (!scheduler.isRunning()) {
            // Nếu scheduler kết thúc, có thể ở trạng thái idle
            // Không làm gì thêm
        }
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
                // Sau khi hoàn thành test, có thể chuyển sang behavior mode nếu muốn
                // Ví dụ: useBehaviorEngine = true;
                // Hoặc để nguyên vòng lặp dừng.
                while (1) {
                        SerialCommandHandler::handle(); // vẫn xử lý Serial
                        delay(30);
                 }
            }
        }
    }
}