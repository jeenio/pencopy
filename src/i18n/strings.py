"""Todas as strings da interface em Português."""

# Janela principal
APP_TITLE = "PenCopy"
APP_SUBTITLE = "Cópia em massa para pendrives"

# Ecrã principal
HOME_NO_SHOWS = "Nenhum espectáculo configurado.\nUse Ferramentas → Adicionar para começar."
HOME_FILES_COUNT = "{count} ficheiro(s)"
HOME_TOTAL_SIZE = "{size}"
BTN_TOOLS = "⚙ Ferramentas"
BTN_EXIT = "Sair"
BTN_BACK = "← Voltar"
BTN_NEXT = "Seguinte →"

# Ecrã de drives
DRIVES_TITLE = "Seleccione as pendrives"
DRIVES_NONE = "Nenhuma pendrive detectada.\nInsira as pendrives e aguarde."
DRIVES_SELECT_ALL = "Seleccionar todas"
DRIVES_DESELECT_ALL = "Desmarcar todas"
DRIVES_FREE = "{size} livres"
DRIVES_TOTAL = "{size} total"
BTN_START = "▶ Iniciar"
DRIVES_REFRESHING = "A procurar pendrives..."

# Diálogo de confirmação
CONFIRM_TITLE = "Atenção!"
CONFIRM_MESSAGE = (
    "TODO o conteúdo de {count} pendrive(s) será APAGADO permanentemente.\n\n"
    "Espectáculo: {show}\n"
    "Pendrives seleccionadas: {count}\n\n"
    "Tem a certeza que deseja continuar?"
)
CONFIRM_YES = "Sim, apagar e copiar"
CONFIRM_NO = "Cancelar"

# Ecrã de progresso
PROGRESS_TITLE = "A processar..."
PROGRESS_FORMATTING = "A formatar pen {current} de {total}..."
PROGRESS_SCANNING = "A verificar pen {current} de {total} (bad sectors)..."
PROGRESS_COPYING = "A copiar para pen {current} de {total} — ficheiro {file_num} de {file_total}"
PROGRESS_VERIFYING = "A verificar pen {current} de {total}..."
PROGRESS_COMPLETE = "Concluído!"
PROGRESS_PEN_OK = "✓ OK"
PROGRESS_PEN_ERROR = "✗ Erro"
PROGRESS_PEN_WAITING = "Em espera"
PROGRESS_PEN_ACTIVE = "A processar..."
BTN_DONE = "Concluir"
BTN_CANCEL = "Cancelar"
CANCEL_CONFIRM_TITLE = "Cancelar operação?"
CANCEL_CONFIRM_MSG = "Tem a certeza? As pens já formatadas ficarão vazias."

# Relatório
REPORT_TITLE = "Relatório"
REPORT_SUCCESS = "{ok} de {total} pen(s) copiada(s) com sucesso"
REPORT_ALL_OK = "Todas as pens foram copiadas e verificadas com sucesso!"
REPORT_ERRORS = "{errors} pen(s) com erro(s):"
REPORT_PEN_LABEL = "Pen {letter}"
REPORT_ERROR_FORMAT = "Erro ao formatar: {detail}"
REPORT_ERROR_COPY = "Erro ao copiar {file}: {detail}"
REPORT_ERROR_VERIFY = "Verificação falhou: {file}"

# Ferramentas
TOOLS_TITLE = "Ferramentas — Espectáculos"
TOOLS_ADD = "Adicionar Pasta"
TOOLS_REMOVE = "Remover"
TOOLS_BACK = "← Voltar"
TOOLS_FOLDER_DIALOG = "Seleccionar pasta do espectáculo"
TOOLS_EMPTY = "Nenhum espectáculo configurado."
TOOLS_PATH = "Pasta: {path}"
TOOLS_CONFIRM_REMOVE = "Remover o espectáculo \"{name}\"?"
TOOLS_NO_MEDIA = (
    "A pasta seleccionada não contém conteúdo multimédia "
    "(mp4, mov, jpg).\n\nTem a certeza que deseja prosseguir?"
)
TOOLS_NO_MEDIA_TITLE = "Aviso"

# Tamanhos
SIZE_BYTES = "{n} B"
SIZE_KB = "{n:.1f} KB"
SIZE_MB = "{n:.1f} MB"
SIZE_GB = "{n:.2f} GB"
SIZE_TB = "{n:.2f} TB"

# Erros
ERR_NO_DRIVES = "Nenhuma pendrive seleccionada."
ERR_NO_SHOW = "Nenhum espectáculo seleccionado."
ERR_FOLDER_MISSING = "A pasta \"{path}\" já não existe."
ERR_FOLDER_EMPTY = "A pasta \"{path}\" está vazia."
ERR_DRIVE_TOO_SMALL = "A pen {letter} ({size}) não tem espaço suficiente para {needed}."
ERR_FORMAT_FAILED = "Erro ao formatar {letter}: {detail}"
ERR_ELEVATION = "Esta operação necessita de permissões de administrador."
