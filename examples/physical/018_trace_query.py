import rcu
import _thread

def test_raw():
    while True:
        # Read raw bitmask and print
        raw = rcu.GetTraceV2I2CData(1)
        print("Raw mask:", raw)
        # Blink LED based on center sensor
        center = rcu.GetTraceV2I2CState(1, 1)
        if center:
            rcu.Set3CLed(1, 1)
        else:
            rcu.Set3CLed(1, 0)
        rcu.SetWaitForTime(0.2)

def test_value():
    while True:
        val = rcu.GetTraceV2I2C(1, 1)  # center channel
        print("Value:", val)
        rcu.SetWaitForTime(0.5)

# Uncomment one of the following to test:
# _thread.start_new_thread(test_raw, ())
# _thread.start_new_thread(test_value, ())
# Use a simple loop for demo:
test_raw()