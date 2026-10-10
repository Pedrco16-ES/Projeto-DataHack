"""Contratos versionados confrontados com os dicionários locais do INEP."""

from pathlib import Path
import hashlib
import json
import re
import unicodedata


class IngestionError(ValueError):
    """Falha legível de contrato ou arquivo; não inclui conteúdo de registros."""


def column_name(value) -> str:
    value = unicodedata.normalize("NFKD", str(value).strip().lstrip("\ufeff"))
    value = "".join(c for c in value if not unicodedata.combining(c))
    return re.sub(r"[^A-Z0-9]+", "_", value.upper()).strip("_")


def load_contract(source: str, edition: int) -> dict:
    if source not in {"trajetoria", "censo_curso"}:
        raise IngestionError("Fonte não suportada. Use trajetoria ou censo_curso.")
    path = Path(__file__).parent / "contracts" / f"{source}_{int(edition)}.json"
    if not path.is_file():
        raise IngestionError("Edição sem contrato validado. Não será inferido um esquema de outro ano.")
    data = path.read_bytes()
    contract = json.loads(data)
    contract["contract_sha256"] = hashlib.sha256(data).hexdigest()
    return contract


def resolve_columns(columns, contract: dict, mapping: dict | None = None) -> list[str]:
    mapping = mapping or {}
    if set(mapping) - {column_name(c) for c in columns}:
        raise IngestionError("Mapeamento menciona coluna de origem inexistente.")
    names = [mapping.get(column_name(c), column_name(c)) for c in columns]
    if len(set(names)) != len(names):
        raise IngestionError("Colunas duplicadas após normalização/mapeamento. Revise a origem.")
    missing = set(contract["required"]) - set(names)
    unknown = set(names) - set(contract["columns"])
    if missing:
        raise IngestionError("Colunas obrigatórias ausentes: " + ", ".join(sorted(missing)))
    if unknown:
        raise IngestionError("Colunas fora do contrato; confirme um mapeamento ou revise o dicionário.")
    return names


def validate_mapping(mapping, confirmed: bool, reason: str) -> dict:
    if not mapping:
        return {}
    if not confirmed or not reason.strip():
        raise IngestionError("Mapeamento manual exige confirmação e justificativa registrada.")
    if not isinstance(mapping, dict) or not all(isinstance(k, str) and isinstance(v, str) for k, v in mapping.items()):
        raise IngestionError("Mapeamento deve ser um objeto JSON de nomes de colunas.")
    normalized = {column_name(k): column_name(v) for k, v in mapping.items()}
    if len(normalized) != len(mapping):
        raise IngestionError("Mapeamento contém nomes de origem ambíguos.")
    return normalized
