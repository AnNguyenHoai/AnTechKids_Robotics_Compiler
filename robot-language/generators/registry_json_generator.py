import json

from .base_generator import BaseGenerator


class RegistryJsonGenerator(BaseGenerator):

    name = "Registry JSON Generator"

    def generate(self, context):

        language = context.language

        output = context.generated_dir / "registry.json"

        registry = {}

        for category_name, category, func in language.all_functions():

            registry[func["name"]] = {
                "opcode": func["opcode"],
                "opcode_id": func["opcode_id"],
                "category": category_name,
                "module": category["module"],
                "handler": category["handler"],
                "arguments": len(func["args"]),
                "description": func["description"],
            }

        with open(output, "w", encoding="utf8") as f:
            json.dump(
                registry,
                f,
                indent=4,
                ensure_ascii=False,
            )