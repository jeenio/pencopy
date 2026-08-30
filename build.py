"""Script de build para gerar executáveis standalone com PyInstaller."""

from __future__ import annotations

import platform
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).parent
MAIN_SCRIPT = ROOT / "src" / "main.py"
ICON = ROOT / "resources" / "icon.png"


def build() -> None:
    system = platform.system()
    name = "PenCopy"

    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--onefile",
        "--windowed",
        "--name", name,
        "--clean",
    ]

    if ICON.exists():
        # PyInstaller aceita .ico no Windows, .icns no Mac
        # Para .png, funciona em Linux
        if system == "Windows":
            ico = ROOT / "resources" / "icon.ico"
            if ico.exists():
                cmd.extend(["--icon", str(ico)])
        elif system == "Darwin":
            icns = ROOT / "resources" / "icon.icns"
            if icns.exists():
                cmd.extend(["--icon", str(icns)])

    # Incluir config.json se existir
    config = ROOT / "config.json"
    if config.exists():
        sep = ";" if system == "Windows" else ":"
        cmd.extend(["--add-data", f"{config}{sep}."])

    # UAC manifest para Windows (pedir elevação)
    if system == "Windows":
        cmd.append("--uac-admin")

    cmd.append(str(MAIN_SCRIPT))

    print(f"A construir {name} para {system}...")
    print(f"Comando: {' '.join(cmd)}")
    result = subprocess.run(cmd, cwd=str(ROOT))
    if result.returncode == 0:
        print(f"\n✓ Build concluído! Executável em: dist/{name}")
    else:
        print(f"\n✗ Erro no build (código {result.returncode})")
        sys.exit(1)


if __name__ == "__main__":
    build()
