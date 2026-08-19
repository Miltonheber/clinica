# Clínica — Sistema de Informação Clínica (TCP Sockets)

Exercício de sockets TCP em Python: um servidor guarda dados de pacientes em SQLite e um cliente de terminal consulta e gere esses dados através de um protocolo de texto simples.

## Objetivo

O cliente informa o id de um paciente e o servidor responde com os dados desse paciente. Inclui CRUD completo: registar, consultar, listar, atualizar e remover pacientes.

## Como correr

```bash
pip install -r requirements.txt

# Terminal 1
python3 server.py

# Terminal 2
python3 client.py
```

O servidor escuta em `127.0.0.1:5000` (constantes `HOST`/`PORT` no topo de `server.py`/`client.py`). Os dados ficam em `clinica.db`, criado automaticamente na primeira execução do servidor.

## Estrutura

| Ficheiro | Responsabilidade |
|---|---|
| `protocol.py` | Contrato de mensagens entre cliente e servidor (comandos, separador, helpers) |
| `validation.py` | Validação dos dados de um paciente antes de gravar |
| `db.py` | Acesso a dados (SQLite), sem ORM |
| `server.py` | Servidor TCP: aceita um cliente de cada vez, despacha comandos |
| `client.py` | Cliente TCP: menu de terminal com interface `rich`, que limpa o ecrã entre operações |

## Protocolo

Texto simples, uma mensagem por linha (`\n`), campos separados por `|`. TCP é um stream de bytes sem limites de mensagem — por isso cada mensagem termina em newline e é lida com `readline()` via `socket.makefile()`.

**Cliente → servidor:**
| Comando | Formato |
|---|---|
| Registar | `REGISTER\|name\|birth_date\|sex\|phone\|diagnosis\|allergies\|medications` |
| Consultar | `QUERY\|id` |
| Listar | `LIST` |
| Atualizar | `UPDATE\|id\|name\|birth_date\|sex\|phone\|diagnosis\|allergies\|medications` |
| Remover | `DELETE\|id` |
| Sair | `QUIT` |

**Servidor → cliente:**
| Resposta | Formato |
|---|---|
| Sucesso genérico | `OK\|message` (no `REGISTER`, a mensagem inclui o id gerado) |
| Sucesso com paciente | `OK\|id\|name\|birth_date\|sex\|phone\|diagnosis\|allergies\|medications` |
| Sucesso com lista | `OK\|n`, seguido de `n` linhas de paciente, terminado por `END` |
| Erro | `ERROR\|message` |

As palavras-chave do protocolo ficam em inglês (camada de código); o texto de `message` é sempre em português, porque é isso que o cliente mostra ao utilizador.

## Validação

Antes de gravar (`REGISTER`/`UPDATE`), o servidor valida os campos em `validation.py` e devolve `ERROR|mensagem` no primeiro problema encontrado:

- `name` é obrigatório (não pode ficar vazio).
- `birth_date` tem de ser uma data válida no formato `AAAA-MM-DD` e não pode ser no futuro.
- `sex`, se preenchido, tem de ser `M`, `F` ou `O`.
- `phone`, se preenchido, só pode conter dígitos (e espaços).

Em `QUERY`/`UPDATE`/`DELETE`, se o `id` enviado não for um número, o servidor devolve `ERROR|ID inválido` sem tocar na base de dados.

## Base de dados

Tabela única `patients`:

```sql
CREATE TABLE patients (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    name         TEXT NOT NULL,
    birth_date   TEXT NOT NULL,
    sex          TEXT,
    phone        TEXT,
    diagnosis    TEXT,
    allergies    TEXT,
    medications  TEXT
)
```

`id` é gerado automaticamente pelo SQLite (`AUTOINCREMENT`) no `REGISTER`; o cliente não o escolhe, apenas o recebe na resposta e usa-o depois para `QUERY`/`UPDATE`/`DELETE`.

## Modelo de concorrência

O servidor atende **um cliente de cada vez** (loop simples de `accept()`, sem threads) — suficiente para o requisito e mais fácil de seguir passo a passo. Uma evolução natural para atender vários clientes em simultâneo seria criar uma `threading.Thread` por ligação aceite, com cuidado extra na partilha da ligação SQLite entre threads.

## Próximos passos possíveis

- Expor o servidor ao browser através de uma ponte WebSocket (mantendo o servidor TCP interno).
- Suporte a múltiplos clientes em simultâneo com `threading`.
# clinica
