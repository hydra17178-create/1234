"""Автоматическая самопроверка основных требований методички."""

from __future__ import annotations

import ast
import inspect
import sys
from datetime import datetime
from pathlib import Path


class RequirementChecker:
    """Запускает проверки без импорта графической библиотеки."""

    ROOT = Path(__file__).resolve().parent.parent
    PACKAGE = ROOT / "bookclub"
    REQUIRED_BOOK_METHODS = (
        "__eq__",
        "__repr__",
        "__str__",
        "__lt__",
        "__le__",
        "__len__",
    )
    REQUIRED_PROPERTIES = (
        "id",
        "title",
        "author",
        "year",
        "category",
        "pages",
        "rating",
        "description",
        "is_available",
    )
    EXPECTED_WIDGET_OVERRIDES = (
        ("ClubLineEdit", "focusInEvent"),
        ("SearchLineEdit", "keyPressEvent"),
        ("ClubComboBox", "wheelEvent"),
        ("YearSpinBox", "textFromValue"),
        ("RatingSpinBox", "textFromValue"),
        ("AvailableCheckBox", "nextCheckState"),
        ("ClubButton", "enterEvent"),
        ("DangerButton", "enterEvent"),
        ("BooksTable", "keyPressEvent"),
        ("NotesEditor", "focusOutEvent"),
        ("SectionBox", "focusInEvent"),
        ("LoginDialog", "accept"),
    )
    QT_COMPONENT_BASES = (
        "QLineEdit",
        "QComboBox",
        "QSpinBox",
        "QDoubleSpinBox",
        "QCheckBox",
        "QPushButton",
        "QTableWidget",
        "QPlainTextEdit",
        "QGroupBox",
        "QDialog",
    )

    @classmethod
    def _python_files(cls) -> list[Path]:
        files = [cls.ROOT / "main.py", cls.ROOT / "tools" / "check_requirements.py"]
        files.extend(cls.PACKAGE.rglob("*.py"))
        files.extend((cls.ROOT / "tests").rglob("*.py"))
        return sorted(path for path in files if path.exists())

    @staticmethod
    def _parse(path: Path) -> ast.Module:
        return ast.parse(path.read_text(encoding="utf-8-sig"), filename=str(path))

    @classmethod
    def _check_no_forbidden_mapping(cls) -> None:
        violations: list[str] = []
        forbidden_nodes = ("Dict", "DictComp")
        forbidden_calls = ("dict", "map")
        for path in cls._python_files():
            tree = cls._parse(path)
            for node in ast.walk(tree):
                if type(node).__name__ in forbidden_nodes:
                    violations.append(f"{path.name}:{getattr(node, 'lineno', 0)}")
                if isinstance(node, ast.Lambda):
                    violations.append(f"{path.name}:{node.lineno}:lambda")
                if (
                    isinstance(node, ast.Call)
                    and isinstance(node.func, ast.Name)
                    and node.func.id in forbidden_calls
                ):
                    violations.append(f"{path.name}:{node.lineno}")
        if violations:
            raise AssertionError("Найдены запрещенные отображения: " + ", ".join(violations))

    @classmethod
    def _check_no_free_functions(cls) -> None:
        violations: list[str] = []
        for path in cls.PACKAGE.rglob("*.py"):
            tree = cls._parse(path)
            for node in tree.body:
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    violations.append(f"{path.name}:{node.lineno}")
        if violations:
            raise AssertionError("Найдены функции вне классов: " + ", ".join(violations))

    @classmethod
    def _check_domain_model(cls) -> None:
        from bookclub.models import Book, DomainEntity

        if not inspect.isabstract(DomainEntity):
            raise AssertionError("DomainEntity должен быть абстрактным")
        if not issubclass(Book, DomainEntity):
            raise AssertionError("Book должен наследоваться от DomainEntity")

        missing_methods = [
            name for name in cls.REQUIRED_BOOK_METHODS if not callable(getattr(Book, name, None))
        ]
        if missing_methods:
            raise AssertionError("Не хватает специальных методов: " + ", ".join(missing_methods))

        missing_properties: list[str] = []
        for name in cls.REQUIRED_PROPERTIES:
            member = getattr(Book, name, None)
            if not isinstance(member, property) or member.fget is None or member.fset is None:
                missing_properties.append(name)
        if missing_properties:
            raise AssertionError("Не хватает свойств: " + ", ".join(missing_properties))

    @staticmethod
    def _check_objects_and_map() -> None:
        from bookclub.custom_map import CustomMap
        from bookclub.seed_data import SeedData

        books = SeedData.create_books()
        if len(books) < 10:
            raise AssertionError("Начальных пользовательских объектов меньше десяти")
        if len(sorted(books)) != len(books):
            raise AssertionError("Объекты книг не сортируются")

        sample: CustomMap[str, int] = CustomMap()
        sample["books"] = len(books)
        if sample["books"] != len(books):
            raise AssertionError("CustomMap не сохраняет значение")

    @classmethod
    def _check_overridden_widgets(cls) -> None:
        tree = cls._parse(cls.PACKAGE / "widgets.py")
        missing: list[str] = []
        found_bases: set[str] = set()
        class_nodes = [node for node in tree.body if isinstance(node, ast.ClassDef)]
        for class_node in class_nodes:
            for base in class_node.bases:
                if isinstance(base, ast.Name) and base.id in cls.QT_COMPONENT_BASES:
                    found_bases.add(base.id)

        for class_name, method_name in cls.EXPECTED_WIDGET_OVERRIDES:
            matching_class = next(
                (node for node in class_nodes if node.name == class_name),
                None,
            )
            if matching_class is None:
                missing.append(f"{class_name}.{method_name}")
                continue
            method_found = any(
                isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef))
                and child.name == method_name
                for child in matching_class.body
            )
            if not method_found:
                missing.append(f"{class_name}.{method_name}")

        if missing:
            raise AssertionError("Не найдены переопределения: " + ", ".join(missing))
        if len(cls.EXPECTED_WIDGET_OVERRIDES) < 10:
            raise AssertionError("Переопределенных компонентов меньше десяти")
        if len(found_bases) < 5:
            raise AssertionError("Использовано меньше пяти типов UI-компонентов")

    @classmethod
    def _check_layout_and_close_integration(cls) -> None:
        window_path = cls.PACKAGE / "main_window.py"
        source = window_path.read_text(encoding="utf-8-sig")
        layout_names = ("QVBoxLayout", "QHBoxLayout", "QGridLayout", "QFormLayout")
        if sum(name in source for name in layout_names) < 3:
            raise AssertionError("Интерфейс должен использовать layout-менеджеры")
        required_close_parts = (
            "def closeEvent",
            "self._save_session_report()",
            "SessionReportService.write_report",
        )
        if not all(part in source for part in required_close_parts):
            raise AssertionError("Закрытие окна не связано с сохранением отчета")

    @staticmethod
    def _check_report() -> None:
        from bookclub.services import SessionReportService

        time_in = datetime(2026, 10, 19, 18, 5, 7)
        time_out = datetime(2026, 10, 19, 19, 15, 17)
        report = SessionReportService.render_report("Student", time_in, time_out)
        required_fragments = (
            "login",
            "time_in",
            "time_out",
            "19.10.2026 18:05:07",
            "19.10.2026 19:15:17",
        )
        if not all(fragment in report for fragment in required_fragments):
            raise AssertionError("Формат отчета не соответствует заданию")
        lines = report.splitlines()
        if len(lines) != 5 or not lines[0].startswith("+") or lines[0] != lines[-1]:
            raise AssertionError("Отчет должен быть оформлен как ASCII-таблица")

    @classmethod
    def run(cls) -> int:
        if str(cls.ROOT) not in sys.path:
            sys.path.insert(0, str(cls.ROOT))

        checks = (
            ("нет запрещенных встроенных отображений", cls._check_no_forbidden_mapping),
            ("нет свободных функций в пакете", cls._check_no_free_functions),
            ("абстракция, свойства и специальные методы", cls._check_domain_model),
            ("объекты, сравнение и CustomMap", cls._check_objects_and_map),
            ("не менее 10 переопределенных компонентов", cls._check_overridden_widgets),
            ("layout и отчет при закрытии окна", cls._check_layout_and_close_integration),
            ("ASCII-отчет и формат времени", cls._check_report),
        )
        for title, check in checks:
            check()
            print(f"[OK] {title}")
        print("Все требования, доступные для автоматической проверки, выполнены.")
        return 0


if __name__ == "__main__":
    raise SystemExit(RequirementChecker.run())
