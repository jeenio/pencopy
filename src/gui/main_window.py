"""Janela principal com navegação entre ecrãs."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QMainWindow, QStackedWidget

from ..core.copier import get_folder_size
from ..core.drive_detector import DriveInfo
from ..i18n import strings as S
from . import styles
from .home_screen import HomeScreen
from .drives_screen import DrivesScreen
from .progress_screen import ProgressScreen
from .tools_dialog import ToolsDialog, load_config


class MainWindow(QMainWindow):
    """Janela principal da aplicação PenCopy."""

    # Índices dos ecrãs
    HOME = 0
    DRIVES = 1
    PROGRESS = 2

    def __init__(self):
        super().__init__()
        self.setWindowTitle(S.APP_TITLE)
        self.setMinimumSize(800, 600)
        self.resize(900, 650)

        # Stack de ecrãs
        self._stack = QStackedWidget()
        self.setCentralWidget(self._stack)

        # Ecrãs
        self._home = HomeScreen()
        self._drives = DrivesScreen()
        self._progress = ProgressScreen()

        self._stack.addWidget(self._home)      # 0
        self._stack.addWidget(self._drives)     # 1
        self._stack.addWidget(self._progress)   # 2

        # Estado
        self._current_show_name = ""
        self._current_show_path = ""

        # Ligações
        self._home.show_selected.connect(self._on_show_selected)
        self._home.tools_requested.connect(self._on_tools)
        self._home.exit_requested.connect(self.close)
        self._drives.back_requested.connect(self._go_home)
        self._drives.start_requested.connect(self._on_start)
        self._progress.done_requested.connect(self._go_home)

        # Carregar espectáculos
        self._reload_shows()

    def _reload_shows(self) -> None:
        """Recarrega a lista de espectáculos do config.json."""
        config = load_config()
        self._home.load_shows(config.get("shows", []))

    def _go_home(self) -> None:
        """Volta ao ecrã principal."""
        self._drives.stop_refresh()
        self._reload_shows()
        self._stack.setCurrentIndex(self.HOME)

    def _on_show_selected(self, name: str, path: str) -> None:
        """Um espectáculo foi seleccionado — avançar para selecção de pens."""
        folder = Path(path)
        if not folder.exists():
            from PySide6.QtWidgets import QMessageBox
            QMessageBox.warning(
                self, S.CONFIRM_TITLE,
                S.ERR_FOLDER_MISSING.format(path=path),
            )
            return

        total_size = get_folder_size(folder)
        if total_size == 0:
            from PySide6.QtWidgets import QMessageBox
            QMessageBox.warning(
                self, S.CONFIRM_TITLE,
                S.ERR_FOLDER_EMPTY.format(path=path),
            )
            return

        self._current_show_name = name
        self._current_show_path = path
        self._drives.set_show(name, path, total_size)
        self._drives.start_refresh()
        self._stack.setCurrentIndex(self.DRIVES)

    def _on_start(self, drives: list[DriveInfo]) -> None:
        """Iniciar o processamento."""
        self._stack.setCurrentIndex(self.PROGRESS)
        self._progress.start(
            source_folder=self._current_show_path,
            drives=drives,
            label=self._current_show_name,
        )

    def _on_tools(self) -> None:
        """Abrir diálogo de ferramentas."""
        dialog = ToolsDialog(self)
        dialog.shows_changed.connect(self._reload_shows)
        dialog.exec()
