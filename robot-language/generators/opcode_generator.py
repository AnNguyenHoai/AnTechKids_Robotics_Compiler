from .base_generator import BaseGenerator


class OpcodeGenerator(BaseGenerator):
    name = "Opcode Generator"

    def generate(self, context):
        query = context.query
        generated = context.generated_dir
        generated.mkdir(exist_ok=True)

        output = generated / "opcode.py"
        with open(output, "w", encoding="utf8") as f:
            f.write('"""\nAUTO GENERATED FILE\n"""\n\n')
            f.write("from enum import IntEnum\n\n")
            f.write("class Opcode(IntEnum):\n")
            for _, _, func in query.functions():
                opcode = query.opcode_of(func)
                opcode_id = query.opcode_id_of(func)
                f.write(f"    {opcode} = {opcode_id}\n")