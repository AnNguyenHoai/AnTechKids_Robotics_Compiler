#ifndef TOUCH_STOP_BEHAVIOR_H
#define TOUCH_STOP_BEHAVIOR_H

#include "Behavior.h"

class TouchStopBehavior : public Behavior {
public:
    TouchStopBehavior(int port = 0, int speed = 50);
    virtual void init(BehaviorContext& context) override;
    virtual void start(BehaviorContext& context) override;
    virtual void update(BehaviorContext& context) override;
    virtual void pause() override;
    virtual void resume() override;
    virtual void stop() override;
    virtual void reset() override;

private:
    int port;
    int speed;
    bool isMoving;
    bool stopRequested;
};

#endif