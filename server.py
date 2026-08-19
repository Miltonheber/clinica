"""Servidor TCP: aceita ligações e responde aos comandos do protocolo, uma thread por cliente."""

import socket
import sqlite3
import threading

import db
import protocol as proto
import validation

HOST = "127.0.0.1"
PORT = 5000


def parse_id(value: str) -> int | None:
    """Converte um id recebido do cliente para int, ou None se for inválido."""
    try:
        return int(value)
    except ValueError:
        return None


def handle_register(connection: sqlite3.Connection, fields: list[str]) -> str:
    """Trata o comando REGISTER: cria um novo paciente com id gerado automaticamente."""
    _, name, birth_date, sex, phone, diagnosis, allergies, medications = fields
    error = validation.validate_patient(name, birth_date, sex, phone,
                                         diagnosis, allergies, medications)
    if error:
        return proto.build_message(proto.STATUS_ERROR, error)
    new_id = db.register_patient(connection, name, birth_date, sex, phone,
                                  diagnosis, allergies, medications)
    return proto.build_message(proto.STATUS_OK, f"Paciente registado com sucesso (ID {new_id})")


def handle_query(connection: sqlite3.Connection, fields: list[str]) -> str:
    """Trata o comando QUERY: procura um paciente pelo id."""
    _, id_field = fields
    patient_id = parse_id(id_field)
    if patient_id is None:
        return proto.build_message(proto.STATUS_ERROR, "ID inválido")
    row = db.find_patient(connection, patient_id)
    if row is None:
        return proto.build_message(proto.STATUS_ERROR, "Paciente não encontrado")
    return proto.build_message(proto.STATUS_OK, *row)


def handle_list(connection: sqlite3.Connection) -> str:
    """Trata o comando LIST: devolve todos os pacientes, terminado por END."""
    rows = db.list_patients(connection)
    lines = [proto.build_message(proto.STATUS_OK, str(len(rows)))]
    for row in rows:
        lines.append(proto.build_message(*row))
    lines.append(proto.END_OF_LIST)
    return "\n".join(lines)


def handle_update(connection: sqlite3.Connection, fields: list[str]) -> str:
    """Trata o comando UPDATE: atualiza os dados de um paciente existente."""
    _, id_field, name, birth_date, sex, phone, diagnosis, allergies, medications = fields
    patient_id = parse_id(id_field)
    if patient_id is None:
        return proto.build_message(proto.STATUS_ERROR, "ID inválido")
    error = validation.validate_patient(name, birth_date, sex, phone,
                                         diagnosis, allergies, medications)
    if error:
        return proto.build_message(proto.STATUS_ERROR, error)
    updated = db.update_patient(connection, patient_id, name, birth_date, sex, phone,
                                 diagnosis, allergies, medications)
    if not updated:
        return proto.build_message(proto.STATUS_ERROR, "Paciente não encontrado")
    return proto.build_message(proto.STATUS_OK, "Paciente atualizado com sucesso")


def handle_delete(connection: sqlite3.Connection, fields: list[str]) -> str:
    """Trata o comando DELETE: remove um paciente pelo id."""
    _, id_field = fields
    patient_id = parse_id(id_field)
    if patient_id is None:
        return proto.build_message(proto.STATUS_ERROR, "ID inválido")
    deleted = db.delete_patient(connection, patient_id)
    if not deleted:
        return proto.build_message(proto.STATUS_ERROR, "Paciente não encontrado")
    return proto.build_message(proto.STATUS_OK, "Paciente removido com sucesso")


def dispatch(connection: sqlite3.Connection, line: str) -> str | None:
    """Interpreta uma linha recebida e devolve a resposta a enviar (None para QUIT)."""
    fields = proto.parse_message(line)
    command = fields[0]

    handlers = {
        proto.CMD_REGISTER: (handle_register, 8),
        proto.CMD_QUERY: (handle_query, 2),
        proto.CMD_LIST: (lambda conn, _: handle_list(conn), 1),
        proto.CMD_UPDATE: (handle_update, 9),
        proto.CMD_DELETE: (handle_delete, 2),
    }

    if command == proto.CMD_QUIT:
        return None

    if command not in handlers:
        return proto.build_message(proto.STATUS_ERROR, "Comando inválido")

    handler, expected_fields = handlers[command]
    if len(fields) != expected_fields:
        return proto.build_message(proto.STATUS_ERROR, "Comando inválido")

    return handler(connection, fields)


def handle_client(client_socket: socket.socket, address) -> None:
    """Atende um cliente numa thread própria, até ele enviar QUIT ou fechar a ligação."""
    print(f"Cliente ligado: {address}")
    connection = db.connect()
    stream = client_socket.makefile("rw", encoding="utf-8", newline="\n")
    try:
        for line in stream:
            response = dispatch(connection, line)
            if response is None:
                break
            stream.write(response + "\n")
            stream.flush()
    except (ConnectionResetError, BrokenPipeError):
        print(f"Ligação interrompida pelo cliente: {address}")
    finally:
        connection.close()
        client_socket.close()
        print(f"Cliente desligado: {address}")


def main() -> None:
    setup_connection = db.connect()
    db.create_table(setup_connection)
    setup_connection.close()

    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind((HOST, PORT))
    server_socket.listen()
    print(f"Servidor à escuta em {HOST}:{PORT}")

    try:
        while True:
            client_socket, address = server_socket.accept()
            threading.Thread(target=handle_client, args=(client_socket, address), daemon=True).start()
    except KeyboardInterrupt:
        print("\nServidor a encerrar")
    finally:
        server_socket.close()


if __name__ == "__main__":
    main()
