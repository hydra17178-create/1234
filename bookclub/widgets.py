"""Пользовательские компоненты интерфейса книжного клуба.

В задании требуется переопределить не менее десяти компонентов окна. Ниже
собраны небольшие, осмысленные наследники Qt-классов; каждый из них
переопределяет настоящий метод или обработчик события родителя:

1. ``ClubLineEdit.focusInEvent``;
2. ``SearchLineEdit.keyPressEvent``;
3. ``ClubComboBox.wheelEvent``;
4. ``YearSpinBox.textFromValue``;
5. ``RatingSpinBox.textFromValue``;
6. ``AvailableCheckBox.nextCheckState``;
7. ``ClubButton.enterEvent``;
8. ``DangerButton.enterEvent``;
9. ``BooksTable.keyPressEvent``;
10. ``NotesEditor.focusOutEvent``;
11. ``SectionBox.focusInEvent``;
12. ``LoginDialog.accept``.

Такое переопределение не сделано ради формального счётчика: компоненты дают
понятные подсказки, удобное управление с клавиатуры и защиту от случайного
изменения фильтров колесом мыши.
"""

from __future__ import annotations

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QEnterEvent, QFocusEvent, QKeyEvent, QWheelEvent
from PyQt6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QDoubleSpinBox,
    QFormLayout,
    QGroupBox,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPlainTextEdit,
    QPushButton,
    QSpinBox,
    QTableWidget,
    QVBoxLayout,
    QWidget,
)


class ClubLineEdit(QLineEdit):
    """Обычное поле ввода, которое выделяет содержимое при первом фокусе."""

    def focusInEvent(self, event: QFocusEvent) -> None:
        super().focusInEvent(event)
        self.selectAll()


class SearchLineEdit(ClubLineEdit):
    """Строка поиска с быстрым сбросом по клавише Escape."""

    def keyPressEvent(self, event: QKeyEvent) -> None:
        if event.key() == Qt.Key.Key_Escape:
            self.clear()
            return
        super().keyPressEvent(event)


class ClubComboBox(QComboBox):
    """Список, который не меняется случайно при прокрутке формы."""

    def wheelEvent(self, event: QWheelEvent) -> None:
        if self.hasFocus():
            super().wheelEvent(event)
            return
        event.ignore()


class YearSpinBox(QSpinBox):
    """Поле года с аккуратным отображением неизвестного значения."""

    def textFromValue(self, value: int) -> str:
        return f"{value:04d}"


class RatingSpinBox(QDoubleSpinBox):
    """Поле оценки, визуально показывающее пятибалльную шкалу."""

    def textFromValue(self, value: float) -> str:
        return self.locale().toString(value, "f", 1)


class AvailableCheckBox(QCheckBox):
    """Флажок наличия с понятной подсказкой после смены состояния."""

    def __init__(self, text: str, parent: QWidget | None = None) -> None:
        super().__init__(text, parent)
        self.toggled.connect(self._update_tooltip)
        self._update_tooltip(False)

    def _update_tooltip(self, checked: bool) -> None:
        self.setToolTip(
            "Показываются только доступные книги"
            if checked
            else "Показываются все книги"
        )

    def nextCheckState(self) -> None:
        super().nextCheckState()
        self._update_tooltip(self.isChecked())


class ClubButton(QPushButton):
    """Основная кнопка, которая сообщает назначение в строке состояния."""

    def __init__(self, text: str, parent: QWidget | None = None) -> None:
        super().__init__(text, parent)
        self._normal_status_tip = ""

    def setStatusTip(self, tip: str) -> None:
        self._normal_status_tip = tip
        super().setStatusTip(tip)

    def enterEvent(self, event: QEnterEvent) -> None:
        if self._normal_status_tip:
            self.setToolTip(self._normal_status_tip)
        super().enterEvent(event)


class DangerButton(ClubButton):
    """Кнопка необратимого действия с дополнительным предупреждением."""

    def enterEvent(self, event: QEnterEvent) -> None:
        self.setToolTip("Действие потребует подтверждения")
        QPushButton.enterEvent(self, event)


class BooksTable(QTableWidget):
    """Таблица с сигналами для Delete и Enter, удобными без мыши."""

    deleteRequested = pyqtSignal()
    activateRequested = pyqtSignal()

    def keyPressEvent(self, event: QKeyEvent) -> None:
        if event.key() == Qt.Key.Key_Delete:
            self.deleteRequested.emit()
            return
        if event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            self.activateRequested.emit()
            return
        super().keyPressEvent(event)


class NotesEditor(QPlainTextEdit):
    """Редактор заметок, сообщающий о завершении правки."""

    editingFinished = pyqtSignal()

    def focusOutEvent(self, event: QFocusEvent) -> None:
        super().focusOutEvent(event)
        self.editingFinished.emit()


class SectionBox(QGroupBox):
    """Секция формы, передающая фокус первому доступному полю."""

    def __init__(self, title: str = "", parent: QWidget | None = None) -> None:
        super().__init__(title, parent)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

    def focusInEvent(self, event: QFocusEvent) -> None:
        super().focusInEvent(event)
        candidate = self.findChild(QLineEdit)
        if candidate is not None:
            candidate.setFocus()


class LoginDialog(QDialog):
    """Редактируемый диалог входа без пароля для учебной сессии."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Вход в книжный клуб")
        self.setModal(True)
        self.setMinimumWidth(390)

        title = QLabel("Добро пожаловать")
        title.setObjectName("loginTitle")
        subtitle = QLabel("Введите имя, которое будет указано в отчёте о сессии.")
        subtitle.setWordWrap(True)

        self.login_edit = ClubLineEdit()
        self.login_edit.setPlaceholderText("Например, Анна")
        self.login_edit.setClearButtonEnabled(True)
        self.login_edit.setMaxLength(48)

        form = QFormLayout()
        form.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.AllNonFixedFieldsGrow)
        form.addRow("Имя пользователя:", self.login_edit)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok
            | QDialogButtonBox.StandardButton.Cancel
        )
        ok_button = buttons.button(QDialogButtonBox.StandardButton.Ok)
        if ok_button is not None:
            ok_button.setText("Войти")
        cancel_button = buttons.button(QDialogButtonBox.StandardButton.Cancel)
        if cancel_button is not None:
            cancel_button.setText("Отмена")
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(14)
        layout.addWidget(title)
        layout.addWidget(subtitle)
        layout.addLayout(form)
        layout.addWidget(buttons)

        self.login_edit.returnPressed.connect(self.accept)

    @property
    def login(self) -> str:
        return self.login_edit.text().strip()

    def accept(self) -> None:
        if not self.login:
            QMessageBox.warning(
                self,
                "Не указано имя",
                "Введите имя пользователя, чтобы начать работу.",
            )
            self.login_edit.setFocus()
            return
        if "|" in self.login:
            QMessageBox.warning(
                self,
                "Недопустимый символ",
                "Имя пользователя не должно содержать символ |.",
            )
            self.login_edit.setFocus()
            return
        super().accept()
