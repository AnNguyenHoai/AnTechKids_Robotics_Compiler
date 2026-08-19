forward(80)
wait(200)
dist = read_ultrasonic()
if dist > 0:
    set_3c_led(1, 1)
else:
    set_3c_led(1, 0)
wait(5000)