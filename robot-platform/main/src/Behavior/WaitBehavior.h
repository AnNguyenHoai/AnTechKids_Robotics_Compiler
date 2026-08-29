#ifndef WAIT_BEHAVIOR_H
#define WAIT_BEHAVIOR_H

#include "Behavior.h"

class WaitBehavior : public Behavior {
public:
    WaitBehavior(uint32_t durationMs);
    virtual void init(BehaviorContext& context) override;
    virtual void start(BehaviorContext& context) override;
    virtual void update(BehaviorContext& context) override;
    virtual void pause() override;
    virtual void resume() override;
    virtual void stop() override;
    virtual void reset() override;

private:
    uint32_t durationMs;
    uint32_t startTime;
    bool isRunning;
};

#endif