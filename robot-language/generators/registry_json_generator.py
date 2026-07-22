import json
from .base_generator import BaseGenerator


class RegistryJsonGenerator(BaseGenerator):
    name = "Registry JSON Generator"

    def generate(self, context):
        query = context.query
        output = context.generated_dir / "registry.json"
        registry = {}

        for cat_name, cat, func in query.functions():
            registry[func["name"]] = {
                "opcode": query.opcode_of(func),
                "opcode_id": query.opcode_id_of(func),
                "category": cat_name,
                "module": query.module_of(cat_name),
                "handler": query.handler_of(cat_name),
                "arguments": query.argument_count_of(func),
                "description": query.description_of(func),
            }

        with open(output, "w", encoding="utf8") as f:
            json.dump(registry, f, indent=4, ensure_ascii=False)