from pathlib import Path
from .generated.opcode import Opcode


class HeaderEmitter:

    def emit(self, program, output_file):
        output_file = Path(output_file)
        with open(output_file, "w", encoding="utf-8") as f:
            f.write("/******************************************************************************\n")
            f.write(" * AUTO GENERATED FILE\n")
            f.write(" *\n")
            f.write(" * DO NOT EDIT MANUALLY.\n")
            f.write(" ******************************************************************************/\n\n")
            f.write("#pragma once\n\n")
            f.write("const Instruction generatedProgram[] =\n")
            f.write("{\n")
            for ins in program.instructions:
                opcode_name = Opcode(ins.opcode).name
                f.write(
                    f"    Instruction(Opcode::{opcode_name}, {ins.p1}, {ins.p2}, {ins.p3}),\n"
                )
            f.write("};\n\n")
            f.write(f"const uint16_t generatedProgramSize = {len(program.instructions)};\n")