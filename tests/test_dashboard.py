"""Testes automatizados do dashboard, analytics e exportações públicas seguras."""

import pandas as pd
import pytest

from src.analytics.loader import (
    load_p1_data,
    load_p2_data,
    load_p3_data,
    load_p4_data,
    load_p5_data,
    load_b1_data,
    load_b2_data,
    load_metadata,
    get_data_source_status
)
from components.export import sanitize_public_dataframe


def test_data_source_status_offline_fallback():
    status = get_data_source_status()
    assert isinstance(status, dict)
    assert "label" in status
    assert "mode" in status
    assert status["mode"] in {"online", "snapshot"}


def test_load_p1_trajetoria_invariants():
    df = load_p1_data()
    assert len(df) == 10  # 10 anos de acompanhamento (2015 a 2024)
    assert set(["nu_ano_referencia", "tda", "tca", "tap", "qt_ingressante"]).issubset(df.columns)
    assert (df["qt_ingressante"] == 40896).all()

    # Equação de balanço do INEP
    soma_taxas = (df["tda"] + df["tca"] + df["tap"]).round(1)
    assert (soma_taxas == 100.0).all()

    # O 2º ano (2016) deve ser o de maior salto de evasão
    maior_salto_ano = df.loc[df["delta_tda"].idxmax(), "nu_ano_referencia"]
    assert maior_salto_ano == 2016


def test_load_p2_cursos_areas():
    df = load_p2_data()
    assert len(df) > 0
    assert "NO_CINE_ROTULO" in df.columns
    assert "tda" in df.columns
    # TDA deve estar no intervalo [0, 100]
    assert (df["tda"] >= 0).all() and (df["tda"] <= 100).all()


def test_load_p3_censo_rede():
    df = load_p3_data()
    assert len(df) == 16  # 4 anos x 2 redes x 2 modalidades
    assert set(["nu_ano_censo", "tp_rede", "tp_modalidade_ensino", "qt_mat"]).issubset(df.columns)
    # Matrículas estritamente positivas
    assert (df["qt_mat"] > 0).all()


def test_load_p4_cpc():
    df = load_p4_data()
    assert len(df) > 0
    assert "faixa_cpc" in df.columns
    assert "Sem CPC" in df["faixa_cpc"].values


def test_load_p5_licenciaturas():
    df = load_p5_data()
    assert len(df) > 0
    assert "NO_CINE_ROTULO" in df.columns
    assert "enade_proficiente_pct" in df.columns
    assert (df["enade_proficiente_pct"] >= 0).all()


def test_load_b1_oferta_municipal():
    df = load_b1_data()
    assert len(df) >= 70
    assert "vagas_por_100_jovens" in df.columns
    # Cuiabá deve ter alta oferta
    cuiaba = df[df["no_municipio"] == "Cuiabá"]
    assert len(cuiaba) == 1
    assert cuiaba["vagas_presenciais"].values[0] > 10000

    # Deve conter municípios classificados como desertos
    desertos = df[df["vagas_presenciais"] == 0]
    assert len(desertos) > 0


def test_load_b2_financiamento():
    df = load_b2_data()
    assert len(df) == 4  # 2021 a 2024
    assert (df["diferencial_permanencia_pp"] > 0).all()


def test_metadata_completeness():
    meta = load_metadata()
    assert "projeto" in meta
    assert "fontes_oficiais" in meta
    assert len(meta["fontes_oficiais"]) >= 3


def test_suppression_of_small_cells():
    test_df = pd.DataFrame({
        "curso": ["Curso A", "Curso B", "Curso C"],
        "ingressantes": [50, 4, 120]
    })
    cleaned = sanitize_public_dataframe(test_df, count_columns=["ingressantes"])
    assert cleaned.loc[0, "ingressantes"] == 50
    assert cleaned.loc[1, "ingressantes"] == "< 10 (suprimido)"
    assert cleaned.loc[2, "ingressantes"] == 120
