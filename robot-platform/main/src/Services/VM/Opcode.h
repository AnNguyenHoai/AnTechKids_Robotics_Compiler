/******************************************************************************
 * File        : Opcode.h
 *
 * Description :
 *      Robot Virtual Machine Opcode Definition.
 *
 *      Every instruction executed by the Robot VM starts with one opcode.
 *      The compiler running on PC will generate these opcodes and send them
 *      to the firmware.
 *
 *      Commit:
 *          Commit001 - VM Skeleton
 *
 ******************************************************************************/

#pragma once

#include <stdint.h>

/**
 * Robot VM Opcode
 */
enum class Opcode : uint8_t
{
    /*----------------------------------------------------------
     * System
     *----------------------------------------------------------*/
    Nop = 0,

    /*----------------------------------------------------------
     * Variable
     *----------------------------------------------------------*/

    /**
     * p1 = Variable ID
     * p2 = Constant Value
     */
    LoadConst,

    /**
     * p1 = Variable ID
     *
     * reg0 = variable[p1]
     */
    LoadVar,

    /*----------------------------------------------------------
     * Sensor
     *----------------------------------------------------------*/

    /**
     * Read sensor value and store into variable.
     *
     * p1 = Variable ID
     * p2 = Sensor ID
     */
    ReadSensor,

    /*----------------------------------------------------------
     * Compare
     *----------------------------------------------------------*/

    /**
     * flag = (reg0 < p1)
     */
    CompareLessThan,

    /**
     * flag = (reg0 > p1)
     */
    CompareGreaterThan,

    /*----------------------------------------------------------
     * Flow Control
     *----------------------------------------------------------*/

    /**
     * Jump when flag == false
     *
     * p1 = Target Instruction Index
     */
    IfFalse,

    /**
     * Jump to instruction.
     *
     * p1 = Target Instruction Index
     */
    Jump,

    /**
     * Start FOR loop.
     *
     * p1 = Loop Variable ID
     * p2 = Loop Count
     */
    ForBegin,

    /**
     * End FOR loop.
     */
    ForEnd,

    /*----------------------------------------------------------
     * Robot Motion
     *----------------------------------------------------------*/

    /**
     * Forward.
     *
     * p1 = Variable ID (Speed)
     */
    Forward,

    /**
     * Backward.
     *
     * p1 = Variable ID
     */
    Backward,

    /**
     * Turn Left.
     *
     * p1 = Variable ID
     */
    TurnLeft,

    /**
     * Turn Right.
     *
     * p1 = Variable ID
     */
    TurnRight,

    /**
     * Stop Robot.
     */
    Stop,

    /**
     * Wait.
     *
     * p1 = Delay(ms)
     */
    Wait
};