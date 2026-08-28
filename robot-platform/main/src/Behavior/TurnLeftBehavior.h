#ifndef TURN_LEFT_BEHAVIOR_H
#define TURN_LEFT_BEHAVIOR_H

#include "Behavior.h"

class TurnLeftBehavior : public Behavior {
public:
    TurnLeftBehavior(int speed, uint16_t durationMs = 0);
    virtual void init(BehaviorContext& context) override;
    virtual void start(BehaviorContext& context) override;
    virtual void update(BehaviorContext& context) override;
    virtual void pause() override;
    virtual void resume() override;
    virtual void stop() override;
    virtual void reset() override;

private:
    int speed;
    uint16_t durationMs;
    uint32_t startTime;
    bool isRunning;
};

#endif