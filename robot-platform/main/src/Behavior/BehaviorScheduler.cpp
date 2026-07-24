#include "BehaviorScheduler.h"
#include "../Logger/BootLogger.h"
#include "MoveForwardBehavior.h"
#include "TouchStopBehavior.h"
#include "WaitBehavior.h"
#include "TurnLeftBehavior.h"
#include "StopBehavior.h"
#include "ObstacleStopBehavior.h"
#include "LineDetectBehavior.h"
#include "LightTriggerBehavior.h"
#include "ColorDetectBehavior.h"
BehaviorScheduler::BehaviorScheduler()
    : currentIndex(0), isRunningFlag(false), isPaused(false) {}

BehaviorScheduler::~BehaviorScheduler() {
    clear();
}

void BehaviorScheduler::clear() {
    for (auto b : behaviors) {
        delete b;
    }
    behaviors.clear();
    currentIndex = 0;
    isRunningFlag = false;
}

void BehaviorScheduler::addBehavior(Behavior* behavior) {
    behaviors.push_back(behavior);
}

void BehaviorScheduler::start() {
    if (behaviors.empty()) {
        BootLogger::log("SCHEDULER", "No behaviors to execute.");
        return;
    }
    currentIndex = 0;
    isRunningFlag = true;
    isPaused = false;
    if (currentIndex < behaviors.size()) {
        behaviors[currentIndex]->init(context);
        behaviors[currentIndex]->start(context);
        BootLogger::logFormat("SCHEDULER", "Started behavior: %s", behaviors[currentIndex]->getName());
    }
}

void BehaviorScheduler::update() {
    if (!isRunningFlag) return;
    if (isPaused) return;

    if (currentIndex >= behaviors.size()) {
        isRunningFlag = false;
        BootLogger::log("SCHEDULER", "All behaviors completed.");
        return;
    }

    Behavior* current = behaviors[currentIndex];
    if (current == nullptr) {
        advanceToNext();
        return;
    }

    context.updateTimestamp();
    current->update(context);

    BehaviorStatus status = current->getStatus();
    if (status == BehaviorStatus::COMPLETED || status == BehaviorStatus::FAILED ||
        status == BehaviorStatus::CANCELLED || status == BehaviorStatus::INTERRUPTED) {
        BootLogger::logFormat("SCHEDULER", "Behavior %s finished with status %d", current->getName(), (int)status);
        advanceToNext();
    }
}

void BehaviorScheduler::advanceToNext() {
    currentIndex++;
    if (currentIndex < behaviors.size()) {
        behaviors[currentIndex]->init(context);
        behaviors[currentIndex]->start(context);
        BootLogger::logFormat("SCHEDULER", "Started behavior: %s", behaviors[currentIndex]->getName());
    } else {
        isRunningFlag = false;
        BootLogger::log("SCHEDULER", "All behaviors completed.");
    }
}

void BehaviorScheduler::stopAll() {
    for (auto b : behaviors) {
        b->stop();
    }
    isRunningFlag = false;
    BootLogger::log("SCHEDULER", "All behaviors stopped.");
}

void BehaviorScheduler::cancelCurrent() {
    if (currentIndex < behaviors.size()) {
        behaviors[currentIndex]->stop();
        behaviors[currentIndex]->setStatus(BehaviorStatus::CANCELLED);
        BootLogger::logFormat("SCHEDULER", "Cancelled behavior: %s", behaviors[currentIndex]->getName());
        advanceToNext();
    }
}

void BehaviorScheduler::runSingle(int index) {
    if (index < 0 || index >= (int)behaviors.size()) {
        BootLogger::log("SCHEDULER", "Invalid behavior index.");
        return;
    }
    stopAll();
    clear();

    Behavior* newBehavior = nullptr;
    switch (index) {
        case 0: newBehavior = new MoveForwardBehavior(50, 2000); break;
        case 1: newBehavior = new TouchStopBehavior(0, 50); break;
        case 2: newBehavior = new WaitBehavior(1000); break;
        case 3: newBehavior = new TurnLeftBehavior(50, 500); break;
        case 4: newBehavior = new StopBehavior(); break;
        case 5: newBehavior = new ObstacleStopBehavior(50, 20); break;
        case 6: newBehavior = new LineDetectBehavior(0, 50); break;
        case 7: newBehavior = new LightTriggerBehavior(0, 500, 50); break;
        case 8: newBehavior = new ColorDetectBehavior(0, 50); break;
        default: break;
    }
    if (newBehavior) {
        addBehavior(newBehavior);
        start();
    } else {
        BootLogger::log("SCHEDULER", "Unknown behavior index.");
    }
}

void BehaviorScheduler::logState() {
    BootLogger::logFormat("SCHEDULER", "Running: %d, Current index: %d, Total: %d",
                          isRunningFlag, currentIndex, behaviors.size());
}