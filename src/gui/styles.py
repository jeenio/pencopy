"""Tema visual da aplicação (QSS)."""

# Cores principais
PRIMARY = "#2563EB"      # Azul
PRIMARY_HOVER = "#1D4ED8"
SUCCESS = "#16A34A"      # Verde
ERROR = "#DC2626"        # Vermelho
WARNING = "#F59E0B"      # Amarelo
BG = "#F8FAFC"           # Fundo
BG_CARD = "#FFFFFF"      # Fundo de cards
TEXT = "#1E293B"         # Texto principal
TEXT_SECONDARY = "#64748B"  # Texto secundário
BORDER = "#E2E8F0"       # Bordas

GLOBAL_STYLE = f"""
QWidget {{
    font-family: "Segoe UI", "Helvetica Neue", "Arial", sans-serif;
    font-size: 14px;
    color: {TEXT};
    background-color: {BG};
}}

QLabel {{
    background-color: transparent;
}}

QPushButton {{
    border: 2px solid {BORDER};
    border-radius: 8px;
    padding: 12px 24px;
    font-size: 15px;
    font-weight: 500;
    background-color: {BG_CARD};
    color: {TEXT};
}}

QPushButton:hover {{
    border-color: {PRIMARY};
    background-color: #EFF6FF;
}}

QPushButton:pressed {{
    background-color: #DBEAFE;
}}

QPushButton:disabled {{
    color: #94A3B8;
    border-color: {BORDER};
    background-color: #F1F5F9;
}}
"""

# Botão primário (azul)
BTN_PRIMARY = f"""
QPushButton {{
    background-color: {PRIMARY};
    color: white;
    border: none;
    border-radius: 8px;
    padding: 14px 32px;
    font-size: 18px;
    font-weight: 600;
}}
QPushButton:hover {{
    background-color: {PRIMARY_HOVER};
}}
QPushButton:pressed {{
    background-color: #1E40AF;
}}
QPushButton:disabled {{
    background-color: #94A3B8;
}}
"""

# Botão de espectáculo (grande, destaque)
BTN_SHOW = f"""
QPushButton {{
    background-color: {BG_CARD};
    border: 2px solid {BORDER};
    border-radius: 12px;
    padding: 20px;
    font-size: 16px;
    font-weight: 600;
    min-height: 80px;
    min-width: 200px;
    text-align: center;
}}
QPushButton:hover {{
    border-color: {PRIMARY};
    background-color: #EFF6FF;
}}
QPushButton:checked {{
    border-color: {PRIMARY};
    background-color: #DBEAFE;
    border-width: 3px;
}}
"""

# Botão secundário (cinza com destaque)
BTN_SECONDARY = f"""
QPushButton {{
    background-color: #E2E8F0;
    color: {TEXT};
    border: none;
    border-radius: 8px;
    padding: 12px 24px;
    font-size: 15px;
    font-weight: 600;
}}
QPushButton:hover {{
    background-color: #CBD5E1;
}}
QPushButton:pressed {{
    background-color: #94A3B8;
}}
"""

# Botão de perigo (vermelho)
BTN_DANGER = f"""
QPushButton {{
    background-color: {ERROR};
    color: white;
    border: none;
    border-radius: 8px;
    padding: 12px 24px;
    font-size: 15px;
    font-weight: 600;
}}
QPushButton:hover {{
    background-color: #B91C1C;
}}
"""

# Card de drive
DRIVE_CARD = f"""
QFrame {{
    background-color: {BG_CARD};
    border: 2px solid {BORDER};
    border-radius: 10px;
    padding: 12px;
}}
QFrame:hover {{
    border-color: {PRIMARY};
}}
"""

DRIVE_CARD_SELECTED = f"""
QFrame {{
    background-color: #DBEAFE;
    border: 3px solid {PRIMARY};
    border-radius: 10px;
    padding: 12px;
}}
"""

# Barra de progresso
PROGRESS_BAR = f"""
QProgressBar {{
    border: 1px solid {BORDER};
    border-radius: 6px;
    text-align: center;
    font-size: 13px;
    font-weight: 500;
    min-height: 24px;
    background-color: #F1F5F9;
}}
QProgressBar::chunk {{
    background-color: {PRIMARY};
    border-radius: 5px;
}}
"""

PROGRESS_BAR_SUCCESS = PROGRESS_BAR.replace(PRIMARY, SUCCESS)
PROGRESS_BAR_ERROR = PROGRESS_BAR.replace(PRIMARY, ERROR)

# Título de secção
SECTION_TITLE = f"""
QLabel {{
    font-size: 22px;
    font-weight: 700;
    color: {TEXT};
    padding: 8px 0;
}}
"""

# Texto informativo
INFO_TEXT = f"""
QLabel {{
    font-size: 14px;
    color: {TEXT_SECONDARY};
    padding: 4px 0;
}}
"""

# Toolbar / header
TOOLBAR = f"""
QFrame {{
    background-color: {BG_CARD};
    border-bottom: 1px solid {BORDER};
    padding: 8px 16px;
}}
"""
