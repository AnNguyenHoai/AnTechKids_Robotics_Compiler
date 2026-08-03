while True:
    raw = get_trace_raw(1)
    if raw == 1:
        set_3c_led(1, 1)
    else:
        set_3c_led(1, 0)
    wait(50)