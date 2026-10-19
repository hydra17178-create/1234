"""Сборка объектов приложения и запуск графического интерфейса."""

from __future__ import annotations

import sys
from datetime import datetime
from pathlib import Path

from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import QApplication, QDialog

from .main_window import BookClubMainWindow
from .repository import BookRepository
from .seed_data import SeedData
from .services import BookService
from .widgets import LoginDialog


class BookClubApplication:
    """Фабрика и единая точка запуска настольного приложения."""

    @classmethod
    def run(cls) -> int:
        application = QApplication.instance()
        owns_event_loop = application is None
        if application is None:
            application = QApplication(sys.argv)

        application.setApplicationName("Книжный клуб")
        application.setOrganizationName("Учебный проект")
        application.setFont(QFont("Segoe UI", 10))

        login_dialog = LoginDialog()
        if login_dialog.exec() != QDialog.DialogCode.Accepted:
            return 0

        time_in = datetime.now()
        repository = BookRepository(SeedData.create_books())
        service = BookService(repository)
        project_root = Path(__file__).resolve().parent.parent
        report_name = f"session_report_{time_in:%Y%m%d_%H%M%S_%f}.txt"
        report_path = project_root / "reports" / report_name
        window = BookClubMainWindow(
            service=service,
            login=login_dialog.login,
            time_in=time_in,
            report_path=report_path,
        )
        window.show()

        if not owns_event_loop:
            return 0
        return application.exec()
