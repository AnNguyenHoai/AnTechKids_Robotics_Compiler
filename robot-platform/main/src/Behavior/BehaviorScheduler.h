#ifndef BEHAVIOR_SCHEDULER_H
#define BEHAVIOR_SCHEDULER_H

#include <vector>
#include "Behavior.h"
#include "BehaviorContext.h"

class BehaviorScheduler {
public:
    BehaviorScheduler();
    ~BehaviorScheduler();

    void addBehavior(Behavior* behavior);
    void clear();                     // Xóa tất cả behaviors
    void start();
    void update();
    void stopAll();
    void cancelCurrent();
    void runSingle(int index);        // Chạy một behavior duy nhất
    void logState();

    bool isRunning() const { return isRunningFlag; }
    const std::vector<Behavior*>& getBehaviors() const { return behaviors; }

private:
    std::vector<Behavior*> behaviors;
    BehaviorContext context;
    size_t currentIndex;
    bool isRunningFlag;
    bool isPaused;

    void advanceToNext();
};

#endif