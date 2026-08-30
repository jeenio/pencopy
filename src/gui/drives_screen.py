"""Ecrã de selecção de pendrives."""

from __future__ import annotations

from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtWidgets import (
    QHBoxLayout, QLabel, QMessageBox, QPushButton, QScrollArea,
    QVBoxLayout, QWidget,
)

from ..core.drive_detector import DriveInfo, detect_usb_drives, format_size
from ..i18n import strings as S
from . import styles
from .widgets import DriveCard


class DrivesScreen(QWidget):
    """Ecrã de selecção de pendrives USB."""

    start_requested = Signal(list)  # list[DriveInfo]
    back_requested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._drive_cards: list[DriveCard] = []
        self._show_name = ""
        self._show_path = ""
        self._show_size = 0
        self._init_ui()

        # Timer para auto-refresh
        self._refresh_timer = QTimer(self)
        self._refresh_timer.timeout.connect(self.refresh_drives)
        self._refresh_timer.setInterval(2000)

    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 16, 24, 16)
        layout.setSpacing(12)

        # Header
        header = QHBoxLayout()
        self._back_btn = QPushButton(S.BTN_BACK)
        self._back_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._back_btn.clicked.connect(self.back_requested.emit)
        header.addWidget(self._back_btn)

        title = QLabel(S.DRIVES_TITLE)
        title.setStyleSheet(styles.SECTION_TITLE)
        header.addWidget(title)
        header.addStretch()
        layout.addLayout(header)

        # Info do espectáculo seleccionado
        self._show_info = QLabel()
        self._show_info.setStyleSheet(styles.INFO_TEXT)
        layout.addWidget(self._show_info)

        # Botões select all / deselect all
        btn_row = QHBoxLayout()
        self._select_all_btn = QPushButton(S.DRIVES_SELECT_ALL)
        self._select_all_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._select_all_btn.clicked.connect(self._select_all)
        btn_row.addWidget(self._select_all_btn)

        self._deselect_all_btn = QPushButton(S.DRIVES_DESELECT_ALL)
        self._deselect_all_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._deselect_all_btn.clicked.connect(self._deselect_all)
        btn_row.addWidget(self._deselect_all_btn)
        btn_row.addStretch()
        layout.addLayout(btn_row)

        # Área de scroll para os cards
        self._scroll = QScrollArea()
        self._scroll.setWidgetResizable(True)
        self._scroll.setFrameShape(QScrollArea.Shape.NoFrame)

        self._cards_widget = QWidget()
        self._cards_layout = QVBoxLayout(self._cards_widget)
        self._cards_layout.setSpacing(8)
        self._cards_layout.setContentsMargins(0, 0, 0, 0)
        self._cards_layout.addStretch()

        self._scroll.setWidget(self._cards_widget)
        layout.addWidget(self._scroll, 1)

        # Mensagem quando não há pens
        self._empty_label = QLabel(S.DRIVES_NONE)
        self._empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._empty_label.setStyleSheet(
            f"font-size: 16px; color: {styles.TEXT_SECONDARY}; padding: 40px;"
        )
        layout.addWidget(self._empty_label)

        # Botão iniciar
        bottom = QHBoxLayout()
        bottom.addStretch()
        self._start_btn = QPushButton(S.BTN_START)
        self._start_btn.setStyleSheet(styles.BTN_PRIMARY)
        self._start_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._start_btn.setEnabled(False)
        self._start_btn.clicked.connect(self._on_start)
        bottom.addWidget(self._start_btn)
        layout.addLayout(bottom)

    def set_show(self, name: str, path: str, total_size: int) -> None:
        """Define o espectáculo seleccionado."""
        self._show_name = name
        self._show_path = path
        self._show_size = total_size
        size_text = format_size(total_size)
        self._show_info.setText(f"Espectáculo: <b>{name}</b> ({size_text})")

    def start_refresh(self) -> None:
        """Inicia o auto-refresh de detecção de pens."""
        self.refresh_drives()
        self._refresh_timer.start()

    def stop_refresh(self) -> None:
        """Para o auto-refresh."""
        self._refresh_timer.stop()

    def refresh_drives(self) -> None:
        """Detecta pens e actualiza a lista de cards."""
        drives = detect_usb_drives()

        # Manter selecção existente
        previously_selected = {
            card.drive.device for card in self._drive_cards if card.is_selected
        }

        # Limpar cards existentes
        for card in self._drive_cards:
            card.deleteLater()
        self._drive_cards.clear()

        # Remover items do layout (excepto o stretch)
        while self._cards_layout.count() > 1:
            item = self._cards_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        has_drives = bool(drives)
        self._empty_label.setVisible(not has_drives)
        self._scroll.setVisible(has_drives)

        for drive in drives:
            card = DriveCard(drive)
            card.toggled.connect(self._update_start_button)
            # Restaurar selecção anterior
            if drive.device in previously_selected:
                card.is_selected = True
            self._cards_layout.insertWidget(
                self._cards_layout.count() - 1, card
            )
            self._drive_cards.append(card)

        self._update_start_button()

    def _select_all(self) -> None:
        for card in self._drive_cards:
            card.is_selected = True

    def _deselect_all(self) -> None:
        for card in self._drive_cards:
            card.is_selected = False

    def _update_start_button(self) -> None:
        selected = any(card.is_selected for card in self._drive_cards)
        self._start_btn.setEnabled(selected)

    def _on_start(self) -> None:
        """Mostra confirmação e emite sinal para iniciar."""
        selected_drives = self.get_selected_drives()
        if not selected_drives:
            return

        # Verificar espaço
        for drive in selected_drives:
            if drive.total_bytes < self._show_size:
                QMessageBox.warning(
                    self,
                    S.CONFIRM_TITLE,
                    S.ERR_DRIVE_TOO_SMALL.format(
                        letter=drive.letter,
                        size=format_size(drive.total_bytes),
                        needed=format_size(self._show_size),
                    ),
                )
                return

        # Diálogo de confirmação
        reply = QMessageBox.warning(
            self,
            S.CONFIRM_TITLE,
            S.CONFIRM_MESSAGE.format(
                count=len(selected_drives),
                show=self._show_name,
            ),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.stop_refresh()
            self.start_requested.emit(selected_drives)

    def get_selected_drives(self) -> list[DriveInfo]:
        """Devolve lista de drives seleccionadas."""
        return [card.drive for card in self._drive_cards if card.is_selected]
