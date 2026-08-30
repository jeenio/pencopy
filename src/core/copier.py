"""Cópia de ficheiros com progresso granular."""

from __future__ import annotations

import os
import shutil
from pathlib import Path
from typing import Callable

import xxhash

# Tamanho do bloco de leitura (4 MB)
BLOCK_SIZE = 4 * 1024 * 1024

# Callback type: (bytes_copied_so_far, total_bytes, current_file_name)
ProgressCallback = Callable[[int, int, str], None]


def get_folder_files(folder: str | Path) -> list[Path]:
    """Devolve lista de ficheiros numa pasta (recursivo), ordenados por nome."""
    folder = Path(folder)
    files = sorted(f for f in folder.rglob("*") if f.is_file())
    return files


def get_folder_size(folder: str | Path) -> int:
    """Calcula o tamanho total de todos os ficheiros numa pasta."""
    return sum(f.stat().st_size for f in get_folder_files(folder))


def copy_folder_to_drive(
    source_folder: str | Path,
    dest_root: str | Path,
    progress_callback: ProgressCallback | None = None,
    cancel_check: Callable[[], bool] | None = None,
) -> dict[str, str]:
    """
    Copia todos os ficheiros de source_folder para dest_root,
    mantendo a estrutura de subpastas.

    Calcula o hash xxhash de cada ficheiro DURANTE a cópia (para não ler 2x).

    Args:
        source_folder: Pasta de origem.
        dest_root: Raiz do destino (mount point da pen).
        progress_callback: Callback chamado a cada bloco copiado.
        cancel_check: Função que devolve True se a operação foi cancelada.

    Returns:
        Dicionário {caminho_relativo: hash_xxhash} para verificação posterior.

    Raises:
        OSError: Se houver erro de I/O.
        InterruptedError: Se a operação for cancelada.
    """
    source_folder = Path(source_folder)
    dest_root = Path(dest_root)
    files = get_folder_files(source_folder)
    total_size = sum(f.stat().st_size for f in files)
    bytes_copied = 0
    hashes: dict[str, str] = {}

    for file_path in files:
        if cancel_check and cancel_check():
            raise InterruptedError("Operação cancelada pelo utilizador.")

        rel_path = file_path.relative_to(source_folder)
        dest_path = dest_root / rel_path

        # Criar directório de destino se necessário
        dest_path.parent.mkdir(parents=True, exist_ok=True)

        # Copiar ficheiro bloco a bloco, calculando hash simultaneamente
        file_hash = xxhash.xxh3_64()
        file_size = file_path.stat().st_size

        with open(file_path, "rb") as src, open(dest_path, "wb") as dst:
            while True:
                if cancel_check and cancel_check():
                    # Limpar ficheiro parcial
                    dst.close()
                    try:
                        dest_path.unlink()
                    except OSError:
                        pass
                    raise InterruptedError("Operação cancelada pelo utilizador.")

                block = src.read(BLOCK_SIZE)
                if not block:
                    break
                dst.write(block)
                file_hash.update(block)
                bytes_copied += len(block)

                if progress_callback:
                    progress_callback(bytes_copied, total_size, rel_path.name)

        # Preservar timestamps
        src_stat = file_path.stat()
        os.utime(dest_path, (src_stat.st_atime, src_stat.st_mtime))

        hashes[str(rel_path)] = file_hash.hexdigest()

    return hashes
