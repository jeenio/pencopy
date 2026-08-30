"""Ecrã principal: botões de espectáculos + botão Ferramentas."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QHBoxLayout, QLabel, QPushButton, QScrollArea, QVBoxLayout, QWidget,
    QGridLayout,
)

from ..core.copier import get_folder_files, get_folder_size
from ..i18n import strings as S
from . import styles
from .widgets import ShowButton


class HomeScreen(QWidget):
    """Ecrã principal com grid de espectáculos."""

    show_selected = Signal(str, str)  # show_name, folder_path
    tools_requested = Signal()
    exit_requested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._show_buttons: list[ShowButton] = []
        self._init_ui()

    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 16, 24, 16)
        layout.setSpacing(16)

        # Header
        header = QHBoxLayout()
        title = QLabel(S.APP_TITLE)
        title.setStyleSheet(styles.SECTION_TITLE)
        header.addWidget(title)

        subtitle = QLabel(S.APP_SUBTITLE)
        subtitle.setStyleSheet(styles.INFO_TEXT)
        header.addWidget(subtitle)
        header.addStretch()

        self._tools_btn = QPushButton(S.BTN_TOOLS)
        self._tools_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._tools_btn.clicked.connect(self.tools_requested.emit)
        header.addWidget(self._tools_btn)

        self._exit_btn = QPushButton(S.BTN_EXIT)
        self._exit_btn.setStyleSheet(styles.BTN_SECONDARY)
        self._exit_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._exit_btn.clicked.connect(self.exit_requested.emit)
        header.addWidget(self._exit_btn)

        layout.addLayout(header)

        # Área de scroll para os botões
        self._scroll = QScrollArea()
        self._scroll.setWidgetResizable(True)
        self._scroll.setFrameShape(QScrollArea.Shape.NoFrame)

        self._grid_widget = QWidget()
        self._grid_layout = QGridLayout(self._grid_widget)
        self._grid_layout.setSpacing(16)
        self._grid_layout.setContentsMargins(0, 0, 0, 0)

        self._scroll.setWidget(self._grid_widget)
        layout.addWidget(self._scroll, 1)

        # Mensagem quando não há espectáculos
        self._empty_label = QLabel(S.HOME_NO_SHOWS)
        self._empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._empty_label.setStyleSheet(
            f"font-size: 16px; color: {styles.TEXT_SECONDARY}; padding: 40px;"
        )
        layout.addWidget(self._empty_label)

        # Botão seguinte
        bottom = QHBoxLayout()
        bottom.addStretch()
        self._next_btn = QPushButton(S.BTN_NEXT)
        self._next_btn.setStyleSheet(styles.BTN_PRIMARY)
        self._next_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._next_btn.setEnabled(False)
        self._next_btn.clicked.connect(self._on_next)
        bottom.addWidget(self._next_btn)
        layout.addLayout(bottom)

        # Créditos
        credits_label = QLabel("Desenvolvido por Jorge A. Silva")
        credits_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        credits_label.setStyleSheet(
            f"font-size: 11px; color: {styles.TEXT_SECONDARY}; padding: 4px 0;"
        )
        layout.addWidget(credits_label)

    def load_shows(self, shows: list[dict]) -> None:
        """
        Carrega os espectáculos configurados.

        Args:
            shows: Lista de dicts com {"name": str, "path": str}
        """
        # Limpar botões existentes
        for btn in self._show_buttons:
            btn.deleteLater()
        self._show_buttons.clear()

        # Limpar layout
        while self._grid_layout.count():
            item = self._grid_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        has_shows = bool(shows)
        self._empty_label.setVisible(not has_shows)
        self._scroll.setVisible(has_shows)
        self._next_btn.setEnabled(False)

        if not has_shows:
            return

        # Criar botões em grid (3 colunas)
        cols = 3
        for i, show in enumerate(shows):
            folder = Path(show["path"])
            if folder.exists():
                files = get_folder_files(folder)
                file_count = len(files)
                total_size = sum(f.stat().st_size for f in files)
            else:
                file_count = 0
                total_size = 0

            btn = ShowButton(show["name"], file_count, total_size)
            btn.setProperty("folder_path", show["path"])
            btn.clicked.connect(self._on_show_clicked)
            self._grid_layout.addWidget(btn, i // cols, i % cols)
            self._show_buttons.append(btn)

    def _on_show_clicked(self) -> None:
        """Quando um botão de espectáculo é clicado."""
        sender = self.sender()
        if not isinstance(sender, ShowButton):
            return

        # Desmarcar os outros botões (só um seleccionado de cada vez)
        for btn in self._show_buttons:
            if btn is not sender:
                btn.setChecked(False)

        self._next_btn.setEnabled(sender.isChecked())

    def _on_next(self) -> None:
        """Avança para o ecrã de selecção de pens."""
        for btn in self._show_buttons:
            if btn.isChecked():
                folder_path = btn.property("folder_path")
                self.show_selected.emit(btn.show_name, folder_path)
                return

    def get_selected_show(self) -> tuple[str, str] | None:
        """Devolve (nome, path) do espectáculo seleccionado, ou None."""
        for btn in self._show_buttons:
            if btn.isChecked():
                return btn.show_name, btn.property("folder_path")
        return None
