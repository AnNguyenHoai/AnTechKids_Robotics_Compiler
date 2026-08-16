stop()
for i in range(30):
    dist = read_ultrasonic()
    if dist >= 0:
        print('ULTRA OK:', dist)
    else:
        print('ULTRA FAIL')
    wait(200)
stop()