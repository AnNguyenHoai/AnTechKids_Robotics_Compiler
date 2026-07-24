#ifndef STOP_BEHAVIOR_H
#define STOP_BEHAVIOR_H

#include "Behavior.h"

class StopBehavior : public Behavior {
public:
    StopBehavior();
    virtual void init(BehaviorContext& context) override;
    virtual void start(BehaviorContext& context) override;
    virtual void update(BehaviorContext& context) override;
    virtual void pause() override;
    virtual void resume() override;
    virtual void stop() override;
    virtual void reset() override;
};

#endif