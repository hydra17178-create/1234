"""Главное окно учебного приложения «Книжный клуб»."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QBrush, QColor, QCloseEvent
from PyQt6.QtWidgets import (
    QAbstractItemView,
    QApplication,
    QFormLayout,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPlainTextEdit,
    QSizePolicy,
    QSpinBox,
    QSplitter,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from .models import Book
from .services import BookService, SessionReportService
from .widgets import (
    AvailableCheckBox,
    BooksTable,
    ClubButton,
    ClubComboBox,
    ClubLineEdit,
    DangerButton,
    NotesEditor,
    RatingSpinBox,
    SearchLineEdit,
    SectionBox,
    YearSpinBox,
)


class BookClubMainWindow(QMainWindow):
    """Окно каталога; ``closeEvent`` сохраняет обязательный отчёт сессии."""

    COLUMN_COUNT = 8

    def __init__(
        self,
        service: BookService,
        login: str,
        time_in: datetime,
        report_path: Path,
    ) -> None:
        super().__init__()
        self._service = service
        self._login = login
        self._time_in = time_in
        self._report_path = report_path
        self._report_saved = False

        self.setWindowTitle("Книжный клуб")
        self.setMinimumSize(1080, 700)
        self.resize(1280, 790)
        self.setObjectName("mainWindow")

        self._build_interface()
        self._connect_signals()
        self._apply_style()
        self._reload_categories()
        self.refresh_books()

    def _build_interface(self) -> None:
        central = QWidget()
        central.setObjectName("centralPanel")
        self.setCentralWidget(central)

        root = QVBoxLayout(central)
        root.setContentsMargins(24, 20, 24, 18)
        root.setSpacing(16)
        root.addLayout(self._build_header())
        root.addWidget(self._build_filters())
        root.addWidget(self._build_content(), 1)

        self.statusBar().showMessage("Каталог готов к работе")

    def _build_header(self) -> QHBoxLayout:
        title_block = QVBoxLayout()
        title_block.setSpacing(2)
        title = QLabel("Книжный клуб")
        title.setObjectName("pageTitle")
        subtitle = QLabel("Домашняя библиотека и журнал выдачи")
        subtitle.setObjectName("pageSubtitle")
        title_block.addWidget(title)
        title_block.addWidget(subtitle)

        self.user_label = QLabel(f"Пользователь: {self._login}")
        self.user_label.setObjectName("userPill")
        self.user_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        layout = QHBoxLayout()
        layout.addLayout(title_block)
        layout.addStretch(1)
        layout.addWidget(self.user_label)
        return layout

    def _build_filters(self) -> SectionBox:
        box = SectionBox("Поиск и фильтры")
        box.setObjectName("filterBox")
        grid = QGridLayout(box)
        grid.setContentsMargins(16, 18, 16, 14)
        grid.setHorizontalSpacing(12)
        grid.setVerticalSpacing(8)

        self.search_edit = SearchLineEdit()
        self.search_edit.setPlaceholderText("Название, автор или описание")
        self.search_edit.setClearButtonEnabled(True)
        self.search_edit.setAccessibleName("Поиск книг")

        self.category_combo = ClubComboBox()
        self.category_combo.setMinimumWidth(170)

        self.min_rating_spin = RatingSpinBox()
        self.min_rating_spin.setRange(0.0, 5.0)
        self.min_rating_spin.setSingleStep(0.5)
        self.min_rating_spin.setDecimals(1)
        self.min_rating_spin.setSuffix(" / 5")
        self.min_rating_spin.setValue(0.0)

        self.available_only_check = AvailableCheckBox("Только доступные")
        self.available_only_check.setToolTip("Показываются все книги")

        self.sort_combo = ClubComboBox()
        self.sort_combo.addItem("Название: А–Я", ("title", False))
        self.sort_combo.addItem("Автор: А–Я", ("author", False))
        self.sort_combo.addItem("Сначала новые", ("year", True))
        self.sort_combo.addItem("Сначала высокий рейтинг", ("rating", True))
        self.sort_combo.addItem("Сначала объёмные", ("pages", True))

        self.reset_filters_button = ClubButton("Сбросить")
        self.reset_filters_button.setStatusTip("Очистить поиск и вернуть исходные фильтры")

        grid.addWidget(QLabel("Поиск"), 0, 0)
        grid.addWidget(QLabel("Категория"), 0, 1)
        grid.addWidget(QLabel("Рейтинг от"), 0, 2)
        grid.addWidget(QLabel("Сортировка"), 0, 4)
        grid.addWidget(self.search_edit, 1, 0)
        grid.addWidget(self.category_combo, 1, 1)
        grid.addWidget(self.min_rating_spin, 1, 2)
        grid.addWidget(self.available_only_check, 1, 3)
        grid.addWidget(self.sort_combo, 1, 4)
        grid.addWidget(self.reset_filters_button, 1, 5)
        grid.setColumnStretch(0, 3)
        grid.setColumnStretch(1, 1)
        grid.setColumnStretch(4, 1)
        return box

    def _build_content(self) -> QSplitter:
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setChildrenCollapsible(False)
        splitter.addWidget(self._build_catalog_panel())
        splitter.addWidget(self._build_add_form())
        splitter.setStretchFactor(0, 4)
        splitter.setStretchFactor(1, 2)
        splitter.setSizes((820, 380))
        return splitter

    def _build_catalog_panel(self) -> QWidget:
        panel = QWidget()
        panel.setObjectName("catalogPanel")
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 8, 0)
        layout.setSpacing(10)

        self.books_table = BooksTable(0, self.COLUMN_COUNT)
        self.books_table.setHorizontalHeaderLabels(
            (
                "№",
                "Название",
                "Автор",
                "Год",
                "Категория",
                "Страниц",
                "Рейтинг",
                "Статус",
            )
        )
        self.books_table.setAlternatingRowColors(True)
        self.books_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.books_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.books_table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.books_table.setSortingEnabled(False)
        self.books_table.verticalHeader().setVisible(False)
        self.books_table.setShowGrid(False)
        self.books_table.setMinimumHeight(300)
        header = self.books_table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.books_table, 1)

        action_row = QHBoxLayout()
        action_row.setSpacing(8)
        self.availability_button = ClubButton("Выдать книгу")
        self.availability_button.setEnabled(False)
        self.availability_button.setStatusTip("Изменить состояние выбранной книги")
        self.delete_button = DangerButton("Удалить")
        self.delete_button.setEnabled(False)
        self.delete_button.setStatusTip("Удалить выбранную книгу из каталога")
        action_row.addWidget(self.availability_button)
        action_row.addWidget(self.delete_button)
        action_row.addStretch(1)
        self.count_label = QLabel("Показано: 0")
        self.count_label.setObjectName("mutedLabel")
        action_row.addWidget(self.count_label)
        layout.addLayout(action_row)

        details_box = SectionBox("Сведения о выбранной книге")
        details_layout = QVBoxLayout(details_box)
        details_layout.setContentsMargins(14, 16, 14, 12)
        self.details_text = QPlainTextEdit()
        self.details_text.setReadOnly(True)
        self.details_text.setPlaceholderText("Выберите строку в таблице")
        self.details_text.setMaximumHeight(130)
        self.details_text.setFrameShape(QFrame.Shape.NoFrame)
        details_layout.addWidget(self.details_text)
        layout.addWidget(details_box)
        return panel

    def _build_add_form(self) -> SectionBox:
        box = SectionBox("Добавить книгу")
        box.setObjectName("addBookBox")
        box.setMinimumWidth(330)
        box.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Expanding)
        form = QFormLayout(box)
        form.setContentsMargins(18, 20, 18, 18)
        form.setHorizontalSpacing(14)
        form.setVerticalSpacing(12)
        form.setLabelAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        form.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.AllNonFixedFieldsGrow)

        self.title_edit = ClubLineEdit()
        self.title_edit.setPlaceholderText("Название книги")
        self.title_edit.setMaxLength(120)
        self.author_edit = ClubLineEdit()
        self.author_edit.setPlaceholderText("Имя автора")
        self.author_edit.setMaxLength(100)
        self.year_spin = YearSpinBox()
        self.year_spin.setRange(0, datetime.now().year)
        self.year_spin.setSpecialValueText("Не указан")
        self.year_spin.setValue(0)
        self.new_category_edit = ClubLineEdit()
        self.new_category_edit.setPlaceholderText("Например, фантастика")
        self.new_category_edit.setMaxLength(60)
        self.pages_spin = QSpinBox()
        self.pages_spin.setRange(1, 20_000)
        self.pages_spin.setValue(250)
        self.rating_spin = RatingSpinBox()
        self.rating_spin.setRange(0.0, 5.0)
        self.rating_spin.setDecimals(1)
        self.rating_spin.setSingleStep(0.5)
        self.rating_spin.setSuffix(" / 5")
        self.rating_spin.setValue(4.0)
        self.description_edit = NotesEditor()
        self.description_edit.setPlaceholderText("Короткое описание или личная заметка")
        self.description_edit.setMaximumHeight(120)
        self.add_button = ClubButton("Добавить в каталог")
        self.add_button.setObjectName("primaryButton")
        self.add_button.setStatusTip("Проверить поля и сохранить новую книгу")

        form.addRow("Название *", self.title_edit)
        form.addRow("Автор *", self.author_edit)
        form.addRow("Год", self.year_spin)
        form.addRow("Категория *", self.new_category_edit)
        form.addRow("Страниц *", self.pages_spin)
        form.addRow("Рейтинг", self.rating_spin)
        form.addRow("Описание", self.description_edit)
        form.addRow("", self.add_button)
        return box

    def _connect_signals(self) -> None:
        self.search_edit.textChanged.connect(self.refresh_books)
        self.category_combo.currentIndexChanged.connect(self.refresh_books)
        self.min_rating_spin.valueChanged.connect(self.refresh_books)
        self.available_only_check.toggled.connect(self.refresh_books)
        self.sort_combo.currentIndexChanged.connect(self.refresh_books)
        self.reset_filters_button.clicked.connect(self.reset_filters)
        self.books_table.itemSelectionChanged.connect(self._show_selected_book)
        self.books_table.deleteRequested.connect(self.delete_selected_book)
        self.books_table.activateRequested.connect(self.toggle_selected_book)
        self.availability_button.clicked.connect(self.toggle_selected_book)
        self.delete_button.clicked.connect(self.delete_selected_book)
        self.add_button.clicked.connect(self.add_book)
        self.description_edit.editingFinished.connect(self._show_description_length)

    def _apply_style(self) -> None:
        self.setStyleSheet(
            """
            QMainWindow#mainWindow, QWidget#centralPanel {
                background: #f4f1ea;
                color: #202522;
            }
            QLabel#pageTitle {
                color: #173d33;
                font-size: 28px;
                font-weight: 700;
            }
            QLabel#pageSubtitle, QLabel#mutedLabel {
                color: #68716c;
            }
            QLabel#userPill {
                background: #e3ebe6;
                border: 1px solid #c6d4cc;
                border-radius: 15px;
                color: #294f43;
                font-weight: 600;
                padding: 7px 13px;
            }
            QGroupBox {
                background: #fffdf8;
                border: 1px solid #d9d5ca;
                border-radius: 10px;
                font-weight: 650;
                margin-top: 9px;
                padding-top: 7px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 13px;
                padding: 0 5px;
                color: #385f52;
            }
            QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox, QPlainTextEdit {
                background: #ffffff;
                border: 1px solid #cfcac0;
                border-radius: 6px;
                min-height: 30px;
                padding: 3px 7px;
                selection-background-color: #3f715f;
            }
            QLineEdit:focus, QComboBox:focus, QSpinBox:focus,
            QDoubleSpinBox:focus, QPlainTextEdit:focus {
                border: 2px solid #4d7f6e;
            }
            QTableWidget {
                background: #fffdf8;
                alternate-background-color: #f5f7f3;
                border: 1px solid #d9d5ca;
                border-radius: 8px;
                selection-background-color: #d3e3db;
                selection-color: #173d33;
            }
            QHeaderView::section {
                background: #e7ece7;
                border: none;
                border-bottom: 1px solid #cbd4ce;
                color: #294f43;
                font-weight: 650;
                padding: 8px 6px;
            }
            QPushButton {
                background: #e8ebe7;
                border: 1px solid #c6ccc8;
                border-radius: 6px;
                min-height: 32px;
                padding: 3px 14px;
            }
            QPushButton:hover { background: #dce5df; }
            QPushButton:pressed { background: #cad9d0; }
            QPushButton:disabled { color: #9b9f9c; background: #eff0ed; }
            QPushButton#primaryButton {
                background: #356b59;
                border-color: #356b59;
                color: white;
                font-weight: 650;
            }
            QPushButton#primaryButton:hover { background: #2b5c4c; }
            QStatusBar { background: #e9e5dc; color: #4f5954; }
            QSplitter::handle { background: transparent; width: 8px; }
            """
        )

    def _reload_categories(self) -> None:
        previous = self.category_combo.currentText()
        self.category_combo.blockSignals(True)
        self.category_combo.clear()
        self.category_combo.addItem("Все категории", "")
        for category in self._service.categories():
            self.category_combo.addItem(category, category)
        index = self.category_combo.findText(previous)
        self.category_combo.setCurrentIndex(index if index >= 0 else 0)
        self.category_combo.blockSignals(False)

    def _filtered_books(self) -> list[Book]:
        books = self._service.all_books()
        query = self.search_edit.text().strip()
        if query:
            books = self._service.search_books(query, books)

        category = self.category_combo.currentData()
        availability = True if self.available_only_check.isChecked() else None
        books = self._service.filter_books(
            books,
            category=category,
            min_rating=self.min_rating_spin.value(),
            is_available=availability,
        )

        sort_settings = self.sort_combo.currentData()
        if sort_settings is None:
            sort_settings = ("title", False)
        return self._service.sort_books(
            books,
            field=sort_settings[0],
            descending=sort_settings[1],
        )

    def refresh_books(self) -> None:
        selected = self._selected_book()
        selected_id = selected.id if selected is not None else None
        books = self._filtered_books()

        self.books_table.blockSignals(True)
        self.books_table.setRowCount(len(books))
        selected_row = -1
        for row, book in enumerate(books):
            id_item = QTableWidgetItem(str(book.id))
            id_item.setData(Qt.ItemDataRole.UserRole, book)
            title_item = QTableWidgetItem(book.title)
            author_item = QTableWidgetItem(book.author)
            year_item = QTableWidgetItem("—" if book.year == 0 else str(book.year))
            category_item = QTableWidgetItem(book.category)
            pages_item = QTableWidgetItem(str(book.pages))
            rating_item = QTableWidgetItem(f"{book.rating:.1f}")
            status_item = QTableWidgetItem("Доступна" if book.is_available else "Выдана")

            id_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            year_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            pages_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            rating_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            status_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            if book.is_available:
                status_item.setForeground(QBrush(QColor("#2f6d50")))
            else:
                status_item.setForeground(QBrush(QColor("#9b493f")))

            row_items = (
                id_item,
                title_item,
                author_item,
                year_item,
                category_item,
                pages_item,
                rating_item,
                status_item,
            )
            for column, item in enumerate(row_items):
                self.books_table.setItem(row, column, item)
            if selected_id == book.id:
                selected_row = row

        self.books_table.blockSignals(False)
        if books:
            self.books_table.selectRow(selected_row if selected_row >= 0 else 0)
        else:
            self.books_table.clearSelection()
            self._show_selected_book()

        total = len(self._service.all_books())
        self.count_label.setText(f"Показано: {len(books)} из {total}")
        self.statusBar().showMessage(f"В каталоге {total} книг", 3500)

    def _selected_book(self) -> Book | None:
        row = self.books_table.currentRow()
        if row < 0:
            return None
        item = self.books_table.item(row, 0)
        if item is None:
            return None
        value = item.data(Qt.ItemDataRole.UserRole)
        return value if isinstance(value, Book) else None

    def _show_selected_book(self) -> None:
        book = self._selected_book()
        has_selection = book is not None
        self.availability_button.setEnabled(has_selection)
        self.delete_button.setEnabled(has_selection)
        if book is None:
            self.availability_button.setText("Выдать книгу")
            self.details_text.clear()
            return

        self.availability_button.setText(
            "Отметить возврат" if not book.is_available else "Выдать книгу"
        )
        year = "не указан" if book.year == 0 else str(book.year)
        description = book.description.strip() or "Описание не добавлено."
        self.details_text.setPlainText(
            f"{book.title} — {book.author}\n"
            f"Категория: {book.category} · Год: {year} · "
            f"Объём: {book.pages} стр. · Рейтинг: {book.rating:.1f}/5\n\n"
            f"{description}"
        )

    def reset_filters(self) -> None:
        self.search_edit.clear()
        self.category_combo.setCurrentIndex(0)
        self.min_rating_spin.setValue(0.0)
        self.available_only_check.setChecked(False)
        self.sort_combo.setCurrentIndex(0)
        self.refresh_books()
        self.statusBar().showMessage("Фильтры сброшены", 3000)

    def _next_book_id(self) -> int:
        next_id = 1
        for book in self._service.all_books():
            if book.id >= next_id:
                next_id = book.id + 1
        return next_id

    def add_book(self) -> None:
        title = self.title_edit.text().strip()
        author = self.author_edit.text().strip()
        category = self.new_category_edit.text().strip()
        if not title or not author or not category:
            QMessageBox.warning(
                self,
                "Не заполнены поля",
                "Укажите название, автора и категорию книги.",
            )
            if not title:
                self.title_edit.setFocus()
            elif not author:
                self.author_edit.setFocus()
            else:
                self.new_category_edit.setFocus()
            return

        try:
            book = Book(
                self._next_book_id(),
                title,
                author,
                self.year_spin.value(),
                category,
                self.pages_spin.value(),
                self.rating_spin.value(),
                self.description_edit.toPlainText().strip(),
                True,
            )
            self._service.add_book(book)
        except (TypeError, ValueError) as error:
            QMessageBox.warning(self, "Книга не добавлена", str(error))
            return

        self._clear_add_form()
        self._reload_categories()
        self.refresh_books()
        self.statusBar().showMessage(f"Добавлена книга «{book.title}»", 5000)

    def _clear_add_form(self) -> None:
        self.title_edit.clear()
        self.author_edit.clear()
        self.year_spin.setValue(0)
        self.new_category_edit.clear()
        self.pages_spin.setValue(250)
        self.rating_spin.setValue(4.0)
        self.description_edit.clear()
        self.title_edit.setFocus()

    def _show_description_length(self) -> None:
        length = len(self.description_edit.toPlainText().strip())
        if length:
            self.statusBar().showMessage(f"Описание: {length} символов", 2500)

    def toggle_selected_book(self) -> None:
        book = self._selected_book()
        if book is None:
            return
        try:
            updated = self._service.toggle_availability(book.id)
        except (KeyError, ValueError) as error:
            QMessageBox.warning(self, "Статус не изменён", str(error))
            return
        self.refresh_books()
        action = "возвращена" if updated.is_available else "выдана"
        self.statusBar().showMessage(f"Книга «{updated.title}» {action}", 5000)

    def delete_selected_book(self) -> None:
        book = self._selected_book()
        if book is None:
            return
        answer = QMessageBox.question(
            self,
            "Удалить книгу?",
            f"Удалить «{book.title}» из каталога?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if answer != QMessageBox.StandardButton.Yes:
            return
        try:
            self._service.remove_book(book.id)
        except (KeyError, ValueError) as error:
            QMessageBox.warning(self, "Книга не удалена", str(error))
            return
        self._reload_categories()
        self.refresh_books()
        self.statusBar().showMessage(f"Книга «{book.title}» удалена", 5000)

    def _save_session_report(self) -> None:
        if self._report_saved:
            return
        SessionReportService.write_report(
            self._report_path,
            self._login,
            self._time_in,
            datetime.now(),
            append=False,
        )
        self._report_saved = True

    def closeEvent(self, event: QCloseEvent) -> None:
        try:
            self._save_session_report()
        except OSError as error:
            QMessageBox.warning(
                self,
                "Отчёт не сохранён",
                f"Не удалось сохранить отчёт о сессии:\n{error}",
            )
        event.accept()

        application = QApplication.instance()
        if application is not None:
            application.quit()
