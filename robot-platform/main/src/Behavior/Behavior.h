#ifndef BEHAVIOR_H
#define BEHAVIOR_H

#include <Arduino.h>
#include "BehaviorContext.h"

enum class BehaviorStatus {
    CREATED,
    INITIALIZED,
    RUNNING,
    COMPLETED,
    FAILED,
    INTERRUPTED,
    CANCELLED
};

class Behavior {
public:
    Behavior() : status(BehaviorStatus::CREATED) {}
    virtual ~Behavior() {}

    // Lifecycle methods (pure virtual)
    virtual void init(BehaviorContext& context) = 0;
    virtual void start(BehaviorContext& context) = 0;
    virtual void update(BehaviorContext& context) = 0;
    virtual void pause() = 0;
    virtual void resume() = 0;
    virtual void stop() = 0;
    virtual void reset() = 0;

    // Getters
    BehaviorStatus getStatus() const { return status; }
    const char* getName() const { return name; }

    // Setter (public để scheduler có thể thay đổi)
    void setStatus(BehaviorStatus s) { status = s; }

protected:
    BehaviorStatus status;
    const char* name = "Behavior";
};

#endif