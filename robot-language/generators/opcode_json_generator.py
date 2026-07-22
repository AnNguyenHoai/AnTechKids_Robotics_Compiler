import json
from .base_generator import BaseGenerator


class OpcodeJsonGenerator(BaseGenerator):
    name = "Opcode JSON Generator"

    def generate(self, context):
        query = context.query
        generated = context.generated_dir
        generated.mkdir(exist_ok=True)

        output = generated / "opcode.json"
        data = {}
        for cat_name, cat, func in query.functions():
            opcode = query.opcode_of(func)
            data[opcode] = {
                "id": query.opcode_id_of(func),
                "opcode": opcode,
                "function": func["name"],
                "category": cat_name,
                "module": query.module_of(cat_name),
                "handler": query.handler_of(cat_name),
            }
        with open(output, "w", encoding="utf8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)