from .base_generator import BaseGenerator


class OpcodeGenerator(BaseGenerator):

    name = "Opcode Generator"

    def generate(self, context):

        language = context.language
        generated = context.generated_dir

        generated.mkdir(exist_ok=True)

        output = generated / "opcode.py"

        with open(output, "w", encoding="utf8") as f:

            f.write('"""\n')
            f.write("AUTO GENERATED FILE\n")
            f.write('"""\n\n')

            f.write("from enum import IntEnum\n\n")

            f.write("class Opcode(IntEnum):\n")

            for _, _, function in language.all_functions():

                f.write(
                    f"    {function['opcode']} = {function['opcode_id']}\n"
                )