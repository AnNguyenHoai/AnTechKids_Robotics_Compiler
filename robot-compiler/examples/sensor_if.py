distance = read_ultrasonic()
if distance < 20:
    forward(50)
else:
    backward(50)