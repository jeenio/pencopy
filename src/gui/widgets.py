"""Componentes GUI reutilizáveis."""

from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QCheckBox, QFrame, QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QWidget,
)

from ..core.drive_detector import DriveInfo, format_size
from ..core.worker import PenStatus
from ..i18n import strings as S
from . import styles


class ShowButton(QPushButton):
    """Botão grande para um espectáculo configurado."""

    def __init__(self, name: str, file_count: int, total_size: int, parent=None):
        super().__init__(parent)
        self.show_name = name
        size_text = format_size(total_size)
        self.setText(f"{name}\n{file_count} ficheiro(s) · {size_text}")
        self.setStyleSheet(styles.BTN_SHOW)
        self.setCheckable(True)
        self.setCursor(Qt.CursorShape.PointingHandCursor)


class DriveCard(QFrame):
    """Card visual para uma pendrive detectada — linha única."""

    toggled = Signal(bool)

    def __init__(self, drive: DriveInfo, parent=None):
        super().__init__(parent)
        self.drive = drive
        self._selected = False
        self.setStyleSheet(styles.DRIVE_CARD)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 10, 12, 10)

        self._checkbox = QCheckBox()
        self._checkbox.toggled.connect(self._on_toggle)
        layout.addWidget(self._checkbox)

        # Tudo numa só linha: letra — label — tamanho
        letter = drive.letter
        label = drive.label or "Sem nome"
        total = format_size(drive.total_bytes)
        self._info_label = QLabel(
            f"<b>{letter}</b> — {label} — {total}"
        )
        self._info_label.setStyleSheet("font-size: 15px;")
        layout.addWidget(self._info_label, 1)

    def _on_toggle(self, checked: bool) -> None:
        self._selected = checked
        self.setStyleSheet(
            styles.DRIVE_CARD_SELECTED if checked else styles.DRIVE_CARD
        )
        self.toggled.emit(checked)

    def mousePressEvent(self, event) -> None:
        """Permite clicar em qualquer parte do card para seleccionar."""
        self._checkbox.setChecked(not self._checkbox.isChecked())

    @property
    def is_selected(self) -> bool:
        return self._selected

    @is_selected.setter
    def is_selected(self, value: bool) -> None:
        self._checkbox.setChecked(value)


class PenStatusWidget(QFrame):
    """Widget que mostra o estado de uma pen durante o processamento."""

    def __init__(self, drive: DriveInfo, index: int, parent=None):
        super().__init__(parent)
        self.drive = drive
        self._index = index

        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 6, 8, 6)

        self._letter_label = QLabel(f"<b>{drive.letter}</b>")
        self._letter_label.setFixedWidth(50)
        layout.addWidget(self._letter_label)

        self._status_label = QLabel(S.PROGRESS_PEN_WAITING)
        self._status_label.setStyleSheet(styles.INFO_TEXT)
        layout.addWidget(self._status_label, 1)

        self._badge = QLabel("")
        self._badge.setFixedWidth(60)
        self._badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self._badge)

    def set_status(self, status: PenStatus, detail: str = "") -> None:
        """Actualiza o estado visual da pen."""
        status_map = {
            PenStatus.WAITING: (S.PROGRESS_PEN_WAITING, styles.TEXT_SECONDARY, ""),
            PenStatus.FORMATTING: ("A formatar...", styles.WARNING, "⏳"),
            PenStatus.SCANNING: ("A verificar disco...", styles.WARNING, "🔍"),
            PenStatus.COPYING: ("A copiar...", styles.PRIMARY, "📋"),
            PenStatus.VERIFYING: ("A verificar ficheiros...", styles.PRIMARY, "✅"),
            PenStatus.OK: (S.PROGRESS_PEN_OK, styles.SUCCESS, ""),
            PenStatus.ERROR: (S.PROGRESS_PEN_ERROR, styles.ERROR, ""),
        }
        text, color, icon = status_map.get(
            status, (str(status), styles.TEXT, "")
        )
        if detail:
            text = detail
        self._status_label.setText(text)
        self._status_label.setStyleSheet(f"color: {color}; font-size: 14px;")
        self._badge.setText(icon)
        if status == PenStatus.OK:
            self._badge.setStyleSheet(
                f"background-color: {styles.SUCCESS}; color: white; "
                "border-radius: 4px; font-weight: bold; font-size: 13px;"
            )
            self._badge.setText("OK")
        elif status == PenStatus.ERROR:
            self._badge.setStyleSheet(
                f"background-color: {styles.ERROR}; color: white; "
                "border-radius: 4px; font-weight: bold; font-size: 13px;"
            )
            self._badge.setText("ERRO")
