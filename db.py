"""Acesso a dados dos pacientes em SQLite. Sem ORM, apenas SQL direto."""

import sqlite3

DB_FILE = "clinica.db"

# Ordem dos campos usada em toda a camada de dados e no protocolo.
FIELDS = ("id", "name", "birth_date", "sex", "phone", "diagnosis", "allergies", "medications")


def connect() -> sqlite3.Connection:
    """Abre a ligação ao ficheiro SQLite do projeto."""
    connection = sqlite3.connect(DB_FILE)
    connection.execute("PRAGMA busy_timeout = 5000")
    return connection


def create_table(connection: sqlite3.Connection) -> None:
    """Cria a tabela de pacientes se ainda não existir."""
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS patients (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            name         TEXT NOT NULL,
            birth_date   TEXT NOT NULL,
            sex          TEXT,
            phone        TEXT,
            diagnosis    TEXT,
            allergies    TEXT,
            medications  TEXT
        )
        """
    )
    connection.commit()


def register_patient(connection: sqlite3.Connection, name, birth_date, sex, phone,
                      diagnosis, allergies, medications) -> int:
    """Insere um novo paciente. Devolve o id gerado automaticamente."""
    cursor = connection.execute(
        "INSERT INTO patients (name, birth_date, sex, phone, diagnosis, allergies, medications) "
        "VALUES (?, ?, ?, ?, ?, ?, ?)",
        (name, birth_date, sex, phone, diagnosis, allergies, medications),
    )
    connection.commit()
    return cursor.lastrowid


def find_patient(connection: sqlite3.Connection, patient_id: int) -> tuple | None:
    """Devolve a linha do paciente com este id, ou None se não existir."""
    cursor = connection.execute("SELECT * FROM patients WHERE id = ?", (patient_id,))
    return cursor.fetchone()


def list_patients(connection: sqlite3.Connection) -> list[tuple]:
    """Devolve todas as linhas de pacientes, ordenadas por id."""
    cursor = connection.execute("SELECT * FROM patients ORDER BY id")
    return cursor.fetchall()


def update_patient(connection: sqlite3.Connection, patient_id, name, birth_date, sex, phone,
                    diagnosis, allergies, medications) -> bool:
    """Atualiza um paciente existente. Devolve False se o id não existir."""
    cursor = connection.execute(
        """
        UPDATE patients
        SET name = ?, birth_date = ?, sex = ?, phone = ?,
            diagnosis = ?, allergies = ?, medications = ?
        WHERE id = ?
        """,
        (name, birth_date, sex, phone, diagnosis, allergies, medications, patient_id),
    )
    connection.commit()
    return cursor.rowcount > 0


def delete_patient(connection: sqlite3.Connection, patient_id: int) -> bool:
    """Remove um paciente pelo id. Devolve False se o id não existir."""
    cursor = connection.execute("DELETE FROM patients WHERE id = ?", (patient_id,))
    connection.commit()
    return cursor.rowcount > 0
