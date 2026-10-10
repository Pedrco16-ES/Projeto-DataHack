import json
from pathlib import Path

import pandas as pd
import pytest

from src.database.ddl import build_ddl
from src.database.persistence import MIGRATION, PersistenceError, make_plan, prepare_batch, verify_plan
from src.ingestion.pipeline import process_file, sha256
from tests.test_ingestion import census, save_csv


@pytest.fixture
def batch_dir(tmp_path):
    original = save_csv(tmp_path, [census(), census(CO_CURSO="00456")])
    result = process_file(original, "censo_curso", 2024, output_root=tmp_path / "processed")
    return Path(result["batch_dir"])


def test_migration_matches_contracts():
    assert MIGRATION.read_text(encoding="utf-8") == build_ddl()


def test_preflight_verifies_private_plan(batch_dir):
    plan = make_plan([batch_dir])
    assert plan["total_rows"] == 2
    assert plan["publication"] == "private_staging_only"
    assert plan["replacement"] == "blocked"
    verify_plan(plan)
    plan["total_rows"] += 1
    with pytest.raises(PersistenceError, match="mudaram"):
        verify_plan(plan)


def test_preflight_rejects_modified_artifact(batch_dir):
    with (batch_dir / "accepted.csv").open("a", encoding="utf-8") as file:
        file.write("alterado\n")
    with pytest.raises(PersistenceError):
        prepare_batch(batch_dir)


def test_preflight_revalidates_values_even_if_report_hash_updated(batch_dir):
    path = batch_dir / "accepted.csv"
    frame = pd.read_csv(path, dtype="string")
    frame.loc[0, "QT_MAT"] = "-1"
    frame.to_csv(path, index=False)
    report_path = batch_dir / "report.json"
    report = json.loads(report_path.read_text(encoding="utf-8"))
    report["artifacts"]["accepted.csv"] = sha256(path)
    report_path.write_text(json.dumps(report), encoding="utf-8")
    with pytest.raises(PersistenceError, match="revalidação"):
        prepare_batch(batch_dir)


def test_preflight_rejects_duplicate_editions(batch_dir):
    with pytest.raises(PersistenceError, match="mesma fonte"):
        make_plan([batch_dir, batch_dir])
