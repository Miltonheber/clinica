"""Cliente TCP com interface de terminal (rich): menu, formulários e tabelas."""

import socket

from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm, Prompt
from rich.table import Table

import protocol as proto

HOST = "127.0.0.1"
PORT = 5000

console = Console()

# Cabeçalhos da tabela de listagem, na mesma ordem dos campos do protocolo.
COLUMN_LABELS = ["ID", "Nome", "Nascimento", "Sexo", "Telefone", "Diagnóstico", "Alergias", "Medicação"]


def print_success(message: str) -> None:
    console.print(f"[bold green]✓ {message}[/bold green]")


def print_error(message: str) -> None:
    console.print(f"[bold red]✗ {message}[/bold red]")


def print_patient(fields: list[str]) -> None:
    """Mostra um único paciente (resposta a QUERY)."""
    table = Table(show_header=False, box=None)
    for label, value in zip(COLUMN_LABELS, fields):
        table.add_row(f"[bold cyan]{label}[/bold cyan]", value)
    console.print(table)


def print_patients_table(rows: list[list[str]]) -> None:
    """Mostra a listagem completa de pacientes."""
    table = Table(title="Pacientes registados", header_style="bold cyan")
    for label in COLUMN_LABELS:
        table.add_column(label)
    for row in rows:
        table.add_row(*row)
    console.print(table)


def prompt_patient_data() -> list[str]:
    """Pede ao utilizador todos os campos de um paciente (registo ou atualização)."""
    name = Prompt.ask("Nome")
    birth_date = Prompt.ask("Data de nascimento (AAAA-MM-DD)")
    sex = Prompt.ask("Sexo", default="")
    phone = Prompt.ask("Telefone", default="")
    diagnosis = Prompt.ask("Diagnóstico", default="")
    allergies = Prompt.ask("Alergias", default="")
    medications = Prompt.ask("Medicação em uso", default="")
    return [name, birth_date, sex, phone, diagnosis, allergies, medications]


def send_command(stream, *fields: str) -> list[str]:
    """Envia um comando e devolve os campos da primeira linha de resposta."""
    stream.write(proto.build_message(*fields) + "\n")
    stream.flush()
    return proto.parse_message(stream.readline())


def read_list_response(stream, first_line_fields: list[str]) -> list[list[str]]:
    """Lê as restantes linhas de uma resposta LIST, até à sentinela END."""
    count = int(first_line_fields[1])
    rows = []
    for _ in range(count):
        rows.append(proto.parse_message(stream.readline()))
    stream.readline()  # consome a linha "END"
    return rows


def action_register(stream) -> None:
    data = prompt_patient_data()
    response = send_command(stream, proto.CMD_REGISTER, *data)
    if response[0] == proto.STATUS_OK:
        print_success(response[1])
    else:
        print_error(response[1])


def action_query(stream) -> None:
    patient_id = Prompt.ask("ID do paciente")
    response = send_command(stream, proto.CMD_QUERY, patient_id)
    if response[0] == proto.STATUS_OK:
        print_patient(response[1:])
    else:
        print_error(response[1])


def action_list(stream) -> None:
    response = send_command(stream, proto.CMD_LIST)
    rows = read_list_response(stream, response)
    if not rows:
        console.print("[yellow]Ainda não há pacientes registados.[/yellow]")
        return
    print_patients_table(rows)


def action_update(stream) -> None:
    patient_id = Prompt.ask("ID do paciente a atualizar")
    data = prompt_patient_data()
    response = send_command(stream, proto.CMD_UPDATE, patient_id, *data)
    if response[0] == proto.STATUS_OK:
        print_success(response[1])
    else:
        print_error(response[1])


def action_delete(stream) -> None:
    patient_id = Prompt.ask("ID do paciente a remover")
    if not Confirm.ask(f"Confirma a remoção do paciente [bold]{patient_id}[/bold]?"):
        console.print("Operação cancelada.")
        return
    response = send_command(stream, proto.CMD_DELETE, patient_id)
    if response[0] == proto.STATUS_OK:
        print_success(response[1])
    else:
        print_error(response[1])


MENU_ACTIONS = {
    "1": action_register,
    "2": action_query,
    "3": action_list,
    "4": action_update,
    "5": action_delete,
}


def print_menu() -> None:
    console.print(Panel.fit("[bold]Sistema de Informação Clínica[/bold]", border_style="cyan"))
    console.print(
        "1. Registar novo paciente\n"
        "2. Consultar paciente por ID\n"
        "3. Listar todos os pacientes\n"
        "4. Atualizar dados de paciente\n"
        "5. Remover paciente\n"
        "6. Sair"
    )


def main() -> None:
    try:
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_socket.connect((HOST, PORT))
    except ConnectionRefusedError:
        print_error("Não foi possível ligar ao servidor. Verifique se o servidor está em execução.")
        return

    stream = client_socket.makefile("rw", encoding="utf-8", newline="\n")

    try:
        while True:
            print_menu()
            choice = Prompt.ask("Escolha uma opção", choices=list(MENU_ACTIONS) + ["6"])
            if choice == "6":
                stream.write(proto.build_message(proto.CMD_QUIT) + "\n")
                stream.flush()
                break
            MENU_ACTIONS[choice](stream)
            console.print()
            Prompt.ask("Prima Enter para continuar", default="")
            console.clear()
    except (ConnectionResetError, BrokenPipeError):
        print_error("Ligação ao servidor perdida.")
    finally:
        client_socket.close()


if __name__ == "__main__":
    main()
