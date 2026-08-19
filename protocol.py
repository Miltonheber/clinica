"""Contrato de mensagens entre o cliente e o servidor.

O protocolo é texto simples, uma mensagem por linha (terminada em '\n'),
porque o TCP é um stream de bytes sem limites de mensagem definidos.
Os campos de cada mensagem são separados por '|'.
"""

SEP = "|"

# Comandos que o cliente pode enviar ao servidor.
CMD_REGISTER = "REGISTER"
CMD_QUERY = "QUERY"
CMD_LIST = "LIST"
CMD_UPDATE = "UPDATE"
CMD_DELETE = "DELETE"
CMD_QUIT = "QUIT"

# Prefixos das respostas do servidor.
STATUS_OK = "OK"
STATUS_ERROR = "ERROR"

# Linha sentinela que marca o fim de uma listagem.
END_OF_LIST = "END"


def build_message(*fields: str) -> str:
    """Junta campos com o separador do protocolo, pronta a enviar."""
    return SEP.join(str(field) for field in fields)


def parse_message(line: str) -> list[str]:
    """Separa uma linha recebida nos seus campos, sem o '\n' final."""
    return line.rstrip("\n").split(SEP)
