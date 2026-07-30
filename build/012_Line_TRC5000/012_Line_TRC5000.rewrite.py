line = read_line(2)
if line:
    forward(80)
    wait(1000)
    stop()
else:
    backward(80)
    wait(1000)
    stop()