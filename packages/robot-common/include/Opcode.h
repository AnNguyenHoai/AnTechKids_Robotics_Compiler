#pragma once
#include <cstdint>

/**
 * Strongly typed opcode enumeration.
 * All instructions used by the compiler and VM.
 */
enum class Opcode : uint8_t {
    // Motion
    MoveRun,        ///< Start continuous movement
    MoveRunTime,    ///< Move for a specified duration
    MoveStop,       ///< Stop all motion

    // Timing
    Wait,           ///< Blocking delay (milliseconds)

    // Servo
    Servo,          ///< Set servo angle

    // Sensor
    ReadTrace,      ///< Read trace sensor

    // Control flow
    Jump,           ///< Unconditional jump
    JumpIf,         ///< Conditional jump

    // Function
    Call,           ///< Call function
    Return,         ///< Return from function

    // Thread
    ThreadStart,    ///< Start a new thread
    ThreadEnd,      ///< End current thread

    COUNT           ///< Sentinel for array size
};