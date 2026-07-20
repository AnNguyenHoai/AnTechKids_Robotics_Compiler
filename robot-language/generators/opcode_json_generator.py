import json

from .base_generator import BaseGenerator


class OpcodeJsonGenerator(BaseGenerator):

    name = "Opcode JSON Generator"

    def generate(self, context):

        language = context.language
        generated = context.generated_dir

        generated.mkdir(exist_ok=True)

        output = generated / "opcode.json"

        data = {}

        for category_name, category, function in language.all_functions():

            data[function["opcode"]] = {
                "id": function["opcode_id"],
                "opcode": function["opcode"],
                "function": function["name"],
                "category": category_name,
                "module": category["module"],
                "handler": category["handler"]
            }

        with open(output, "w", encoding="utf8") as f:

            json.dump(
                data,
                f,
                indent=4,
                ensure_ascii=False
            )