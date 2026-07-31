#ifndef MOVE_BACKWARD_BEHAVIOR_H
#define MOVE_BACKWARD_BEHAVIOR_H

#include "Behavior.h"

class MoveBackwardBehavior : public Behavior {
public:
    MoveBackwardBehavior(int speed, uint32_t  durationMs = 0);
    virtual void init(BehaviorContext& context) override;
    virtual void start(BehaviorContext& context) override;
    virtual void update(BehaviorContext& context) override;
    virtual void pause() override;
    virtual void resume() override;
    virtual void stop() override;
    virtual void reset() override;

private:
    int speed;
    uint32_t durationMs;
    uint32_t startTime;
    bool isRunning;
};

#endif