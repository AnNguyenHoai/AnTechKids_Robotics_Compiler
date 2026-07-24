# integration/end_to_end/programs/demo_sensor.py
import rcu

# Giả sử có một sensor đọc line
# Trong RoboSim thực tế, sẽ có API đọc sensor, nhưng để demo ta dùng biến
# Vì chưa có API sensor trong RoboSim spec, ta sẽ dùng biến để mô phỏng
# Thay vì đó, ta sẽ đọc biến 'sensor_value' đã được set trong test
# Nhưng để test pipeline, ta có thể dùng một hàm giả lập.

# Ở đây ta dùng lệnh gán và so sánh để mô phỏng logic sensor
sensor = 512
if sensor > 300:
    rcu.SetMoveRun("forward", 50)
else:
    rcu.SetMoveRun("backward", 30)
rcu.SetMoveStop()