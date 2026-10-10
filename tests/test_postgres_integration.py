"""Executa somente em cluster explicitamente local do helper de testes."""

import os
from pathlib import Path
import uuid

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url
from sqlalchemy.exc import IntegrityError

from src.database.persistence import migrate, make_plan, apply_plan, withdraw_batches, PersistenceError
from src.ingestion.pipeline import process_file
from tests.test_ingestion import census, save_csv

pytestmark = pytest.mark.skipif(not os.environ.get("ROTA_TEST_DATABASE_URL"), reason="Use scripts/test_postgres.py para PostgreSQL isolado")


@pytest.fixture
def engine():
    url = make_url(os.environ["ROTA_TEST_DATABASE_URL"])
    assert url.host == "127.0.0.1" and url.database == "rota_stage4_test" and url.username == "rota_test"
    admin = create_engine(url, isolation_level="AUTOCOMMIT")
    name = "rota_case_" + uuid.uuid4().hex
    with admin.connect() as conn:
        conn.execute(text(f'CREATE DATABASE "{name}"'))
    admin.dispose()
    database = create_engine(url.set(database=name), hide_parameters=True)
    try:
        yield database
    finally:
        database.dispose()


def plan_for(tmp_path, *, year=2024, count="30"):
    path = save_csv(tmp_path, [census(NU_ANO_CENSO=str(year), QT_MAT=count)])
    batch = process_file(path, "censo_curso", year, output_root=tmp_path / "processed")
    return make_plan([Path(batch["batch_dir"])])


def test_migration_idempotent_and_does_not_adopt_existing_schema(engine):
    with engine.begin() as conn:
        conn.execute(text("CREATE SCHEMA staging"))
    with pytest.raises(PersistenceError, match="existentes"):
        migrate(engine)
    with engine.connect() as conn:
        assert conn.execute(text("SELECT to_regnamespace('meta')")).scalar_one() is None


def test_load_twice_preserves_codes_counts_and_audit(engine, tmp_path, monkeypatch):
    import src.database.persistence as persistence
    original = persistence.load_one
    observed_timeouts = []
    def check_timeout(conn, batch):
        observed_timeouts.append(conn.execute(text("SHOW statement_timeout")).scalar_one())
        return original(conn, batch)
    monkeypatch.setattr(persistence, "load_one", check_timeout)
    assert migrate(engine)
    assert migrate(engine) is False
    plan = plan_for(tmp_path)
    assert apply_plan(engine, plan)[0]["status"] == "loaded"
    assert apply_plan(engine, plan)[0]["status"] == "reused"
    assert observed_timeouts == ["3min", "3min"]
    with engine.connect() as conn:
        assert conn.execute(text("SHOW statement_timeout")).scalar_one() != "3min"
        assert conn.execute(text("SELECT count(*) FROM staging.censo_curso")).scalar_one() == 1
        assert conn.execute(text("SELECT co_curso FROM staging.censo_curso")).scalar_one() == "00123"
        assert conn.execute(text("SELECT count(*) FROM meta.eventos")).scalar_one() == 1
        assert conn.execute(text("SELECT public_approved FROM meta.importacoes")).scalar_one() is False


def test_mid_load_failure_rolls_back_every_batch(engine, tmp_path, monkeypatch):
    import src.database.persistence as persistence
    migrate(engine)
    first = plan_for(tmp_path, year=2023)
    second = plan_for(tmp_path, year=2024)
    plan = make_plan([Path(first["batches"][0]["batch_dir"]), Path(second["batches"][0]["batch_dir"])])
    original = persistence.load_one
    calls = 0
    def fail_second(conn, batch):
        nonlocal calls
        calls += 1
        result = original(conn, batch)
        if calls == 2:
            raise RuntimeError("falha didática após COPY")
        return result
    monkeypatch.setattr(persistence, "load_one", fail_second)
    with pytest.raises(RuntimeError):
        apply_plan(engine, plan)
    with engine.connect() as conn:
        assert conn.execute(text("SELECT count(*) FROM staging.censo_curso")).scalar_one() == 0
        assert conn.execute(text("SELECT count(*) FROM meta.importacoes")).scalar_one() == 0
        assert conn.execute(text("SELECT count(*) FROM meta.eventos")).scalar_one() == 0


def test_conflicting_edition_blocked_and_withdraw_preserves_history(engine, tmp_path):
    migrate(engine)
    first = plan_for(tmp_path)
    apply_plan(engine, first)
    second = plan_for(tmp_path, count="31")
    with pytest.raises(PersistenceError, match="ativo"):
        apply_plan(engine, second)
    ids = [first["batches"][0]["batch_id"]]
    assert withdraw_batches(engine, ids, "teste de reversão") == 1
    assert withdraw_batches(engine, ids, "repetição") == 0
    with engine.connect() as conn:
        assert conn.execute(text("SELECT count(*) FROM staging.censo_curso")).scalar_one() == 1
        assert conn.execute(text("SELECT count(*) FROM staging.censo_curso_atual")).scalar_one() == 0
    with pytest.raises(PersistenceError, match="retirado"):
        apply_plan(engine, first)
    assert apply_plan(engine, second)[0]["status"] == "loaded"
    with engine.connect() as conn:
        assert conn.execute(text("SELECT count(*) FROM staging.censo_curso")).scalar_one() == 2
        assert conn.execute(text("SELECT count(*) FROM staging.censo_curso_atual")).scalar_one() == 1


def test_database_constraints_and_private_permissions(engine, tmp_path):
    migrate(engine)
    apply_plan(engine, plan_for(tmp_path))
    with pytest.raises(IntegrityError):
        with engine.begin() as conn:
            conn.execute(text("UPDATE staging.censo_curso SET qt_mat=-1"))
    with engine.begin() as conn:
        role = "reader_" + uuid.uuid4().hex
        conn.execute(text(f'CREATE ROLE "{role}" NOLOGIN'))
        assert conn.execute(text("SELECT has_schema_privilege(:role,'staging','USAGE')"), {"role": role}).scalar_one() is False
        assert conn.execute(text("SELECT has_table_privilege(:role,'staging.censo_curso','SELECT')"), {"role": role}).scalar_one() is False
        assert conn.execute(text("SELECT relrowsecurity FROM pg_class WHERE oid='staging.censo_curso'::regclass")).scalar_one() is True


def test_failed_migration_rolls_back_ddl(engine, tmp_path, monkeypatch):
    import src.database.persistence as persistence
    path = tmp_path / "broken.sql"
    path.write_text("CREATE SCHEMA staging; SELECT 1/0;", encoding="utf-8")
    monkeypatch.setattr(persistence, "MIGRATION", path)
    with pytest.raises(Exception):
        migrate(engine)
    with engine.connect() as conn:
        assert conn.execute(text("SELECT to_regnamespace('staging')")).scalar_one() is None


def test_supabase_style_default_grants_revoked(engine):
    with engine.begin() as conn:
        for role in ["anon", "authenticated"]:
            if not conn.execute(text("SELECT 1 FROM pg_roles WHERE rolname=:role"), {"role": role}).scalar_one_or_none():
                conn.execute(text(f"CREATE ROLE {role} NOLOGIN"))
        conn.execute(text("ALTER DEFAULT PRIVILEGES GRANT ALL ON TABLES TO anon, authenticated"))
    migrate(engine)
    with engine.connect() as conn:
        for role in ["anon", "authenticated"]:
            for schema in ["meta", "staging", "marts"]:
                assert conn.execute(text("SELECT has_schema_privilege(:role,:schema,'USAGE')"), {"role": role, "schema": schema}).scalar_one() is False
            for table in ["staging.censo_curso", "staging.trajetoria_atual", "meta.importacoes"]:
                assert conn.execute(text("SELECT has_table_privilege(:role,:table,'SELECT')"), {"role": role, "table": table}).scalar_one() is False


def test_withdraw_unknown_batch_rolls_back_entire_withdrawal(engine, tmp_path):
    migrate(engine)
    plan = plan_for(tmp_path)
    apply_plan(engine, plan)
    with pytest.raises(PersistenceError, match="não encontrado"):
        withdraw_batches(engine, [plan["batches"][0]["batch_id"], "0" * 24], "teste de retirada atômica")
    with engine.connect() as conn:
        assert conn.execute(text("SELECT count(*) FROM staging.censo_curso_atual")).scalar_one() == 1
        assert conn.execute(text("SELECT count(*) FROM meta.eventos WHERE action='withdraw'")).scalar_one() == 0


def test_concurrent_same_plan_has_one_load_and_one_reuse(engine, tmp_path):
    from concurrent.futures import ThreadPoolExecutor
    migrate(engine)
    plan = plan_for(tmp_path)
    with ThreadPoolExecutor(max_workers=2) as pool:
        futures = [pool.submit(apply_plan, engine, plan) for _ in range(2)]
        statuses = sorted(f.result()[0]["status"] for f in futures)
    assert statuses == ["loaded", "reused"]
    with engine.connect() as conn:
        assert conn.execute(text("SELECT count(*) FROM staging.censo_curso")).scalar_one() == 1
