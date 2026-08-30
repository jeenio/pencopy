"""Diálogo de Ferramentas — adicionar/remover espectáculos."""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QDialog, QFileDialog, QHBoxLayout, QLabel, QListWidget, QListWidgetItem,
    QMessageBox, QPushButton, QVBoxLayout,
)

from ..i18n import strings as S
from . import styles


def get_config_path() -> Path:
    """Devolve o caminho do ficheiro de configuração."""
    if getattr(sys, "frozen", False):
        # Executável PyInstaller — guardar junto ao .exe
        base = Path(sys.executable).parent
    else:
        # Desenvolvimento — guardar na pasta do projecto
        base = Path(__file__).resolve().parent.parent.parent
    return base / "config.json"


def load_config() -> dict:
    """Carrega a configuração do ficheiro JSON."""
    path = get_config_path()
    if path.exists():
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            pass
    return {"shows": []}


def save_config(config: dict) -> None:
    """Guarda a configuração no ficheiro JSON."""
    path = get_config_path()
    path.write_text(
        json.dumps(config, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )


# Extensões de media válidas
MEDIA_EXTENSIONS = {".mp4", ".mov", ".jpg", ".jpeg", ".png", ".mkv", ".avi", ".mts", ".m2ts"}


def folder_has_media(folder: Path) -> bool:
    """Verifica se a pasta (ou subpastas) contém ficheiros multimédia."""
    for f in folder.rglob("*"):
        if f.is_file() and f.suffix.lower() in MEDIA_EXTENSIONS:
            return True
    return False


class ToolsDialog(QDialog):
    """Diálogo para gerir espectáculos configurados."""

    shows_changed = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(S.TOOLS_TITLE)
        self.setMinimumSize(500, 400)
        self._config = load_config()
        self._init_ui()
        self._load_list()

    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        title = QLabel(S.TOOLS_TITLE)
        title.setStyleSheet(styles.SECTION_TITLE)
        layout.addWidget(title)

        # Lista de espectáculos
        self._list = QListWidget()
        self._list.setStyleSheet(
            "QListWidget { border: 1px solid #E2E8F0; border-radius: 6px; }"
            "QListWidget::item { padding: 8px; }"
            "QListWidget::item:selected { background-color: #DBEAFE; }"
        )
        layout.addWidget(self._list, 1)

        # Botões
        btn_row = QHBoxLayout()

        self._back_btn = QPushButton(S.TOOLS_BACK)
        self._back_btn.setStyleSheet(styles.BTN_SECONDARY)
        self._back_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._back_btn.clicked.connect(self.accept)
        btn_row.addWidget(self._back_btn)

        btn_row.addStretch()

        self._add_btn = QPushButton(S.TOOLS_ADD)
        self._add_btn.setStyleSheet(styles.BTN_PRIMARY)
        self._add_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._add_btn.clicked.connect(self._on_add)
        btn_row.addWidget(self._add_btn)

        self._remove_btn = QPushButton(S.TOOLS_REMOVE)
        self._remove_btn.setStyleSheet(styles.BTN_DANGER)
        self._remove_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._remove_btn.setEnabled(False)
        self._remove_btn.clicked.connect(self._on_remove)
        btn_row.addWidget(self._remove_btn)

        layout.addLayout(btn_row)

        self._list.currentRowChanged.connect(
            lambda row: self._remove_btn.setEnabled(row >= 0)
        )

    def _load_list(self) -> None:
        """Carrega a lista de espectáculos na UI."""
        self._list.clear()
        for show in self._config.get("shows", []):
            name = show.get("name", "")
            path = show.get("path", "")
            item = QListWidgetItem(f"{name}\n{S.TOOLS_PATH.format(path=path)}")
            item.setData(Qt.ItemDataRole.UserRole, show)
            self._list.addItem(item)

        if not self._config.get("shows"):
            item = QListWidgetItem(S.TOOLS_EMPTY)
            item.setFlags(Qt.ItemFlag.NoItemFlags)
            self._list.addItem(item)

    def _on_add(self) -> None:
        """Adicionar um novo espectáculo."""
        folder = QFileDialog.getExistingDirectory(
            self,
            S.TOOLS_FOLDER_DIALOG,
            "",
            QFileDialog.Option.ShowDirsOnly,
        )
        if not folder:
            return

        folder_path = Path(folder)
        name = folder_path.name

        # Verificar se já existe
        shows = self._config.get("shows", [])
        for s in shows:
            if s["path"] == str(folder_path):
                return  # Já existe, ignorar

        # Validar que tem conteúdo multimédia
        if not folder_has_media(folder_path):
            reply = QMessageBox.warning(
                self,
                S.TOOLS_NO_MEDIA_TITLE,
                S.TOOLS_NO_MEDIA,
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No,
            )
            if reply != QMessageBox.StandardButton.Yes:
                return

        shows.append({"name": name, "path": str(folder_path)})
        self._config["shows"] = shows
        save_config(self._config)
        self.shows_changed.emit()
        # Fechar diálogo e voltar ao ecrã principal
        self.accept()

    def _on_remove(self) -> None:
        """Remover o espectáculo seleccionado."""
        current = self._list.currentItem()
        if not current:
            return

        show_data = current.data(Qt.ItemDataRole.UserRole)
        if not show_data:
            return

        reply = QMessageBox.question(
            self,
            S.CONFIRM_TITLE,
            S.TOOLS_CONFIRM_REMOVE.format(name=show_data["name"]),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if reply != QMessageBox.StandardButton.Yes:
            return

        shows = self._config.get("shows", [])
        shows = [s for s in shows if s["path"] != show_data["path"]]
        self._config["shows"] = shows
        save_config(self._config)
        self._load_list()
        self.shows_changed.emit()
