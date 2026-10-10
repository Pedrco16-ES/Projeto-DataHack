"""Gera a migration revisável a partir dos contratos oficiais versionados."""

from src.ingestion.schema import load_contract


def source_columns(source: str) -> list[str]:
    editions = [2024] if source == "trajetoria" else range(2021, 2025)
    return list(dict.fromkeys(c for year in editions for c in load_contract(source, year)["columns"]))


def build_ddl() -> str:
    sql = """-- Rota do Diploma, migration 001. Executar somente pelo runner transacional.
-- Schemas novos; não adota objetos existentes. Nenhum dado será publicado.
CREATE SCHEMA meta;
CREATE SCHEMA staging;
CREATE SCHEMA marts;
REVOKE ALL ON SCHEMA meta, staging, marts FROM PUBLIC;

CREATE TABLE meta.schema_versions (
    version text PRIMARY KEY,
    checksum text NOT NULL CHECK (checksum ~ '^[0-9a-f]{64}$'),
    installed_at timestamptz NOT NULL DEFAULT now()
);
CREATE TABLE meta.importacoes (
    batch_id text PRIMARY KEY CHECK (batch_id ~ '^[0-9a-f]{24}$'),
    source text NOT NULL CHECK (source IN ('trajetoria','censo_curso')),
    edition integer NOT NULL,
    file_sha256 text NOT NULL CHECK (file_sha256 ~ '^[0-9a-f]{64}$'),
    report_sha256 text NOT NULL CHECK (report_sha256 ~ '^[0-9a-f]{64}$'),
    accepted_sha256 text NOT NULL CHECK (accepted_sha256 ~ '^[0-9a-f]{64}$'),
    contract_sha256 text NOT NULL CHECK (contract_sha256 ~ '^[0-9a-f]{64}$'),
    pipeline_sha256 text NOT NULL CHECK (pipeline_sha256 ~ '^[0-9a-f]{64}$'),
    received bigint NOT NULL CHECK (received >= 0),
    accepted bigint NOT NULL CHECK (accepted > 0),
    rejected bigint NOT NULL CHECK (rejected >= 0),
    excluded bigint NOT NULL CHECK (excluded >= 0),
    status text NOT NULL CHECK (status IN ('loaded','withdrawn')),
    public_approved boolean NOT NULL DEFAULT false CHECK (NOT public_approved),
    loaded_at timestamptz NOT NULL DEFAULT now(),
    withdrawn_at timestamptz,
    CHECK (received = accepted + rejected + excluded),
    CHECK ((status='withdrawn') = (withdrawn_at IS NOT NULL))
);
CREATE UNIQUE INDEX importacoes_active_edition ON meta.importacoes(source, edition) WHERE status='loaded';
CREATE TABLE meta.validacoes (
    batch_id text PRIMARY KEY REFERENCES meta.importacoes(batch_id),
    report jsonb NOT NULL CHECK (jsonb_typeof(report) = 'object')
);
CREATE TABLE meta.eventos (
    event_id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    batch_id text NOT NULL REFERENCES meta.importacoes(batch_id),
    action text NOT NULL CHECK (action IN ('load','withdraw')),
    reason text NOT NULL,
    created_at timestamptz NOT NULL DEFAULT now()
);
"""
    for source in ["trajetoria", "censo_curso"]:
        contract = load_contract(source, 2024)
        parts = ["batch_id text NOT NULL REFERENCES meta.importacoes(batch_id)",
                 "source_record_number bigint NOT NULL CHECK (source_record_number > 0)"]
        for column in source_columns(source):
            name = column.lower()
            required = column in contract["key"] or column in {"CO_UF", "TP_MODALIDADE_ENSINO", "CO_MUNICIPIO"}
            dtype = "numeric" if column in {"TAP", "TCA", "TDA", "TCAN", "TADA"} else "bigint" if column.startswith(("QT_", "NU_")) else "text"
            definition = f'"{name}" {dtype}' + (" NOT NULL" if required else "")
            if dtype == "bigint":
                definition += f' CHECK ("{name}" >= 0)'
            elif dtype == "numeric":
                definition += f' CHECK ("{name}" BETWEEN 0 AND 100)'
            if column == "CO_UF":
                definition += " CHECK (co_uf = '51')"
            if column == "CO_MUNICIPIO":
                definition += " CHECK (co_municipio ~ '^51[0-9]{5}$')"
            if column == "TP_MODALIDADE_ENSINO":
                definition += " CHECK (tp_modalidade_ensino IN ('1','2'))"
            parts.append(definition)
        key = ", ".join('"' + c.lower() + '"' for c in contract["key"])
        parts.extend([f"PRIMARY KEY (batch_id, {key})", "UNIQUE (batch_id, source_record_number)"])
        if source == "trajetoria":
            parts.append("CHECK (nu_ano_referencia >= nu_ano_ingresso)")
        else:
            parts.append("CHECK (tp_dimensao IN ('1','2') AND tp_dimensao = tp_modalidade_ensino)")
        sql += f'\nCREATE TABLE staging.{source} (\n    ' + ",\n    ".join(parts) + "\n);\n"
        sql += f"CREATE INDEX {source}_municipio ON staging.{source}(co_municipio);\n"
        sql += f"CREATE VIEW staging.{source}_atual WITH (security_invoker=true) AS\n SELECT i.edition AS source_edition, t.* FROM staging.{source} t\n JOIN meta.importacoes i USING (batch_id) WHERE i.status='loaded';\n"
    sql += """
-- Sem políticas: contas sem privilégios de proprietário não leem staging/meta.
ALTER TABLE staging.trajetoria ENABLE ROW LEVEL SECURITY;
ALTER TABLE staging.censo_curso ENABLE ROW LEVEL SECURITY;
ALTER TABLE meta.importacoes ENABLE ROW LEVEL SECURITY;
ALTER TABLE meta.validacoes ENABLE ROW LEVEL SECURITY;
ALTER TABLE meta.eventos ENABLE ROW LEVEL SECURITY;
ALTER TABLE meta.schema_versions ENABLE ROW LEVEL SECURITY;
REVOKE ALL ON ALL TABLES IN SCHEMA meta, staging, marts FROM PUBLIC;
REVOKE ALL ON ALL SEQUENCES IN SCHEMA meta, staging, marts FROM PUBLIC;
ALTER DEFAULT PRIVILEGES IN SCHEMA meta, staging, marts REVOKE ALL ON TABLES FROM PUBLIC;
ALTER DEFAULT PRIVILEGES IN SCHEMA meta, staging, marts REVOKE ALL ON SEQUENCES FROM PUBLIC;
-- Impede herança de grants públicos do Supabase nos schemas recém-criados.
DO $access$
DECLARE role_name text;
BEGIN
  FOREACH role_name IN ARRAY ARRAY['anon','authenticated'] LOOP
    IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname=role_name) THEN
      EXECUTE format('REVOKE ALL ON SCHEMA meta, staging, marts FROM %I', role_name);
      EXECUTE format('REVOKE ALL ON ALL TABLES IN SCHEMA meta, staging, marts FROM %I', role_name);
      EXECUTE format('REVOKE ALL ON ALL SEQUENCES IN SCHEMA meta, staging, marts FROM %I', role_name);
      EXECUTE format('ALTER DEFAULT PRIVILEGES IN SCHEMA meta, staging, marts REVOKE ALL ON TABLES FROM %I', role_name);
      EXECUTE format('ALTER DEFAULT PRIVILEGES IN SCHEMA meta, staging, marts REVOKE ALL ON SEQUENCES FROM %I', role_name);
    END IF;
  END LOOP;
END $access$;
"""
    return sql
