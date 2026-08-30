"""Verificação de integridade de ficheiros copiados via xxhash."""

from __future__ import annotations

from pathlib import Path
from typing import Callable

import xxhash

from .copier import BLOCK_SIZE

# Callback: (files_verified, total_files, current_file_name)
VerifyCallback = Callable[[int, int, str], None]


def verify_copy(
    dest_root: str | Path,
    expected_hashes: dict[str, str],
    progress_callback: VerifyCallback | None = None,
    cancel_check: Callable[[], bool] | None = None,
) -> list[str]:
    """
    Verifica a integridade dos ficheiros copiados comparando hashes.

    Args:
        dest_root: Raiz do destino (mount point da pen).
        expected_hashes: Dicionário {caminho_relativo: hash_esperado} do copier.
        progress_callback: Callback chamado por cada ficheiro verificado.
        cancel_check: Função que devolve True se a operação foi cancelada.

    Returns:
        Lista de caminhos relativos com hash diferente (lista vazia = tudo OK).

    Raises:
        InterruptedError: Se a operação for cancelada.
    """
    dest_root = Path(dest_root)
    failed: list[str] = []
    total = len(expected_hashes)

    for idx, (rel_path, expected_hash) in enumerate(expected_hashes.items(), 1):
        if cancel_check and cancel_check():
            raise InterruptedError("Verificação cancelada pelo utilizador.")

        file_path = dest_root / rel_path

        if not file_path.exists():
            failed.append(rel_path)
            if progress_callback:
                progress_callback(idx, total, Path(rel_path).name)
            continue

        # Calcular hash do ficheiro no destino
        actual_hash = _hash_file(file_path)
        if actual_hash != expected_hash:
            failed.append(rel_path)

        if progress_callback:
            progress_callback(idx, total, Path(rel_path).name)

    return failed


def _hash_file(file_path: Path) -> str:
    """Calcula o hash xxh3_64 de um ficheiro."""
    h = xxhash.xxh3_64()
    with open(file_path, "rb") as f:
        while True:
            block = f.read(BLOCK_SIZE)
            if not block:
                break
            h.update(block)
    return h.hexdigest()
