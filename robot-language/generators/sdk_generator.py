from pathlib import Path
from .base_generator import BaseGenerator


class SDKGenerator(BaseGenerator):
    name = "SDK Generator"

    def generate(self, context):
        language = context.language
        # Sinh vào thư mục robot/ (ở gốc robot-language)
        robot_dir = context.root / "robot"
        robot_dir.mkdir(exist_ok=True)

        # Danh sách các module đã sinh (để tạo __all__)
        module_names = []

        # Sinh module cho từng category (bỏ qua internal)
        for category_name, category in language.categories.items():
            if category_name == "internal":
                continue

            filename = robot_dir / f"{category_name}.py"
            self._generate_module(filename, category_name, category)
            module_names.append(category_name)

        # Sinh __init__.py
        self._generate_init(robot_dir / "__init__.py", module_names)

        print(f"[SDKGenerator] Generated SDK in {robot_dir}")

    def _generate_module(self, filepath: Path, category_name: str, category: dict):
        """Sinh một module Python cho một category."""
        with open(filepath, "w", encoding="utf-8") as f:
            # Header
            f.write('"""\n')
            f.write(f"AUTO GENERATED FILE – {category_name.capitalize()} API\n")
            f.write('"""\n\n')

            # Hàm
            for func in category["functions"]:
                # Xây dựng signature với type hints
                args = []
                for arg in func["args"]:
                    arg_type = arg.get("type", "int")  # mặc định int
                    args.append(f"{arg['name']}: {arg_type}")

                signature = f"def {func['name']}({', '.join(args)}) -> None:"

                # Docstring
                doc_lines = [
                    f'    """',
                    f"    {func.get('description', '')}",
                    "",
                ]
                if func["args"]:
                    doc_lines.append("    Args:")
                    for arg in func["args"]:
                        doc_lines.append(f"        {arg['name']} ({arg.get('type', 'int')}):")
                doc_lines.append('    """')

                # Thân hàm
                f.write(f"{signature}\n")
                f.write("\n".join(doc_lines) + "\n")
                f.write("    pass\n\n")

    def _generate_init(self, filepath: Path, module_names: list):
        """Sinh __init__.py với export toàn bộ API."""
        with open(filepath, "w", encoding="utf-8") as f:
            f.write('"""\n')
            f.write("Robot Standard API Package (AUTO GENERATED)\n")
            f.write("\n")
            f.write("This package is generated from specification/api.yaml.\n")
            f.write("DO NOT EDIT MANUALLY.\n")
            f.write('"""\n\n')

            # Import từ các module
            for mod in module_names:
                f.write(f"from .{mod} import *\n")

            f.write("\n")

            # __all__
            # Chúng ta không thể biết trước danh sách hàm, nhưng có thể lấy từ các module.
            # Hoặc đơn giản là export tất cả (không cần __all__) – nhưng yêu cầu có __all__.
            # Cách đơn giản: thu thập tất cả tên hàm từ các category không internal.
            # Nhưng để đơn giản, chúng ta có thể đặt __all__ = [] và bổ sung trong generator.
            # Thay vì phức tạp, chúng ta có thể liệt kê tất cả function names từ spec.
            # Cách khác: không cần __all__ vì import * đã hoạt động.
            # Nhưng để đúng yêu cầu, chúng ta sẽ tạo __all__ động.
            # Ở đây, vì đã import *, __all__ không cần thiết, nhưng vẫn sinh để đúng.

            # Lấy tất cả function names từ spec (qua context)
            # context không có sẵn ở đây, nên chúng ta truyền vào hoặc lấy từ language.
            # Tuy nhiên, để đơn giản, ta có thể bỏ qua __all__ vì import * đã hoạt động.
            # Nhưng yêu cầu task có sinh __all__, vì vậy ta sẽ tạo danh sách hàm từ language.
            # Ta cần truyền language vào, nhưng hiện tại không có. Có thể sửa lại generate để truyền danh sách hàm.
            # Để tránh phức tạp, ta sẽ bỏ __all__ hoặc tạo sau.
            # Tôi sẽ thêm __all__ với danh sách hàm được truyền vào từ bên ngoài.

            # Vì generate_init được gọi từ generate, ta có thể lấy danh sách hàm từ language.
            # Tuy nhiên, để đơn giản, tôi sẽ bổ sung tham số function_names.
            # Nhưng tạm thời bỏ qua __all__, vì import * đã đủ.
            # Có thể thêm __all__ = [] và comment.

        # Ghi đè bằng cách khác: thêm __all__ với danh sách các hàm.
        # Tôi sẽ sửa lại phương pháp: thu thập function names từ language trong generate, và truyền vào.
        # Để đảm bảo, tôi sẽ sửa generate để gọi _generate_init với danh sách function names.

    # Sửa generate để thu thập function names
    def generate(self, context):
        language = context.language
        robot_dir = context.root / "robot"
        robot_dir.mkdir(exist_ok=True)

        module_names = []
        function_names = []

        for category_name, category in language.categories.items():
            if category_name == "internal":
                continue
            module_names.append(category_name)
            # Thu thập tên hàm
            for func in category["functions"]:
                function_names.append(func["name"])

            # Sinh module
            self._generate_module(robot_dir / f"{category_name}.py", category_name, category)

        # Sinh __init__ với đầy đủ __all__
        self._generate_init(robot_dir / "__init__.py", module_names, function_names)

        print(f"[SDKGenerator] Generated SDK in {robot_dir}")

    def _generate_init(self, filepath: Path, module_names: list, function_names: list):
        """Sinh __init__.py với export và __all__."""
        with open(filepath, "w", encoding="utf-8") as f:
            f.write('"""\n')
            f.write("Robot Standard API Package (AUTO GENERATED)\n")
            f.write("\n")
            f.write("This package is generated from specification/api.yaml.\n")
            f.write("DO NOT EDIT MANUALLY.\n")
            f.write('"""\n\n')

            # Import từ các module
            for mod in module_names:
                f.write(f"from .{mod} import *\n")

            f.write("\n")
            f.write(f"__all__ = {function_names}\n")

            # Thêm version
            f.write('\n__version__ = "1.0.0"\n')