"""Ecrã de progresso + relatório final."""

from __future__ import annotations

import time

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QHBoxLayout, QLabel, QMessageBox, QProgressBar, QPushButton,
    QScrollArea, QVBoxLayout, QWidget,
)

from ..core.drive_detector import DriveInfo, format_size
from ..core.copier import get_folder_size
from ..core.worker import CopyWorker, PenResult, PenStatus
from ..i18n import strings as S
from . import styles
from .widgets import PenStatusWidget


def _format_eta(seconds: float) -> str:
    """Formata segundos em HH:MM:SS."""
    if seconds <= 0 or seconds > 360000:
        return "--:--:--"
    h = int(seconds) // 3600
    m = (int(seconds) % 3600) // 60
    s = int(seconds) % 60
    return f"{h:02d}:{m:02d}:{s:02d}"


class ProgressScreen(QWidget):
    """Ecrã de progresso e relatório."""

    done_requested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._worker: CopyWorker | None = None
        self._pen_widgets: list[PenStatusWidget] = []
        self._total_pens = 0
        self._bytes_per_pen = 0
        self._start_time = 0.0
        self._init_ui()

    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 16, 24, 16)
        layout.setSpacing(10)

        # Título
        self._title = QLabel(S.PROGRESS_TITLE)
        self._title.setStyleSheet(styles.SECTION_TITLE)
        layout.addWidget(self._title)

        # Info + ETA
        info_row = QHBoxLayout()
        self._info_label = QLabel()
        self._info_label.setStyleSheet(styles.INFO_TEXT)
        info_row.addWidget(self._info_label, 1)

        self._eta_label = QLabel()
        self._eta_label.setStyleSheet(
            f"font-size: 16px; font-weight: 600; color: {styles.PRIMARY}; "
            "font-family: 'Consolas', 'Courier New', monospace;"
        )
        self._eta_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        info_row.addWidget(self._eta_label)
        layout.addLayout(info_row)

        # Barra de progresso de cópia
        copy_lbl = QLabel("Cópia:")
        copy_lbl.setStyleSheet("font-size: 12px; font-weight: 600;")
        layout.addWidget(copy_lbl)
        self._copy_progress = QProgressBar()
        self._copy_progress.setStyleSheet(styles.PROGRESS_BAR)
        self._copy_progress.setRange(0, 10000)
        self._copy_progress.setValue(0)
        self._copy_progress.setFormat("%p%")
        layout.addWidget(self._copy_progress)

        # Barra de progresso de verificação
        verify_lbl = QLabel("Verificação:")
        verify_lbl.setStyleSheet("font-size: 12px; font-weight: 600;")
        layout.addWidget(verify_lbl)
        self._verify_progress = QProgressBar()
        self._verify_progress.setStyleSheet(styles.PROGRESS_BAR)
        self._verify_progress.setRange(0, 10000)
        self._verify_progress.setValue(0)
        self._verify_progress.setFormat("%p%")
        layout.addWidget(self._verify_progress)

        # Lista de pens com estado
        self._scroll = QScrollArea()
        self._scroll.setWidgetResizable(True)
        self._scroll.setFrameShape(QScrollArea.Shape.NoFrame)

        self._pens_widget = QWidget()
        self._pens_layout = QVBoxLayout(self._pens_widget)
        self._pens_layout.setSpacing(4)
        self._pens_layout.setContentsMargins(0, 0, 0, 0)
        self._pens_layout.addStretch()

        self._scroll.setWidget(self._pens_widget)
        layout.addWidget(self._scroll, 1)

        # Relatório (inicialmente escondido)
        self._report_label = QLabel()
        self._report_label.setWordWrap(True)
        self._report_label.setStyleSheet("font-size: 15px; padding: 12px;")
        self._report_label.setVisible(False)
        layout.addWidget(self._report_label)

        # Botões
        bottom = QHBoxLayout()
        self._cancel_btn = QPushButton(S.BTN_CANCEL)
        self._cancel_btn.setStyleSheet(styles.BTN_DANGER)
        self._cancel_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._cancel_btn.clicked.connect(self._on_cancel)
        bottom.addWidget(self._cancel_btn)

        bottom.addStretch()

        self._done_btn = QPushButton(S.BTN_DONE)
        self._done_btn.setStyleSheet(styles.BTN_PRIMARY)
        self._done_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._done_btn.setVisible(False)
        self._done_btn.clicked.connect(self.done_requested.emit)
        bottom.addWidget(self._done_btn)

        layout.addLayout(bottom)

    def start(
        self,
        source_folder: str,
        drives: list[DriveInfo],
        label: str,
    ) -> None:
        """Inicia o processamento de pens."""
        self._total_pens = len(drives)
        self._bytes_per_pen = get_folder_size(source_folder)
        self._start_time = time.monotonic()

        self._title.setText(S.PROGRESS_TITLE)
        self._info_label.setText("")
        self._eta_label.setText("--:--:--")
        self._copy_progress.setValue(0)
        self._copy_progress.setStyleSheet(styles.PROGRESS_BAR)
        self._verify_progress.setValue(0)
        self._verify_progress.setStyleSheet(styles.PROGRESS_BAR)
        self._report_label.setVisible(False)
        self._cancel_btn.setVisible(True)
        self._done_btn.setVisible(False)

        # Limpar widgets de pens anteriores
        for w in self._pen_widgets:
            w.deleteLater()
        self._pen_widgets.clear()
        while self._pens_layout.count() > 1:
            item = self._pens_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        # Criar widgets de estado por pen
        for i, drive in enumerate(drives):
            widget = PenStatusWidget(drive, i)
            self._pens_layout.insertWidget(
                self._pens_layout.count() - 1, widget
            )
            self._pen_widgets.append(widget)

        # Criar e iniciar worker
        self._worker = CopyWorker(source_folder, drives, label)
        self._worker.pen_status_changed.connect(self._on_pen_status)
        self._worker.pen_progress.connect(self._on_pen_progress)
        self._worker.verify_progress.connect(self._on_verify_progress)
        self._worker.all_done.connect(self._on_all_done)
        self._worker.start()

    def _on_pen_status(self, pen_idx: int, status: PenStatus) -> None:
        """Actualiza estado de uma pen."""
        if pen_idx < len(self._pen_widgets):
            self._pen_widgets[pen_idx].set_status(status)

        if status == PenStatus.FORMATTING:
            self._info_label.setText(
                S.PROGRESS_FORMATTING.format(
                    current=pen_idx + 1, total=self._total_pens
                )
            )
        elif status == PenStatus.SCANNING:
            self._info_label.setText(
                S.PROGRESS_SCANNING.format(
                    current=pen_idx + 1, total=self._total_pens
                )
            )
        elif status == PenStatus.VERIFYING:
            self._info_label.setText(
                S.PROGRESS_VERIFYING.format(
                    current=pen_idx + 1, total=self._total_pens
                )
            )

    def _on_pen_progress(
        self, pen_idx: int, bytes_done: int, bytes_total: int, filename: str
    ) -> None:
        """Actualiza progresso de cópia — global para todas as pens."""
        if bytes_total > 0 and self._total_pens > 0:
            pen_fraction = bytes_done / bytes_total
            global_fraction = (pen_idx + pen_fraction) / self._total_pens
            self._copy_progress.setValue(int(global_fraction * 10000))

        # ETA
        self._update_eta(pen_idx, bytes_done, bytes_total)

        done_text = format_size(bytes_done)
        total_text = format_size(bytes_total)
        self._info_label.setText(
            f"Pen {pen_idx + 1} de {self._total_pens} — "
            f"A copiar: {filename} ({done_text} / {total_text})"
        )

    def _on_verify_progress(
        self, pen_idx: int, files_done: int, files_total: int, filename: str
    ) -> None:
        """Actualiza progresso de verificação."""
        if files_total > 0 and self._total_pens > 0:
            pen_fraction = files_done / files_total
            global_fraction = (pen_idx + pen_fraction) / self._total_pens
            self._verify_progress.setValue(int(global_fraction * 10000))

        self._info_label.setText(
            f"Pen {pen_idx + 1} de {self._total_pens} — "
            f"A verificar: {filename} ({files_done}/{files_total})"
        )

    def _update_eta(
        self, pen_idx: int, bytes_done: int, bytes_total: int
    ) -> None:
        """Calcula e mostra o tempo estimado restante."""
        elapsed = time.monotonic() - self._start_time
        if elapsed < 2:
            return
        if bytes_total <= 0 or self._total_pens <= 0:
            return

        # Total de bytes para todas as pens
        total_all_pens = self._bytes_per_pen * self._total_pens
        bytes_all_done = (pen_idx * self._bytes_per_pen) + bytes_done
        if bytes_all_done <= 0:
            return

        # Velocidade média de cópia
        speed = bytes_all_done / elapsed
        bytes_remaining = total_all_pens - bytes_all_done
        # Estimar verificação como ~50% do tempo de cópia (só leitura)
        verify_estimate = (total_all_pens / speed) * 0.5
        eta_seconds = (bytes_remaining / speed) + verify_estimate
        self._eta_label.setText(_format_eta(eta_seconds))

    def _on_all_done(self, results: list[PenResult]) -> None:
        """Processamento concluído — mostra relatório."""
        self._worker = None
        self._cancel_btn.setVisible(False)
        self._done_btn.setVisible(True)

        ok_count = sum(1 for r in results if r.status == PenStatus.OK)
        error_count = sum(1 for r in results if r.status == PenStatus.ERROR)
        total = len(results)
        elapsed_text = _format_eta(time.monotonic() - self._start_time)

        if error_count == 0:
            self._title.setText(S.PROGRESS_COMPLETE)
            self._copy_progress.setValue(10000)
            self._copy_progress.setStyleSheet(styles.PROGRESS_BAR_SUCCESS)
            self._verify_progress.setValue(10000)
            self._verify_progress.setStyleSheet(styles.PROGRESS_BAR_SUCCESS)
            self._report_label.setText(
                f"<span style='color: {styles.SUCCESS}; font-size: 18px; font-weight: bold;'>"
                f"{S.REPORT_ALL_OK}</span>"
                f"<br><br>Tempo total: {elapsed_text}"
            )
        else:
            self._title.setText(S.REPORT_TITLE)
            self._copy_progress.setStyleSheet(styles.PROGRESS_BAR_ERROR)
            self._verify_progress.setStyleSheet(styles.PROGRESS_BAR_ERROR)
            lines = [S.REPORT_SUCCESS.format(ok=ok_count, total=total)]
            lines.append(f"Tempo total: {elapsed_text}")
            lines.append("")
            for r in results:
                if r.status == PenStatus.ERROR:
                    lines.append(
                        f"<span style='color: {styles.ERROR};'>"
                        f"✗ {r.drive.letter}: {r.error_message}</span>"
                    )
                    for f in r.failed_files:
                        lines.append(f"&nbsp;&nbsp;&nbsp;— {f}")
            self._report_label.setText("<br>".join(lines))

        self._report_label.setVisible(True)
        self._eta_label.setText(f"Total: {elapsed_text}")
        self._info_label.setText(
            S.REPORT_SUCCESS.format(ok=ok_count, total=total)
        )

    def _on_cancel(self) -> None:
        """Pede cancelamento ao worker."""
        reply = QMessageBox.question(
            self,
            S.CANCEL_CONFIRM_TITLE,
            S.CANCEL_CONFIRM_MSG,
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes and self._worker:
            self._worker.cancel()
