from .base_generator import BaseGenerator


class RegistryGenerator(BaseGenerator):
    name = "Registry Generator"

    def generate(self, context):
        query = context.query
        generated = context.generated_dir
        generated.mkdir(exist_ok=True)

        output = generated / "function_registry.py"
        with open(output, "w", encoding="utf8") as f:
            f.write('"""\nAUTO GENERATED FILE\n"""\n\n')

            # Collect imports (one per module)
            imports = {}
            for cat_name, cat in query.categories().items():
                if cat_name == "internal":
                    continue
                module = query.module_of(cat_name)
                handler = query.handler_of(cat_name)
                imports[module] = handler

            for module, handler in imports.items():
                f.write(f"from compiler.handlers.{module} import {handler}\n")

            f.write("\nFUNCTION_REGISTRY = {\n")
            for cat_name, cat, func in query.functions():
                if cat_name == "internal":
                    continue
                handler = query.handler_of(cat_name)
                opcode = query.opcode_of(func)
                arg_count = query.argument_count_of(func)
                desc = query.description_of(func)
                f.write(f'    "{func["name"]}": {{\n')
                f.write(f'        "handler": {handler}.{func["name"]},\n')
                f.write(f'        "opcode": "{opcode}",\n')
                f.write(f'        "arguments": {arg_count},\n')
                f.write(f'        "category": "{cat_name}",\n')
                f.write(f'        "description": "{desc}"\n')
                f.write("    },\n")
            f.write("}\n")