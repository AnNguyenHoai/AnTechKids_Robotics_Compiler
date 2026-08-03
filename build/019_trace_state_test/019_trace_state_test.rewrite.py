while True:
    if get_trace_state(1, 1):
        set_3c_led(1, 0)
    else:
        set_3c_led(1, 1)
    wait(100)