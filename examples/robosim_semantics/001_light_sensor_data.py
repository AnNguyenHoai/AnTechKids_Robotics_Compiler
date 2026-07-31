import rcu

# Test: return value for different surface colors
# Run with: black surface, white surface, gray surface

value_black = rcu.GetLightSensorData(1)
value_white = rcu.GetLightSensorData(1)
value_gray = rcu.GetLightSensorData(1)