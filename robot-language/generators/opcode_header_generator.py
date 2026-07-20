from .base_generator import BaseGenerator

class OpcodeHeaderGenerator(BaseGenerator):
    name = "Opcode Header Generator"

    def generate(self, context):
        language = context.language
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
            for _, _, func in language.all_functions():
                f.write(f"    {func['opcode']} = {func['opcode_id']},\n")

            f.write("};\n")