"""Reconciliação somente leitura do plano, sem imprimir dados de estudantes."""

import argparse
from dataclasses import replace
from datetime import datetime, timezone
import json
from pathlib import Path
import sys

import pandas as pd
from sqlalchemy import text

PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT))

from src.config import load_settings
from src.database.connection import create_database_engine
from src.ingestion.pipeline import sha256
from src.ingestion.schema import load_contract


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--plan", type=Path, required=True)
    args = parser.parse_args()
    plan = json.loads(args.plan.read_text(encoding="utf-8"))
    engine = create_database_engine(replace(load_settings(), connect_timeout=30))
    summary = {"verified_at": datetime.now(timezone.utc).isoformat(), "plan_sha256": sha256(args.plan), "batches": []}
    try:
        with engine.connect() as conn:
            assert conn.connection.driver_connection.pgconn.ssl_in_use
            summary["tls"] = True
            summary["readonly"] = conn.execute(text("SHOW transaction_read_only")).scalar_one()
            assert summary["readonly"] == "on"
            summary["statement_timeout"] = conn.execute(text("SHOW statement_timeout")).scalar_one()
            checksum = conn.execute(text("SELECT checksum FROM meta.schema_versions WHERE version='001'")).scalar_one()
            assert checksum == plan["migration_sha256"]
            for item in plan["batches"]:
                source = item["source"]
                assert source in {"trajetoria", "censo_curso"}
                contract = load_contract(source, item["edition"])
                metadata = conn.execute(text("SELECT status,accepted,report_sha256,accepted_sha256,public_approved FROM meta.importacoes WHERE batch_id=:id"),
                                        {"id": item["batch_id"]}).mappings().one()
                assert metadata["status"] == "loaded" and not metadata["public_approved"]
                assert metadata["report_sha256"] == item["report_sha256"]
                assert metadata["accepted_sha256"] == item["accepted_sha256"]
                path = Path(item["batch_dir"]) / "accepted.csv"
                assert sha256(path) == item["accepted_sha256"]
                metrics = ["QT_INGRESSANTE", "QT_PERMANENCIA", "QT_CONCLUINTE", "QT_DESISTENCIA", "QT_FALECIDO"] if source == "trajetoria" else ["QT_MAT", "QT_ING", "QT_CONC"]
                frame = pd.read_csv(path, dtype="string", usecols=contract["key"] + metrics)
                keys = ",".join(c.lower() for c in contract["key"])
                stored = conn.execute(text(f"SELECT {keys} FROM staging.{source}_atual WHERE batch_id=:id"), {"id": item["batch_id"]}).all()
                assert len(stored) == len(frame) == metadata["accepted"] == item["counts"]["accepted"]
                expected_keys = sorted(tuple(str(v) for v in row) for row in frame[contract["key"]].itertuples(index=False, name=None))
                actual_keys = sorted(tuple(str(v) for v in row) for row in stored)
                assert actual_keys == expected_keys
                sums_sql = ",".join(f"sum({column.lower()})" for column in metrics)
                sums = conn.execute(text(f"SELECT {sums_sql} FROM staging.{source}_atual WHERE batch_id=:id"), {"id": item["batch_id"]}).one()
                for column, stored_sum in zip(metrics, sums):
                    expected_sum = pd.to_numeric(frame[column], errors="raise").sum(min_count=1)
                    assert stored_sum == (None if pd.isna(expected_sum) else int(expected_sum))
                summary["batches"].append({"source": source, "edition": item["edition"], "rows": len(stored),
                                          "keys_match": True, "counts_match": True, "hashes_match": True, "public_approved": False})
            roles = conn.execute(text("SELECT rolname FROM pg_roles WHERE rolname IN ('anon','authenticated')")).scalars().all()
            for role in roles:
                for schema in ["meta", "staging", "marts"]:
                    assert not conn.execute(text("SELECT has_schema_privilege(:role,:schema,'USAGE')"), {"role": role, "schema": schema}).scalar_one()
            tables = conn.execute(text("SELECT n.nspname,c.relname,c.relrowsecurity FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace WHERE n.nspname IN ('meta','staging') AND c.relkind='r'")).all()
            assert len(tables) == 6 and all(row[2] for row in tables)
            summary["rls_tables"] = len(tables)
            summary["anonymous_schema_access"] = False
            summary["total_rows"] = sum(item["rows"] for item in summary["batches"])
            assert summary["total_rows"] == plan["total_rows"]
            summary["load_events"] = conn.execute(text("SELECT count(*) FROM meta.eventos WHERE action='load'")).scalar_one()
        output = PROJECT / "data/processed/stage4_supabase_verification.json"
        output.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
        print(json.dumps(summary, ensure_ascii=False))
        return 0
    except Exception as error:
        cause = getattr(error, "orig", error)
        print("Reconciliação não aprovada:", type(error).__name__, "SQLSTATE:", getattr(cause, "sqlstate", None))
        return 1
    finally:
        engine.dispose()


if __name__ == "__main__":
    raise SystemExit(main())
