# Compiler Function Registry

**Version:** 1.0  
**Status:** Complete  
**Date:** 2026-08-09

## Overview

The Function Registry is the single source of truth for all RoboSim APIs recognized by the compiler. It maps each API name to:

- Handler function (Python callable)
- Opcode
- Argument count
- Category
- Semantic classification
- Priority

---

## Registry Structure

```python
FUNCTION_REGISTRY = {
    "function_name": {
        "handler": handler_function,
        "opcode": "OpcodeName",
        "arguments": arg_count,
        "category": "category_name",
        "semantic": "Native|Rewrite|NOP|Stub|Approximation|Dummy",
        "description": "Description",
        "priority": "P0|P1|P2|P3"
    },
    ...
}

Full Registry Table
Function	Semantic	Priority	Handler	Opcode	Args
forward	Native	P0	MotionHandler.forward	Forward	1
backward	Native	P0	MotionHandler.backward	Backward	1
turn_left	Native	P0	MotionHandler.turn_left	TurnLeft	1
turn_right	Native	P0	MotionHandler.turn_right	TurnRight	1
set_motor_speed	Native	P0	MotionHandler.set_motor_speed	SetMotorSpeed	2
set_move_initialize	Stub	P1	MotionHandler.set_move_initialize	MoveInitialize	3
set_move_run_angle	Approximation	P1	MotionHandler.set_move_run_angle	MoveRunAngle	3
wait	Native	P0	SystemHandler.wait	Wait	1
stop	Native	P0	SystemHandler.stop	Stop	0
read_ultrasonic	Native	P0	SensorHandler.read_ultrasonic	ReadUltrasonic	0
read_touch	Native	P0	SensorHandler.read_touch	ReadTouch	1
read_light	Native	P0	SensorHandler.read_light	ReadLight	1
read_color	Native	P2	SensorHandler.read_color	ReadColor	0
read_line	Native	P0	SensorHandler.read_line	ReadLine	1
get_trace_value	Dummy	P1	SensorHandler.get_trace_value	GetTraceValue	2
get_trace_state	Native	P0	SensorHandler.get_trace_state	GetTraceState	2
get_trace_raw	Native	P0	SensorHandler.get_trace_raw	GetTraceRaw	1
get_light_sensor_data	Dummy	P2	SensorHandler.get_light_sensor_data	GetLightSensorData	1
set_3c_led	Native	P0	LedHandler.set_3c_led	Set3CLed	2
set_light_sensor_led	Native	P0	LedHandler.set_light_sensor_led	SetLightSensorLed	2
set_mp3_play	Approximation	P0	PeripheralHandler.set_mp3_play	SetMp3Play	1
set_lizard	Stub	P3	PeripheralHandler.set_lizard	SetLizard	1
set_servo	Stub	P2	ServoHandler.set_servo	SetServo	2
set_seering_engine	Stub	P2	ServoHandler.set_seering_engine	SetSeeringEngine	2
set_seering_engine_time	Stub	P2	ServoHandler.set_seering_engine_time	SetSeeringEngineTime	3
set_motor	Stub	P2	MotorHandler.set_motor	SetMotor	2
set_motor_servo	Stub	P2	MotorHandler.set_motor_servo	SetMotorServo	3
set_motor_straight_angle	Stub	P1	MotorHandler.set_motor_straight_angle	SetMotorStraightAngle	4
line_basis	Native	P1	LineHandler.line_basis	LineBasis	1
line_follow	Native	P1	LineHandler.line_follow	LineFollow	1
line_stop	Native	P1	LineHandler.line_stop	LineStop	0
line_millisecond	Approximation	P1	LineHandler.line_millisecond	LineMillisecond	2
line_intersection_stop	Stub	P1	LineHandler.line_intersection_stop	LineIntersectionStop	2
line_turn_encounterline	Native	P1	LineHandler.line_turn_encounterline	LineTurnEncounterLine	3
line_for_bmp	Approximation	P2	LineHandler.line_for_bmp	LineForBmp	2
line_set_initialize	Stub	P2	LineHandler.line_set_initialize	LineSetInitialize	3
update_var	NOP	P3	GuiHandler.update_var	UpdateVar	2
display_variable	NOP	P3	GuiHandler.display_variable	DisplayVariable	1