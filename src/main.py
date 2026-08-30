"""PenCopy — Ferramenta de cópia em massa para pendrives."""

from __future__ import annotations

import sys

from PySide6.QtWidgets import QApplication

from .gui.main_window import MainWindow
from .gui import styles


def main() -> None:
    app = QApplication(sys.argv)
    app.setApplicationName("PenCopy")
    app.setStyleSheet(styles.GLOBAL_STYLE)

    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
