while True:
    rcu.SetMotorSpeed(80, 80)
    dist = read_ultrasonic()
    wait(200)