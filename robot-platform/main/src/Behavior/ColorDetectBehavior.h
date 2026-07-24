#ifndef COLOR_DETECT_BEHAVIOR_H
#define COLOR_DETECT_BEHAVIOR_H

#include "Behavior.h"

class ColorDetectBehavior : public Behavior {
public:
    ColorDetectBehavior(int targetColor = 0, int speed = 50);
    virtual void init(BehaviorContext& context) override;
    virtual void start(BehaviorContext& context) override;
    virtual void update(BehaviorContext& context) override;
    virtual void pause() override;
    virtual void resume() override;
    virtual void stop() override;
    virtual void reset() override;

private:
    int targetColor;
    int speed;
    bool isMoving;
};

#endif