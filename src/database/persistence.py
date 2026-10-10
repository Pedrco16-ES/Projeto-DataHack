"""Plano verificável, migration e carga transacional de lotes privados."""

from dataclasses import dataclass
from decimal import Decimal
import hashlib
import json
from pathlib import Path
import re

import pandas as pd
from psycopg import sql
from sqlalchemy import text
from sqlalchemy.engine import Engine

from src.config import PROJECT_ROOT
from src.database.ddl import source_columns
from src.ingestion.pipeline import sha256, verify_existing, pipeline_digest
from src.ingestion.schema import load_contract, IngestionError
from src.processing.validation import clean_strings, validate_rows

MIGRATION = PROJECT_ROOT / "sql/001_staging.sql"
LOCK_ID = 7240162026


class PersistenceError(ValueError):
    """Mensagem administrativa segura, sem valores de linhas ou credenciais."""


@dataclass
class PreparedBatch:
    report: dict
    frame: pd.DataFrame
    report_sha256: str


def prepare_batch(path: Path) -> PreparedBatch:
    path = Path(path).resolve()
    try:
        report_hash = sha256(path / "report.json")
        report = verify_existing(path)
        contract = load_contract(report["source"], report["edition"])
        if report["contract_sha256"] != contract["contract_sha256"] or report["pipeline_sha256"] != pipeline_digest():
            raise PersistenceError("Contrato ou pipeline mudou; revise e reprocesse o lote antes da carga.")
        if report["key"] != contract["key"]:
            raise PersistenceError("Chave do lote incompatível com o contrato.")
        decision = {k: report[k] for k in ["source", "edition", "file_sha256", "contract_sha256", "pipeline_sha256",
                                         "mapping", "mapping_reason", "member", "sheet", "encoding", "separator"]}
        expected_id = hashlib.sha256(json.dumps(decision, sort_keys=True).encode()).hexdigest()[:24]
        if report["batch_id"] != expected_id or path.name != expected_id:
            raise PersistenceError("Identificador do lote não corresponde às decisões registradas.")
        for name in ["file_sha256", "contract_sha256", "pipeline_sha256"]:
            if not re.fullmatch(r"[0-9a-f]{64}", report[name]):
                raise PersistenceError("Hash inválido no relatório.")
        frame = pd.read_csv(path / "accepted.csv", dtype="string", keep_default_na=False)
        expected_columns = report["layout"]["columns"] + ["_record_number"]
        if report["source"] == "trajetoria":
            expected_columns += ["ANOS_DESDE_INGRESSO"]
        if frame.columns.tolist() != expected_columns:
            raise PersistenceError("Colunas tratadas divergentes do relatório.")
        if set(report["layout"]["columns"]) - set(contract["columns"]):
            raise PersistenceError("Coluna sem contrato oficial.")
        clean = clean_strings(frame)
        treated, errors = validate_rows(clean, contract)
        if errors.ne("").any() or not clean.CO_UF.eq("51").all() or clean.duplicated(contract["key"]).any():
            raise PersistenceError("Registros aceitos falharam na revalidação de chaves, tipos ou recorte MT.")
        source_rows = pd.to_numeric(clean["_record_number"], errors="coerce")
        counts = report["counts"]
        if source_rows.isna().any() or source_rows.duplicated().any() or (source_rows % 1 != 0).any() or not source_rows.between(1, counts["received"]).all():
            raise PersistenceError("Posições dos registros inválidas.")
        for name in ["received", "accepted", "rejected", "excluded"]:
            if type(counts[name]) is not int or counts[name] < 0:
                raise PersistenceError("Contagens inválidas.")
        if not len(frame) or len(frame) != counts["accepted"] or counts["received"] != sum(counts[k] for k in ["accepted", "rejected", "excluded"]):
            raise PersistenceError("Contagens do lote não reconciliam ou não há registros aceitos.")
        for file, key in [("rejected.csv", "rejected"), ("excluded.csv", "excluded")]:
            actual_count = sum(len(chunk) for chunk in pd.read_csv(path / file, usecols=["_record_number"], chunksize=50000))
            if actual_count != counts[key]:
                raise PersistenceError("Contagens de rejeições/exclusões divergentes.")
        # Releitura dos hashes fecha a janela de alteração dos arquivos durante a preparação.
        verify_existing(path)
        if sha256(path / "report.json") != report_hash:
            raise PersistenceError("Relatório mudou durante a revisão.")
        return PreparedBatch(report, treated, report_hash)
    except (KeyError, OSError, IngestionError, TypeError):
        raise PersistenceError("Lote incompleto ou incompatível; consulte os relatórios locais.") from None


def make_plan(paths: list[Path]) -> dict:
    items = []
    seen = set()
    for path in paths:
        batch = prepare_batch(path)
        report = batch.report
        scope = (report["source"], report["edition"])
        if scope in seen:
            raise PersistenceError("Plano contém mais de um lote para a mesma fonte/edição.")
        seen.add(scope)
        items.append({"batch_id": report["batch_id"], "batch_dir": str(Path(path).resolve()),
                      "source": scope[0], "edition": scope[1], "counts": report["counts"],
                      "report_sha256": batch.report_sha256, "accepted_sha256": report["artifacts"]["accepted.csv"]})
    if not items:
        raise PersistenceError("Plano sem lotes.")
    return {"version": 1, "migration_sha256": sha256(MIGRATION), "batches": items,
            "total_rows": sum(item["counts"]["accepted"] for item in items),
            "publication": "private_staging_only", "replacement": "blocked"}


def verify_plan(plan: dict):
    if plan.get("version") != 1 or plan.get("migration_sha256") != sha256(MIGRATION):
        raise PersistenceError("Migration ou versão do plano mudou; gere novo plano.")
    current = make_plan([Path(item["batch_dir"]) for item in plan["batches"]])
    if current != plan:
        raise PersistenceError("Lotes ou decisões mudaram após a revisão; gere novo plano.")


def lock(conn):
    conn.execute(text("SET LOCAL lock_timeout = '5s'"))
    conn.execute(text("SELECT pg_advisory_xact_lock(:key)"), {"key": LOCK_ID})


def migrate(engine: Engine) -> bool:
    """Retorna False quando a migration já está aplicada com o mesmo checksum."""
    with engine.begin() as conn:
        lock(conn)
        existing = conn.execute(text("SELECT nspname FROM pg_namespace WHERE nspname IN ('meta','staging','marts')")).scalars().all()
        if existing:
            table = conn.execute(text("SELECT to_regclass('meta.schema_versions')")).scalar_one()
            if set(existing) == {"meta", "staging", "marts"} and table:
                checksum = conn.execute(text("SELECT checksum FROM meta.schema_versions WHERE version='001'")).scalar_one_or_none()
                if checksum == sha256(MIGRATION):
                    return False
            raise PersistenceError("Schemas existentes não pertencem à migration reconhecida. Nenhum objeto será adotado ou alterado.")
        conn.connection.driver_connection.execute(MIGRATION.read_text(encoding="utf-8"), prepare=False)
        conn.execute(text("INSERT INTO meta.schema_versions(version, checksum) VALUES ('001',:checksum)"), {"checksum": sha256(MIGRATION)})
    return True


def require_migration(conn):
    if conn.execute(text("SELECT to_regclass('meta.schema_versions')")).scalar_one() is None:
        raise PersistenceError("Migration 001 ainda não aplicada.")
    if conn.execute(text("SELECT checksum FROM meta.schema_versions WHERE version='001'")).scalar_one_or_none() != sha256(MIGRATION):
        raise PersistenceError("Checksum da migration diverge do código revisado.")


def rows_for_copy(batch: PreparedBatch):
    columns = source_columns(batch.report["source"])
    frame = batch.frame.reindex(columns=["_record_number"] + columns)
    for row in frame.itertuples(index=False, name=None):
        values = [batch.report["batch_id"], int(row[0])]
        for column, value in zip(columns, row[1:]):
            if pd.isna(value):
                values.append(None)
            elif column.startswith(("QT_", "NU_")):
                values.append(int(value))
            elif column in {"TAP", "TCA", "TDA", "TCAN", "TADA"}:
                values.append(Decimal(str(value)))
            else:
                values.append(str(value))
        yield tuple(values)


def load_one(conn, batch: PreparedBatch) -> str:
    report = batch.report
    batch_id, source = report["batch_id"], report["source"]
    existing = conn.execute(text("SELECT status, report_sha256, accepted_sha256, accepted FROM meta.importacoes WHERE batch_id=:id"), {"id": batch_id}).mappings().one_or_none()
    if existing:
        if existing["status"] != "loaded":
            raise PersistenceError("Lote retirado: não será reativado automaticamente.")
        if existing["report_sha256"] != batch.report_sha256 or existing["accepted_sha256"] != report["artifacts"]["accepted.csv"]:
            raise PersistenceError("Mesmo lote com conteúdo divergente no banco.")
        count = conn.execute(text(f"SELECT count(*) FROM staging.{source} WHERE batch_id=:id"), {"id": batch_id}).scalar_one()
        if count != existing["accepted"] or count != len(batch.frame):
            raise PersistenceError("Contagem persistida diverge do lote; repetição bloqueada.")
        return "reused"
    conflict = conn.execute(text("SELECT batch_id FROM meta.importacoes WHERE source=:source AND edition=:edition AND status='loaded'"),
                            {"source": source, "edition": report["edition"]}).scalar_one_or_none()
    if conflict:
        raise PersistenceError("Já há um lote ativo para esta fonte/edição. Substituição exige revisão e retirada explícita.")
    params = {k: report[k] for k in ["batch_id", "source", "edition", "file_sha256", "contract_sha256", "pipeline_sha256"]}
    params.update({"report_sha256": batch.report_sha256, "accepted_sha256": report["artifacts"]["accepted.csv"],
                   **{k: report["counts"][k] for k in ["received", "accepted", "rejected", "excluded"]}})
    columns = ", ".join(params)
    bindings = ", ".join(":" + k for k in params)
    conn.execute(text(f"INSERT INTO meta.importacoes({columns},status) VALUES ({bindings},'loaded')"), params)
    dbapi = conn.connection.driver_connection
    table_identifier = sql.Identifier("staging", source)
    target_columns = ["batch_id", "source_record_number"] + [c.lower() for c in source_columns(source)]
    identifiers = sql.SQL(", ").join(sql.Identifier(c) for c in target_columns)
    with dbapi.cursor() as cursor:
        cursor.execute(sql.SQL("CREATE TEMP TABLE rota_load (LIKE {} INCLUDING DEFAULTS INCLUDING CONSTRAINTS) ON COMMIT DROP").format(table_identifier))
        with cursor.copy(sql.SQL("COPY pg_temp.rota_load ({}) FROM STDIN").format(identifiers)) as copy:
            for row in rows_for_copy(batch):
                copy.write_row(row)
        cursor.execute("SELECT count(*) FROM pg_temp.rota_load")
        if cursor.fetchone()[0] != report["counts"]["accepted"]:
            raise PersistenceError("Contagem temporária divergente; carga cancelada.")
        cursor.execute(sql.SQL("INSERT INTO {} ({}) SELECT {} FROM pg_temp.rota_load").format(table_identifier, identifiers, identifiers))
        cursor.execute("DROP TABLE pg_temp.rota_load")
    count = conn.execute(text(f"SELECT count(*) FROM staging.{source} WHERE batch_id=:id"), {"id": batch_id}).scalar_one()
    if count != report["counts"]["accepted"]:
        raise PersistenceError("Contagem final divergente; carga cancelada.")
    stored_report = {k: v for k, v in report.items() if k not in {"batch_dir", "reused"}}
    conn.execute(text("INSERT INTO meta.validacoes(batch_id,report) VALUES (:id,CAST(:report AS jsonb))"),
                 {"id": batch_id, "report": json.dumps(stored_report, ensure_ascii=False)})
    conn.execute(text("INSERT INTO meta.eventos(batch_id,action,reason) VALUES (:id,'load','Carga estrutural privada; aprovação pública pendente')"), {"id": batch_id})
    return "loaded"


def apply_plan(engine: Engine, plan: dict) -> list[dict]:
    verify_plan(plan)
    result = []
    with engine.begin() as conn:
        lock(conn)
        require_migration(conn)
        # COPY dos arquivos nacionais tratados pode superar o limite das consultas
        # interativas. O ajuste vale somente nesta transação e não altera o servidor.
        conn.execute(text("SET LOCAL statement_timeout = '180s'"))
        for item in plan["batches"]:
            batch = prepare_batch(Path(item["batch_dir"]))
            if batch.report_sha256 != item["report_sha256"]:
                raise PersistenceError("Lote mudou durante a carga; transação cancelada.")
            result.append({"batch_id": item["batch_id"], "status": load_one(conn, batch), "rows": len(batch.frame)})
    return result


def withdraw_batches(engine: Engine, batch_ids: list[str], reason: str) -> int:
    if not batch_ids or not reason.strip() or any(not re.fullmatch(r"[0-9a-f]{24}", i) for i in batch_ids):
        raise PersistenceError("Informe lotes válidos e justificativa para retirada.")
    changed = 0
    with engine.begin() as conn:
        lock(conn)
        require_migration(conn)
        for batch_id in dict.fromkeys(batch_ids):
            status = conn.execute(text("SELECT status FROM meta.importacoes WHERE batch_id=:id"), {"id": batch_id}).scalar_one_or_none()
            if status is None:
                raise PersistenceError("Lote não encontrado; retirada cancelada integralmente.")
            if status == "withdrawn":
                continue
            conn.execute(text("UPDATE meta.importacoes SET status='withdrawn', withdrawn_at=now() WHERE batch_id=:id"), {"id": batch_id})
            conn.execute(text("INSERT INTO meta.eventos(batch_id,action,reason) VALUES (:id,'withdraw',:reason)"), {"id": batch_id, "reason": reason})
            changed += 1
    return changed
