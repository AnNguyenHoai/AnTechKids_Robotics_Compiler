import rcu
import _thread

def task():
    # Bật sensor LED trong 2 giây, tắt 1 giây, lặp 3 lần
    for i in range(3):
        rcu.SetLightSensorLed(1, 1)
        rcu.SetWaitForTime(2)
        rcu.SetLightSensorLed(1, 0)
        rcu.SetWaitForTime(1)

_thread.start_new_thread(task, ())
while 1:
    pass