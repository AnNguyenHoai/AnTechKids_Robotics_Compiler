from pathlib import Path

from .base_generator import BaseGenerator


class RegistryGenerator(BaseGenerator):

    name = "Registry Generator"

    def generate(self, context):
        language = context.language
        generated = context.generated_dir
        generated.mkdir(exist_ok=True)

        output = generated / "function_registry.py"

        with open(output, "w", encoding="utf8") as f:
            f.write('"""\nAUTO GENERATED FILE\n"""\n\n')

            imports = {}
            for category_name, category in language.categories.items():
                if category_name == "internal":
                    continue
                module = category["module"]
                handler = category["handler"]
                imports[module] = handler

            for module, handler in imports.items():
                f.write(f"from compiler.handlers.{module} import {handler}\n")

            f.write("\nFUNCTION_REGISTRY = {\n")

            for category_name, category, func in language.all_functions():
                if category_name == "internal":
                    continue
                handler = category["handler"]
                f.write(f'    "{func["name"]}": {{\n')
                f.write(f'        "handler": {handler}.{func["name"]},\n')
                f.write(f'        "opcode": "{func["opcode"]}",\n')
                f.write(f'        "arguments": {len(func["args"])},\n')
                f.write(f'        "category": "{category_name}",\n')
                f.write(f'        "description": "{func["description"]}"\n')
                f.write("    },\n")

            f.write("}\n")