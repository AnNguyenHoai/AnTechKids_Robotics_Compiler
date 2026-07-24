#ifndef OBSTACLE_STOP_BEHAVIOR_H
#define OBSTACLE_STOP_BEHAVIOR_H

#include "Behavior.h"

class ObstacleStopBehavior : public Behavior {
public:
    ObstacleStopBehavior(int speed = 50, int threshold = 20);
    virtual void init(BehaviorContext& context) override;
    virtual void start(BehaviorContext& context) override;
    virtual void update(BehaviorContext& context) override;
    virtual void pause() override;
    virtual void resume() override;
    virtual void stop() override;
    virtual void reset() override;

private:
    int speed;
    int threshold; // cm
    bool isMoving;
    bool stopRequested;
};

#endif