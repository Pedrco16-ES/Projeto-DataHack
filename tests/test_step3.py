"""Duas verificações essenciais da integração: dados e isolamento de filtros."""
from copy import deepcopy
import json

import pandas as pd
import pytest

from src.analytics.build import digest
from src.analytics.metrics import AnalyticsError
from src.analytics.snapshots import read_snapshot, validate_envelope
from src.config import PROJECT_ROOT


def test_integrated_sources_and_public_protection():
    path = PROJECT_ROOT / "outputs/public_snapshot.json"
    data = read_snapshot(path)
    assert data["p1"][0]["denominador"] == 41889
    cohorts = pd.DataFrame(data["cohorts"])
    assert set(cohorts.coorte) == set(range(2015, 2021))
    assert (cohorts.ano - cohorts.coorte).eq(4).all()
    assert not {"denominador", "falecidos", "desistentes"}.intersection(cohorts)
    assert [r["evasao_sistema_pct"] for r in data["annual_flow"]] == [13.7, 16.7, 17.9, 18.5]
    municipal = pd.DataFrame(data["municipal"])
    assert len(municipal) == 141 and municipal.populacao_18_24.sum() == 397671
    assert municipal.vagas.sum() == 84508
    assert (~municipal.oferta_registrada).sum() == 99
    assert municipal.loc[~municipal.oferta_registrada, "vagas_por_100_jovens"].eq(0).all()
    enade = pd.DataFrame(data["enade"])
    assert len(enade) == 11 and enade.participantes.sum() == 339 and enade.proficientes.sum() == 180
    assert "inscritos" not in enade
    for column in ["participantes", "proficientes", "nao_proficientes"]:
        assert not enade[column].between(1, 9).any()
    # Mesmo recalculando o hash, uma célula pequena não pode ser publicada.
    envelope = deepcopy(json.loads(path.read_text(encoding="utf-8")))
    envelope["payload"]["enade"][0]["proficientes"] = 5
    envelope["sha256"] = digest(envelope["payload"])
    with pytest.raises(AnalyticsError):
        validate_envelope(envelope)


def test_enade_filters_do_not_change_trajectory():
    from streamlit.testing.v1 import AppTest
    page = AppTest.from_file(str(PROJECT_ROOT / "pages/5_Licenciaturas.py"), default_timeout=30).run()
    before = [(x.label, x.value) for x in page.metric[:4]]
    field = next(x for x in page.multiselect if x.key == "lic_enade_instituicao")
    field.select(field.options[0]).run()
    assert not page.exception
    assert [(x.label, x.value) for x in page.metric[:4]] == before
    assert page.multiselect(key="lic_traj_rede").value == []
