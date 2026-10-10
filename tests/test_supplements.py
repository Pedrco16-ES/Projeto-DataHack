"""Três verificações essenciais de fontes/denominadores, sem rede ou banco."""

import copy
import json
import pandas as pd
import pytest

from src.analytics.metrics import AnalyticsError
from src.ingestion.supplements import RAW, population_from_json, validate_geometry, enade_from_frame
from src.ingestion.flow import read_flow


def test_ibge_complete_ages_geography_and_duplicate_rejection():
    path = RAW / "ibge_18_24_municipios_mt_2022.json"
    if not path.exists():
        pytest.skip("Fonte oficial local ainda não adquirida.")
    data = json.loads(path.read_text(encoding="utf-8"))
    detail, totals = population_from_json(data)
    assert len(detail) == 987 and len(totals) == 141
    assert totals.populacao_18_24.sum() == 397671
    validate_geometry(json.loads((RAW / "ibge_malha_mt_2022.geojson").read_text(encoding="utf-8")), totals.codigo_municipio)
    duplicate = copy.deepcopy(data)
    duplicate[0]["resultados"].append(duplicate[0]["resultados"][0])
    with pytest.raises(AnalyticsError):
        population_from_json(duplicate)


def test_enade_fraction_counts_and_absence_not_zero():
    path = RAW / "enade_licenciaturas_2025.xlsx"
    if not path.exists():
        pytest.skip("Fonte oficial local ainda não adquirida.")
    frame, report = enade_from_frame(pd.read_excel(path, dtype="string"))
    assert report["cursos_mt"] == 97 and report["sem_resultado_mt"] == 6
    valid = frame.loc[frame.status.eq("calculavel")]
    assert (valid.proficiencia_pct - valid.fracao_oficial * 100).abs().max() <= 0.051
    assert frame.loc[frame.status.ne("calculavel"), "proficientes"].isna().all()


def test_flow_is_annual_state_rate_not_course_dropout():
    path = RAW / "fluxo_uf_2010_2024.zip"
    if not path.exists():
        pytest.skip("Fonte oficial local ainda não adquirida.")
    frame = read_flow(path)
    assert len(frame) == 14 and frame.periodo.is_unique
    assert frame.loc[frame.periodo.eq("2023-2024"), "evasao_sistema_pct"].iloc[0] == 18.5
    assert not frame.denominador_numerico_disponivel.any()
    assert "curso" not in frame and "modalidade" not in frame
