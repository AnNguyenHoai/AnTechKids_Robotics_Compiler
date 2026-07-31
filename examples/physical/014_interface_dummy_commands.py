import rcu

rcu.SetServo(1, 90)
rcu.Set3CLed(2, 1)
rcu.SetLightSensorLed(3, 0)
rcu.SetMotorStraightAngle(1, 2, 70, 360)
rcu.line_intersection_stop(70, 17)