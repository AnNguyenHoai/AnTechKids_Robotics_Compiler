# frontend/mapping.py
ROBOSIM_API = {
    "forward": "forward",
    "backward": "backward",
    "turnleft": "turn_left",
    "turnright": "turn_right",
    "left": "turn_left",
    "right": "turn_right",
}

# Sensor API mapping: authoritative definition for all RoboSim sensor adapters.
# - target: Standard Robot API function name
# - arg_indices: which arguments from RoboSim call to preserve (empty = discard all)
# - expected_args: exact number of arguments RoboSim must provide
SENSOR_API_MAPPING = {
    "GetUltrasound": {
        "target": "read_ultrasonic",
        "arg_indices": [],
        "expected_args": 1,
    },
    "GetTouch": {
        "target": "read_touch",
        "arg_indices": [0],
        "expected_args": 1,
    },
    "GetLightSensor": {
        "target": "read_light",
        "arg_indices": [0],
        "expected_args": 1,
    },
    "GetTraceV2I2CChxState": {
        "target": "read_line",
        "arg_indices": [1],
        "expected_args": 2,
    },
}