"""Validação dos dados de um paciente antes de serem gravados na base de dados."""

from datetime import date

SEX_VALUES = {"M", "F", "O"}


def validate_patient(name: str, birth_date: str, sex: str, phone: str,
                      diagnosis: str, allergies: str, medications: str) -> str | None:
    """Valida os campos de um paciente. Devolve a mensagem de erro, ou None se estiver tudo válido."""
    if not name.strip():
        return "O nome do paciente é obrigatório"

    try:
        parsed_date = date.fromisoformat(birth_date)
    except ValueError:
        return "Data de nascimento inválida (use o formato AAAA-MM-DD)"
    if parsed_date > date.today():
        return "Data de nascimento não pode ser no futuro"

    if sex and sex.upper() not in SEX_VALUES:
        return "Sexo inválido (use M, F ou O)"

    if phone and not phone.replace(" ", "").isdigit():
        return "Telefone inválido (use apenas dígitos)"

    return None
