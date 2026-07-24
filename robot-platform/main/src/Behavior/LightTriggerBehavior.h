#ifndef LIGHT_TRIGGER_BEHAVIOR_H
#define LIGHT_TRIGGER_BEHAVIOR_H

#include "Behavior.h"

class LightTriggerBehavior : public Behavior {
public:
    LightTriggerBehavior(int channel = 0, int threshold = 500, int speed = 50);
    virtual void init(BehaviorContext& context) override;
    virtual void start(BehaviorContext& context) override;
    virtual void update(BehaviorContext& context) override;
    virtual void pause() override;
    virtual void resume() override;
    virtual void stop() override;
    virtual void reset() override;

private:
    int channel;
    int threshold;
    int speed;
    bool isMoving;
};

#endif