# RobotAPI Dispatcher

This module forms the official **Platform Boundary** between the Runtime Execution Engine and the RobotAPI.

## Architecture
InstructionHandler
|
v
InstructionContext
|
v
RobotApiDispatcher <-- Platform Boundary
|
v
RobotApiMapper
|
v
IRobotApi
|
v
RobotAPI (C++ implementation)
|
v
HAL / Hardware

text

## Components

- **RobotApiRequest**: Encapsulates a runtime request (API ID, parameters, context, timestamp).
- **RobotApiResponse**: Represents the response from RobotAPI (success, return value, diagnostic, execution time).
- **RobotApiResult**: Normalized result with platform status codes and diagnostic information; can be converted to `ExecutionResult`.
- **RobotApiMapper**: Maps `ApiId` to actual `IRobotApi` method calls.
- **RobotApiDispatcher**: Main entry point; validates requests, invokes mapper, returns results.
- **IRobotApi**: Abstract interface defining all robot hardware APIs (move, stop, wait, LED, sensor, audio). Runtime never sees concrete implementation.

## Dummy Implementation

Currently, `IRobotApi` is not implemented; all methods return a dummy success response. Real hardware integration will be added in later sprints.

## Error Conversion

- `RobotApiResult::toExecutionResult()` converts platform errors to Runtime-friendly `ExecutionResult` format.
- Generic exceptions are caught and converted to `PlatformStatus::ERROR`.

## Future Extensions

- Add more API IDs and mapping logic.
- Implement real `IRobotApi` with HAL.
- Add tracing and profiling.
- Support async calls.