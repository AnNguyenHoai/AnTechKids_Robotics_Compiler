from pathlib import Path
from .base_generator import BaseGenerator

_TYPE_MAP = {
    "int": "int",
    "string": "str",
    "bool": "bool",
    "any": "Any",
}


class SDKGenerator(BaseGenerator):
    name = "SDK Generator"

    def generate(self, context):
        query = context.query
        robot_dir = context.root / "robot"
        robot_dir.mkdir(exist_ok=True)

        module_names = []
        function_names = []

        for cat_name, cat in query.categories().items():
            if cat_name == "internal":
                continue
            module_names.append(cat_name)
            for func in cat.get("functions", []):
                function_names.append(func["name"])
            self._generate_module(robot_dir / f"{cat_name}.py", cat_name, cat, query)

        self._generate_init(robot_dir / "__init__.py", module_names, function_names)
        print(f"[SDKGenerator] Generated SDK in {robot_dir}")

    @staticmethod
    def _python_type(spec_type):
        try:
            return _TYPE_MAP[spec_type]
        except KeyError as exc:
            raise ValueError(f"Unsupported Robot Language type: {spec_type!r}") from exc

    def _generate_module(self, filepath, category_name, category, query):
        functions = category.get("functions", [])
        uses_any = any(
            arg.get("type") == "any" for func in functions for arg in query.arguments_of(func)
        ) or any(func.get("returns") == "any" for func in functions)

        with open(filepath, "w", encoding="utf-8") as f:
            f.write('"""\n')
            f.write(f"AUTO GENERATED FILE – {category_name.capitalize()} API\n")
            f.write('"""\n')
            if uses_any:
                f.write("\nfrom typing import Any\n")
            f.write("\n")

            for func in functions:
                args = []
                for arg in query.arguments_of(func):
                    arg_type = self._python_type(arg.get("type", "int"))
                    args.append(f"{arg['name']}: {arg_type}")

                return_type = self._python_type(func["returns"]) if "returns" in func else "None"
                signature = f"def {func['name']}({', '.join(args)}) -> {return_type}:"

                doc_lines = ['    """', f"    {query.description_of(func)}", ""]
                if args:
                    doc_lines.append("    Args:")
                    for arg in query.arguments_of(func):
                        doc_lines.append(
                            f"        {arg['name']} ({arg.get('type', 'int')}):"
                        )
                doc_lines.append('    """')

                f.write(f"{signature}\n")
                f.write("\n".join(doc_lines) + "\n")
                f.write("    pass\n\n")

    def _generate_init(self, filepath, module_names, function_names):
        with open(filepath, "w", encoding="utf-8") as f:
            f.write('"""\n')
            f.write("Robot Standard API Package (AUTO GENERATED)\n")
            f.write("\n")
            f.write("This package is generated from specification/api.yaml.\n")
            f.write("DO NOT EDIT MANUALLY.\n")
            f.write('"""\n\n')

            for mod in module_names:
                f.write(f"from .{mod} import *\n")

            f.write("\n")
            f.write(f"__all__ = {function_names}\n")
            f.write('\n__version__ = "1.0.0"\n')