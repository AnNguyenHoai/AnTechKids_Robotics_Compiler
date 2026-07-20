/******************************************************************************
 * File        : Instruction.h
 *
 * Description :
 *      Robot Virtual Machine Instruction Definition.
 *
 *      Every instruction executed by the Robot VM consists of:
 *
 *          Opcode
 *          Parameter1
 *          Parameter2
 *          Parameter3
 *
 *      Prototype Version:
 *          Commit001
 *
 ******************************************************************************/

#pragma once

#include <stdint.h>

#include "Opcode.h"

/**
 * Robot VM Instruction
 *
 * Instruction Format
 *
 * +--------+--------+--------+--------+
 * | Opcode |   P1   |   P2   |   P3   |
 * +--------+--------+--------+--------+
 *
 * Prototype Note
 * ----------------
 * Every instruction has FIXED size.
 * This makes the VM implementation much simpler.
 */
struct Instruction
{
    Opcode opcode;

    int16_t p1;

    int16_t p2;

    int16_t p3;

    /**
     * Default constructor.
     */
    Instruction()
        : opcode(Opcode::Nop),
          p1(0),
          p2(0),
          p3(0)
    {
    }

    /**
     * Constructor.
     */
    Instruction(
        Opcode op,
        int16_t param1,
        int16_t param2,
        int16_t param3)
        : opcode(op),
          p1(param1),
          p2(param2),
          p3(param3)
    {
    }
};