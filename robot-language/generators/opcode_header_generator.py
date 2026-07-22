from .base_generator import BaseGenerator


class OpcodeHeaderGenerator(BaseGenerator):
    name = "Opcode Header Generator"

    def generate(self, context):
        query = context.query
        generated = context.generated_dir
        generated.mkdir(exist_ok=True)

        output = generated / "opcode.h"
        with open(output, "w", encoding="utf8") as f:
            f.write("""
/******************************************************************************
 * AUTO GENERATED FILE
 * DO NOT EDIT MANUALLY
 ******************************************************************************/

#pragma once

#include <stdint.h>

enum class Opcode : uint8_t
{
""")
            for _, _, func in query.functions():
                opcode = query.opcode_of(func)
                opcode_id = query.opcode_id_of(func)
                f.write(f"    {opcode} = {opcode_id},\n")
            f.write("};\n")