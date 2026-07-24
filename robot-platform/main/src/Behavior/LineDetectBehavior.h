#ifndef LINE_DETECT_BEHAVIOR_H
#define LINE_DETECT_BEHAVIOR_H

#include "Behavior.h"

class LineDetectBehavior : public Behavior {
public:
    LineDetectBehavior(int channel = 0, int speed = 50);
    virtual void init(BehaviorContext& context) override;
    virtual void start(BehaviorContext& context) override;
    virtual void update(BehaviorContext& context) override;
    virtual void pause() override;
    virtual void resume() override;
    virtual void stop() override;
    virtual void reset() override;

private:
    int channel;
    int speed;
    bool isMoving;
};

#endif