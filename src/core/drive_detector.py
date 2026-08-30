"""Detecção cross-platform de drives USB removíveis."""

from __future__ import annotations

import os
import platform
import subprocess
import string
from dataclasses import dataclass

import psutil

# Tamanho máximo para considerar como pendrive (64 GB)
# Drives maiores são provavelmente discos externos e são ignoradas
MAX_DRIVE_BYTES = 64 * 1024 * 1024 * 1024  # 64 GB


@dataclass
class DriveInfo:
    """Informação sobre uma pendrive detectada."""

    mount_point: str   # Ex: "E:\\" (Win), "/Volumes/PEN" (Mac), "/media/user/PEN" (Linux)
    label: str         # Label do volume (pode ser vazia)
    total_bytes: int   # Capacidade total
    free_bytes: int    # Espaço livre
    device: str        # Ex: "E:" (Win), "/dev/disk2" (Mac), "/dev/sdb1" (Linux)

    @property
    def letter(self) -> str:
        """Devolve a letra da drive (Windows) ou o nome do mount point."""
        if platform.system() == "Windows":
            return self.mount_point.rstrip("\\").rstrip("/")
        return os.path.basename(self.mount_point) or self.mount_point


def format_size(size_bytes: int) -> str:
    """Formata bytes num tamanho legível."""
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 ** 2:
        return f"{size_bytes / 1024:.1f} KB"
    elif size_bytes < 1024 ** 3:
        return f"{size_bytes / 1024 ** 2:.1f} MB"
    elif size_bytes < 1024 ** 4:
        return f"{size_bytes / 1024 ** 3:.2f} GB"
    else:
        return f"{size_bytes / 1024 ** 4:.2f} TB"


def detect_usb_drives() -> list[DriveInfo]:
    """Detecta todas as pendrives USB removíveis ligadas ao sistema (≤64GB)."""
    system = platform.system()
    if system == "Windows":
        drives = _detect_windows()
    elif system == "Darwin":
        drives = _detect_macos()
    elif system == "Linux":
        drives = _detect_linux()
    else:
        drives = []
    # Filtrar drives maiores que 64GB (provavelmente discos externos)
    return [d for d in drives if d.total_bytes <= MAX_DRIVE_BYTES]


def _detect_windows() -> list[DriveInfo]:
    """Detecção de USB removíveis no Windows via WMI."""
    drives: list[DriveInfo] = []
    try:
        # Usa wmic para listar drives removíveis (DriveType=2)
        result = subprocess.run(
            ["wmic", "logicaldisk", "where", "DriveType=2", "get",
             "DeviceID,VolumeName,Size,FreeSpace", "/format:csv"],
            capture_output=True, text=True, timeout=10,
            creationflags=subprocess.CREATE_NO_WINDOW,
        )
        for line in result.stdout.strip().splitlines():
            line = line.strip()
            if not line or line.startswith("Node"):
                continue
            parts = line.split(",")
            if len(parts) < 5:
                continue
            # CSV: Node, DeviceID, FreeSpace, Size, VolumeName
            _, device_id, free_space, size, volume_name = parts[0], parts[1], parts[2], parts[3], parts[4] if len(parts) > 4 else ""
            if not size or not device_id:
                continue
            try:
                total = int(size)
                free = int(free_space) if free_space else 0
            except ValueError:
                continue
            mount = device_id + "\\"
            drives.append(DriveInfo(
                mount_point=mount,
                label=volume_name.strip(),
                total_bytes=total,
                free_bytes=free,
                device=device_id,
            ))
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
        # Fallback: usar psutil
        drives = _detect_windows_fallback()
    return drives


def _detect_windows_fallback() -> list[DriveInfo]:
    """Fallback via psutil para Windows."""
    drives: list[DriveInfo] = []
    for part in psutil.disk_partitions(all=False):
        # Em Windows, pendrives removíveis têm 'removable' nas opts
        if "removable" not in part.opts.lower():
            continue
        try:
            usage = psutil.disk_usage(part.mountpoint)
        except (PermissionError, OSError):
            continue
        drives.append(DriveInfo(
            mount_point=part.mountpoint,
            label=_get_volume_label_win(part.mountpoint),
            total_bytes=usage.total,
            free_bytes=usage.free,
            device=part.device,
        ))
    return drives


def _get_volume_label_win(mount_point: str) -> str:
    """Obtém o label do volume no Windows via vol command."""
    try:
        drive_letter = mount_point.rstrip("\\").rstrip("/")
        result = subprocess.run(
            ["cmd", "/c", "vol", drive_letter],
            capture_output=True, text=True, timeout=5,
            creationflags=subprocess.CREATE_NO_WINDOW,
        )
        # Output: " Volume in drive E is LABEL"
        for line in result.stdout.splitlines():
            if " is " in line:
                return line.split(" is ", 1)[1].strip()
    except (subprocess.TimeoutExpired, OSError):
        pass
    return ""


def _detect_macos() -> list[DriveInfo]:
    """Detecção de USB removíveis no macOS via diskutil."""
    drives: list[DriveInfo] = []
    try:
        # Lista todos os discos externos
        result = subprocess.run(
            ["diskutil", "list", "-plist", "external"],
            capture_output=True, text=True, timeout=10,
        )
        # Alternativa mais simples: iterar /Volumes e verificar se é removível
        import plistlib
        plist = plistlib.loads(result.stdout.encode())
        disk_ids = plist.get("AllDisksAndPartitions", [])

        for disk in disk_ids:
            disk_id = disk.get("DeviceIdentifier", "")
            partitions = disk.get("Partitions", [])
            for part in partitions:
                part_id = part.get("DeviceIdentifier", "")
                mount = part.get("MountPoint", "")
                if not mount:
                    continue
                info = _get_diskutil_info(part_id)
                if not info:
                    continue
                if not info.get("removable", False):
                    continue
                drives.append(DriveInfo(
                    mount_point=mount,
                    label=info.get("name", ""),
                    total_bytes=info.get("total", 0),
                    free_bytes=info.get("free", 0),
                    device=f"/dev/{part_id}",
                ))
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
        pass
    return drives


def _get_diskutil_info(disk_id: str) -> dict | None:
    """Obtém informação detalhada de um disco via diskutil info."""
    try:
        result = subprocess.run(
            ["diskutil", "info", "-plist", disk_id],
            capture_output=True, text=True, timeout=10,
        )
        import plistlib
        plist = plistlib.loads(result.stdout.encode())
        return {
            "name": plist.get("VolumeName", ""),
            "total": plist.get("TotalSize", 0),
            "free": plist.get("APFSContainerFree", plist.get("FreeSpace", 0)),
            "removable": plist.get("RemovableMedia", False),
        }
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
        return None


def _detect_linux() -> list[DriveInfo]:
    """Detecção de USB removíveis no Linux via /sys e lsblk."""
    drives: list[DriveInfo] = []
    try:
        result = subprocess.run(
            ["lsblk", "-J", "-o", "NAME,MOUNTPOINT,LABEL,SIZE,FSTYPE,RM,TYPE,HOTPLUG"],
            capture_output=True, text=True, timeout=10,
        )
        import json
        data = json.loads(result.stdout)
        for device in data.get("blockdevices", []):
            # Verificar se é removível ou hotplug (USB)
            is_removable = device.get("rm", False) or device.get("hotplug", False)
            if not is_removable:
                continue
            # Verificar partições
            children = device.get("children", [])
            if not children:
                # Dispositivo sem partições
                mount = device.get("mountpoint", "")
                if mount:
                    _add_linux_drive(drives, device, mount)
            else:
                for child in children:
                    mount = child.get("mountpoint", "")
                    if mount:
                        _add_linux_drive(drives, child, mount, parent_name=device.get("name", ""))
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
        pass
    return drives


def _add_linux_drive(drives: list[DriveInfo], dev: dict, mount: str, parent_name: str = "") -> None:
    """Adiciona um drive Linux à lista."""
    try:
        usage = psutil.disk_usage(mount)
    except (PermissionError, OSError):
        return
    name = dev.get("name", "")
    drives.append(DriveInfo(
        mount_point=mount,
        label=dev.get("label", "") or "",
        total_bytes=usage.total,
        free_bytes=usage.free,
        device=f"/dev/{name}",
    ))
