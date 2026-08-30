"""Worker thread para processar pens sequencialmente."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum, auto
from pathlib import Path

from PySide6.QtCore import QThread, Signal

from .drive_detector import DriveInfo
from .formatter import format_drive, sanitize_label
from .copier import copy_folder_to_drive, get_folder_files
from .scanner import scan_drive, SCAN_FULL
from .verifier import verify_copy


class PenStatus(Enum):
    WAITING = auto()
    FORMATTING = auto()
    SCANNING = auto()
    COPYING = auto()
    VERIFYING = auto()
    OK = auto()
    ERROR = auto()


@dataclass
class PenResult:
    """Resultado do processamento de uma pen."""

    drive: DriveInfo
    status: PenStatus = PenStatus.WAITING
    error_message: str = ""
    failed_files: list[str] = field(default_factory=list)


class CopyWorker(QThread):
    """
    Worker que processa múltiplas pens sequencialmente.

    Sinais emitidos:
        pen_status_changed(int, PenStatus): índice da pen + novo estado
        pen_progress(int, int, int, str): pen_idx, bytes_done, bytes_total, filename
        verify_progress(int, int, int, str): pen_idx, files_done, files_total, filename
        all_done(list[PenResult]): resultado final de todas as pens
    """

    pen_status_changed = Signal(int, object)  # pen_idx, PenStatus
    pen_progress = Signal(int, object, object, str)  # pen_idx, bytes_done, total, filename
    verify_progress = Signal(int, int, int, str)  # pen_idx, files_done, total, filename
    all_done = Signal(list)  # list[PenResult]

    def __init__(
        self,
        source_folder: str,
        drives: list[DriveInfo],
        label: str,
        parent=None,
    ):
        super().__init__(parent)
        self._source_folder = source_folder
        self._drives = drives
        self._label = label
        self._cancelled = False

    def cancel(self) -> None:
        """Pede o cancelamento da operação."""
        self._cancelled = True

    def _is_cancelled(self) -> bool:
        return self._cancelled

    def run(self) -> None:
        """Processa cada pen sequencialmente: formatar → copiar → verificar."""
        results: list[PenResult] = []

        for idx, drive in enumerate(self._drives):
            result = PenResult(drive=drive)

            if self._cancelled:
                result.status = PenStatus.ERROR
                result.error_message = "Cancelado pelo utilizador."
                results.append(result)
                continue

            # 1. Formatar
            result.status = PenStatus.FORMATTING
            self.pen_status_changed.emit(idx, PenStatus.FORMATTING)
            try:
                format_drive(drive, self._label)
            except Exception as e:
                result.status = PenStatus.ERROR
                result.error_message = f"Erro ao formatar: {e}"
                self.pen_status_changed.emit(idx, PenStatus.ERROR)
                results.append(result)
                continue

            if self._cancelled:
                result.status = PenStatus.ERROR
                result.error_message = "Cancelado pelo utilizador."
                self.pen_status_changed.emit(idx, PenStatus.ERROR)
                results.append(result)
                continue

            # 2. Scan completo (bad sectors)
            result.status = PenStatus.SCANNING
            self.pen_status_changed.emit(idx, PenStatus.SCANNING)
            try:
                scan_drive(drive, SCAN_FULL)
            except Exception as e:
                result.status = PenStatus.ERROR
                result.error_message = f"Erro no scan: {e}"
                self.pen_status_changed.emit(idx, PenStatus.ERROR)
                results.append(result)
                continue

            if self._cancelled:
                result.status = PenStatus.ERROR
                result.error_message = "Cancelado pelo utilizador."
                self.pen_status_changed.emit(idx, PenStatus.ERROR)
                results.append(result)
                continue

            # 3. Copiar
            result.status = PenStatus.COPYING
            self.pen_status_changed.emit(idx, PenStatus.COPYING)
            try:
                hashes = copy_folder_to_drive(
                    self._source_folder,
                    drive.mount_point,
                    progress_callback=lambda done, total, name, i=idx: (
                        self.pen_progress.emit(i, done, total, name)
                    ),
                    cancel_check=self._is_cancelled,
                )
            except InterruptedError:
                result.status = PenStatus.ERROR
                result.error_message = "Cancelado pelo utilizador."
                self.pen_status_changed.emit(idx, PenStatus.ERROR)
                results.append(result)
                continue
            except Exception as e:
                result.status = PenStatus.ERROR
                result.error_message = f"Erro ao copiar: {e}"
                self.pen_status_changed.emit(idx, PenStatus.ERROR)
                results.append(result)
                continue

            if self._cancelled:
                result.status = PenStatus.ERROR
                result.error_message = "Cancelado pelo utilizador."
                self.pen_status_changed.emit(idx, PenStatus.ERROR)
                results.append(result)
                continue

            # 3. Verificar
            result.status = PenStatus.VERIFYING
            self.pen_status_changed.emit(idx, PenStatus.VERIFYING)
            try:
                failed = verify_copy(
                    drive.mount_point,
                    hashes,
                    progress_callback=lambda done, total, name, i=idx: (
                        self.verify_progress.emit(i, done, total, name)
                    ),
                    cancel_check=self._is_cancelled,
                )
            except InterruptedError:
                result.status = PenStatus.ERROR
                result.error_message = "Cancelado pelo utilizador."
                self.pen_status_changed.emit(idx, PenStatus.ERROR)
                results.append(result)
                continue
            except Exception as e:
                result.status = PenStatus.ERROR
                result.error_message = f"Erro ao verificar: {e}"
                self.pen_status_changed.emit(idx, PenStatus.ERROR)
                results.append(result)
                continue

            if failed:
                result.status = PenStatus.ERROR
                result.failed_files = failed
                result.error_message = f"Verificação falhou em {len(failed)} ficheiro(s)."
                self.pen_status_changed.emit(idx, PenStatus.ERROR)
            else:
                result.status = PenStatus.OK
                self.pen_status_changed.emit(idx, PenStatus.OK)

            results.append(result)

        self.all_done.emit(results)
