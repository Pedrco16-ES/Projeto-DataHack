"""Somente regressões essenciais do MVP: matemática, proteção e execução."""

from io import BytesIO
import json

import pandas as pd
import pytest

from src.analytics.metrics import AnalyticsError, trajectory, trajectory_summary, join_quality
from src.analytics.disclosure import public_courses, public_census, STATES
from src.analytics.snapshots import write_snapshot, read_snapshot, load_public_data
from src.analytics.build import digest
from src.config import Settings, PROJECT_ROOT
from src.export.public import public_csv, public_xlsx


def example():
    rows = []
    for course, n in [("001", 100), ("002", 300)]:
        for year, dead, d, c, p in [(2015, 0, 10, 0, n - 10), (2016, 1, 20, 10, n - 41)]:
            denominator = n - dead
            rows.append({"CO_IES": "1", "CO_CURSO": course, "CO_UF": "51", "NU_ANO_INGRESSO": 2015,
                         "NU_ANO_REFERENCIA": year, "QT_INGRESSANTE": n, "QT_FALECIDO": dead,
                         "QT_DESISTENCIA": d, "QT_CONCLUINTE": c, "QT_PERMANENCIA": p,
                         "TDA": (10 if year == 2015 else 30) / denominator * 100,
                         "TCA": c / denominator * 100, "TAP": p / denominator * 100,
                         "TP_MODALIDADE_ENSINO": "1", "TP_GRAU_ACADEMICO": "2",
                         "TP_CATEGORIA_ADMINISTRATIVA": "1", "NO_CURSO": "Curso", "NO_IES": "IES",
                         "NO_CINE_AREA_GERAL": "Educação"})
    return pd.DataFrame(rows)


def test_accumulation_denominator_and_weighted_rate():
    x = trajectory(example())
    final = x.loc[x.ano.eq(2016)]
    result = trajectory_summary(final, ["ano", "coorte"])
    assert result.denominador.iloc[0] == 398
    assert result.desistentes.iloc[0] == 60
    assert result.tda.iloc[0] == pytest.approx(60 / 398 * 100)
    assert result.tda.iloc[0] != pytest.approx(final.TDA.mean())
    with pytest.raises(AnalyticsError):
        trajectory(example().iloc[1:])
    with pytest.raises(AnalyticsError):
        trajectory(pd.concat([example(), example().iloc[:1]]))


def test_small_cells_and_complementary_protection():
    x = trajectory(example())
    final = x.loc[x.ano.eq(2016)].copy()
    # Um curso fica oculto por permanência 5; retirar só ele deixaria um resíduo
    # pequeno revelável contra o total estadual. A proteção remove outro curso.
    final.loc[final.index[0], "permanentes"] = 5
    out = public_courses(final)
    assert out.empty
    safe = public_courses(x.loc[x.ano.eq(2016)])
    assert len(safe) == 2
    assert "QT_INGRESSANTE" not in safe and "falecidos" not in safe
    assert not ((safe[STATES] > 0) & (safe[STATES] < 10)).any().any()


def test_cpc_join_never_multiplies_population():
    final = public_courses(trajectory(example()).query("ano == 2016"))
    q = pd.DataFrame({"CO_IES": ["1"], "CO_CURSO": ["001"], "ano_cpc": [2015], "cpc": [3.2], "faixa_cpc": ["4"]})
    joined = join_quality(final, q, 2015)
    assert len(joined) == 2 and joined.denominador.sum() == final.denominador.sum()
    assert joined.faixa_cpc.tolist() == ["4", "Sem CPC"]
    with pytest.raises(AnalyticsError):
        join_quality(final, pd.concat([q, q]), 2015)


def test_financing_suppresses_complements_and_dependent_change():
    frame = pd.DataFrame({"ano": [2023, 2024], "rede": ["Privada"] * 2, "modalidade": ["EAD"] * 2,
                          "matriculas": [100, 200], "fies": [95, 100], "prouni_integral": [0, 0],
                          "prouni_parcial": [0, 0], "fies_pct": [95., 50.], "prouni_integral_pct": [0., 0.],
                          "prouni_parcial_pct": [0., 0.], "variacao_pct": [None, 100.]})
    result = public_census(frame)
    assert result.loc[0, "protegido"]
    assert pd.isna(result.loc[0, "fies"])
    assert result.loc[0, "matriculas"] == 100
    assert result.loc[1, "variacao_pct"] == 100
    frame.loc[0, "matriculas"] = 5
    result = public_census(frame)
    assert pd.isna(result.loc[0, "matriculas"])
    assert pd.isna(result.loc[1, "variacao_pct"])


def test_real_snapshot_integrity_and_offline_fallback(tmp_path, monkeypatch):
    source = PROJECT_ROOT / "outputs/public_snapshot.json"
    if not source.exists():
        pytest.skip("Snapshot real local ainda não construído.")
    payload = read_snapshot(source)
    assert payload["p1"][0]["desistentes"] + payload["p1"][0]["concluintes"] + payload["p1"][0]["permanentes"] == payload["p1"][0]["denominador"]
    assert payload["p1"][0]["cursos"] == payload["coverage"]["cursos_trajetoria"]
    assert len(payload["courses"]) == payload["coverage"]["cursos_publicaveis"]
    snapshot = tmp_path / "public_snapshot.json"
    write_snapshot(payload, snapshot, "Teste local")
    import src.analytics.snapshots as module
    def unavailable(*args, **kwargs):
        raise RuntimeError("Erro do driver contendo informação privada que não deve sair")
    monkeypatch.setattr(module, "create_database_engine", unavailable)
    data, message = load_public_data(Settings(outputs_dir=tmp_path, public_database_url="configured"))
    assert data == payload and "indisponível" in message and "privada" not in message
    document = json.loads(snapshot.read_text(encoding="utf-8"))
    document["payload"]["p1"][0]["tda"] = -1
    snapshot.write_text(json.dumps(document), encoding="utf-8")
    with pytest.raises(AnalyticsError):
        read_snapshot(snapshot)


def test_public_exports_neutralize_formulas_and_preserve_metadata():
    frame = pd.DataFrame({"Curso": ["=1+1"], "Taxa": [12.5]})
    meta = {"fonte": "Teste didático", "denominador": "100"}
    assert b"'=1+1" in public_csv(frame, meta)
    book = pd.ExcelFile(BytesIO(public_xlsx(frame, meta)))
    assert book.sheet_names == ["Resultados públicos", "Metodologia"]
    assert pd.read_excel(book).iloc[0, 0] == "'=1+1"


def test_dashboard_eight_pages_and_filter_reset():
    if not (PROJECT_ROOT / "outputs/public_snapshot.json").exists():
        pytest.skip("Snapshot real local ainda não construído.")
    from streamlit.testing.v1 import AppTest
    app = AppTest.from_file(str(PROJECT_ROOT / "app.py"), default_timeout=30).run()
    assert not app.exception, [x.message for x in app.exception]
    for file in sorted((PROJECT_ROOT / "pages").glob("*.py")):
        page = AppTest.from_file(str(file), default_timeout=30).run()
        assert not page.exception, (file.name, [x.message for x in page.exception])
        assert len(page.title) == 1
        if file.name == "2_Cursos.py":
            page.multiselect[0].select("Pública").run()
            assert not page.exception
            button = next(x for x in page.button if x.label == "Limpar filtros")
            button.click().run()
            assert not page.exception and page.multiselect[0].value == []
