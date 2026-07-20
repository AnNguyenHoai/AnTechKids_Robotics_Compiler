from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from language import RobotLanguage

lang = RobotLanguage()

generated = ROOT / "generated"
generated.mkdir(exist_ok=True)

with open(
    generated / "function_registry.py",
    "w",
    encoding="utf8"
) as f:

    f.write('"""\n')
    f.write("AUTO GENERATED FILE\n")
    f.write('"""\n\n')

    imports = set()

    for _, category, _ in lang.all_functions():

        imports.add(
            (
                category["module"],
                category["handler"]
            )
        )

    for module, handler in sorted(imports):

        f.write(
            f"from compiler.handlers.{module} import {handler}\n"
        )

    f.write("\n")

    f.write("FUNCTION_REGISTRY = {\n")

    for _, category, function in lang.all_functions():

        handler = category["handler"]

        f.write(

            f'    "{function["name"]}": {handler}.{function["name"]},\n'

        )

    f.write("}\n")