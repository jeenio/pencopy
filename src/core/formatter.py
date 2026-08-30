"""Formatação exFAT cross-platform."""

from __future__ import annotations

import platform
import re
import subprocess

from .drive_detector import DriveInfo

# Limite de caracteres para label exFAT
MAX_LABEL_LENGTH = 15
# Caracteres inválidos em labels exFAT
_INVALID_LABEL_CHARS = re.compile(r'[\\/:*?"<>|]')


def sanitize_label(label: str) -> str:
    """Limpa e trunca um label para ser válido em exFAT."""
    label = _INVALID_LABEL_CHARS.sub("", label)
    return label[:MAX_LABEL_LENGTH].strip()


def format_drive(drive: DriveInfo, label: str) -> None:
    """
    Formata uma drive em exFAT com o label indicado.

    Raises:
        PermissionError: Se não houver privilégios suficientes.
        RuntimeError: Se a formatação falhar.
    """
    label = sanitize_label(label)
    system = platform.system()

    if system == "Windows":
        _format_windows(drive, label)
    elif system == "Darwin":
        _format_macos(drive, label)
    elif system == "Linux":
        _format_linux(drive, label)
    else:
        raise RuntimeError(f"Sistema operativo não suportado: {system}")


def _format_windows(drive: DriveInfo, label: str) -> None:
    """Formata em Windows usando format.com via cmd."""
    drive_letter = drive.device  # Ex: "E:"
    try:
        # format é um comando interno do cmd, não um executável separado
        # Precisamos de stdin PIPE para responder ao prompt do format
        result = subprocess.run(
            ["cmd", "/c", "format", drive_letter, "/FS:exFAT", f"/V:{label}", "/Q", "/Y"],
            capture_output=True, text=True, timeout=120,
            creationflags=subprocess.CREATE_NO_WINDOW,
            input="\n",  # Confirmar prompts do format
        )
        if result.returncode != 0:
            stderr = result.stderr.strip() or result.stdout.strip()
            raise RuntimeError(stderr)
    except subprocess.TimeoutExpired:
        raise RuntimeError("Formatação excedeu o tempo limite (2 minutos).")


def _format_macos(drive: DriveInfo, label: str) -> None:
    """Formata em macOS usando diskutil."""
    # Precisamos do identificador do disco inteiro (ex: disk2), não da partição
    # drive.device é algo como "/dev/disk2s1"
    device = drive.device
    # Extrair o disco pai (ex: /dev/disk2s1 -> disk2)
    disk_match = re.match(r"/dev/(disk\d+)", device)
    if not disk_match:
        raise RuntimeError(f"Não foi possível determinar o disco para {device}")
    disk_id = disk_match.group(1)

    try:
        result = subprocess.run(
            ["diskutil", "eraseDisk", "ExFAT", label, disk_id],
            capture_output=True, text=True, timeout=120,
        )
        if result.returncode != 0:
            stderr = result.stderr.strip() or result.stdout.strip()
            raise RuntimeError(stderr)
    except subprocess.TimeoutExpired:
        raise RuntimeError("Formatação excedeu o tempo limite (2 minutos).")


def _format_linux(drive: DriveInfo, label: str) -> None:
    """Formata em Linux usando mkfs.exfat."""
    device = drive.device  # Ex: "/dev/sdb1"

    # Desmontar primeiro
    try:
        subprocess.run(
            ["umount", device],
            capture_output=True, text=True, timeout=30,
        )
    except (subprocess.TimeoutExpired, OSError):
        pass  # Pode já estar desmontado

    try:
        result = subprocess.run(
            ["mkfs.exfat", "-n", label, device],
            capture_output=True, text=True, timeout=120,
        )
        if result.returncode != 0:
            stderr = result.stderr.strip() or result.stdout.strip()
            raise RuntimeError(stderr)
    except FileNotFoundError:
        raise RuntimeError(
            "mkfs.exfat não encontrado. Instale o pacote 'exfatprogs': "
            "sudo apt install exfatprogs"
        )
    except subprocess.TimeoutExpired:
        raise RuntimeError("Formatação excedeu o tempo limite (2 minutos).")

    # Remontar para podermos copiar ficheiros
    try:
        subprocess.run(
            ["mount", device, drive.mount_point],
            capture_output=True, text=True, timeout=30,
        )
    except (subprocess.TimeoutExpired, OSError):
        raise RuntimeError(
            f"Formatação concluída mas não foi possível remontar {device}."
        )
