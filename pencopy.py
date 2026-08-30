"""PenCopy — Entry point para PyInstaller e execução directa."""

import sys
import os

# Garantir que o directório do script está no path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.main import main

if __name__ == "__main__":
    main()
