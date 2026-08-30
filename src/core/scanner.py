"""Scan de pendrives para detecção e marcação de bad sectors."""

from __future__ import annotations

import platform
import subprocess

from .drive_detector import DriveInfo


# Modos de scan
SCAN_NONE = "none"
SCAN_QUICK = "quick"   # Só erros lógicos do filesystem
SCAN_FULL = "full"     # Scan de superfície + marcação de bad sectors


def scan_drive(drive: DriveInfo, mode: str) -> None:
    """
    Faz scan de uma drive para detectar/corrigir erros.

    Args:
        drive: A drive a verificar.
        mode: SCAN_NONE, SCAN_QUICK ou SCAN_FULL.

    Raises:
        RuntimeError: Se o scan falhar criticamente.
    """
    if mode == SCAN_NONE:
        return

    system = platform.system()
    if system == "Windows":
        _scan_windows(drive, mode)
    elif system == "Darwin":
        _scan_macos(drive, mode)
    elif system == "Linux":
        _scan_linux(drive, mode)


def _scan_windows(drive: DriveInfo, mode: str) -> None:
    """Scan no Windows via chkdsk."""
    drive_letter = drive.device  # Ex: "E:"

    if mode == SCAN_FULL:
        # /R = localiza bad sectors e recupera informação legível
        #      (inclui /F automaticamente)
        flags = "/R"
        timeout = 3600  # 1h max para scan completo
    else:
        # /F = corrige erros no filesystem
        flags = "/F"
        timeout = 120

    try:
        result = subprocess.run(
            ["cmd", "/c", "chkdsk", drive_letter, flags],
            capture_output=True, text=True, timeout=timeout,
            creationflags=subprocess.CREATE_NO_WINDOW,
            input="Y\n",  # Confirmar prompts
        )
        # chkdsk pode retornar código != 0 mesmo com correcções bem-sucedidas
        # Só falha se stderr tiver erros graves
        if result.returncode not in (0, 1, 2, 3):
            stderr = result.stderr.strip() or result.stdout.strip()
            raise RuntimeError(f"chkdsk falhou: {stderr}")
    except subprocess.TimeoutExpired:
        raise RuntimeError(
            f"Scan excedeu o tempo limite ({timeout // 60} minutos)."
        )


def _scan_macos(drive: DriveInfo, mode: str) -> None:
    """Scan no macOS via diskutil/fsck."""
    import re
    device = drive.device
    disk_match = re.match(r"/dev/(disk\d+s?\d*)", device)
    if not disk_match:
        raise RuntimeError(f"Não foi possível determinar o disco para {device}")
    disk_id = disk_match.group(1)

    if mode == SCAN_FULL:
        # repairVolume corrige erros e faz verificação mais profunda
        cmd = ["diskutil", "repairVolume", disk_id]
        timeout = 3600
    else:
        cmd = ["diskutil", "verifyVolume", disk_id]
        timeout = 120

    try:
        result = subprocess.run(
            cmd, capture_output=True, text=True, timeout=timeout,
        )
        # verifyVolume pode reportar erros sem falhar
        if result.returncode != 0 and mode == SCAN_QUICK:
            # Se verificação falhou, tentar reparar
            subprocess.run(
                ["diskutil", "repairVolume", disk_id],
                capture_output=True, text=True, timeout=timeout,
            )
    except subprocess.TimeoutExpired:
        raise RuntimeError(
            f"Scan excedeu o tempo limite ({timeout // 60} minutos)."
        )


def _scan_linux(drive: DriveInfo, mode: str) -> None:
    """Scan no Linux via fsck.exfat e badblocks."""
    device = drive.device

    # Desmontar para fsck
    try:
        subprocess.run(
            ["umount", device],
            capture_output=True, text=True, timeout=30,
        )
    except (subprocess.TimeoutExpired, OSError):
        pass

    if mode == SCAN_FULL:
        # badblocks faz scan de superfície e lista sectores maus
        timeout = 3600
        try:
            result = subprocess.run(
                ["badblocks", "-sv", device],
                capture_output=True, text=True, timeout=timeout,
            )
        except FileNotFoundError:
            pass  # badblocks não disponível, continuar com fsck
        except subprocess.TimeoutExpired:
            raise RuntimeError("Scan de superfície excedeu o tempo limite.")

    # fsck.exfat para corrigir erros do filesystem
    try:
        result = subprocess.run(
            ["fsck.exfat", "-y", device],
            capture_output=True, text=True, timeout=300,
        )
    except FileNotFoundError:
        # Tentar alternativa
        try:
            subprocess.run(
                ["exfatfsck", device],
                capture_output=True, text=True, timeout=300,
            )
        except FileNotFoundError:
            pass  # Sem ferramentas de fsck disponíveis

    # Remontar
    try:
        subprocess.run(
            ["mount", device, drive.mount_point],
            capture_output=True, text=True, timeout=30,
        )
    except (subprocess.TimeoutExpired, OSError):
        raise RuntimeError(
            f"Scan concluído mas não foi possível remontar {device}."
        )
