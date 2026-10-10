"""Regressões das telas ativas e dos filtros compartilháveis."""
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

ROOT = Path(__file__).parents[1]


@pytest.mark.parametrize("path", ["app.py", "pages/1_Trajetoria.py", "pages/2_Cursos.py",
    "pages/3_Redes.py", "pages/4_Qualidade.py", "pages/5_Licenciaturas.py",
    "pages/6_Municipios.py", "pages/7_Financiamento.py"])
def test_active_pages_render_with_public_snapshot(path):
    page = AppTest.from_file(str(ROOT / path), default_timeout=30).run()
    assert not page.exception, [e.message for e in page.exception]
    assert page.get("plotly_chart")


def test_filter_url_restores_valid_values_and_clear_resets():
    page = AppTest.from_file(str(ROOT / "pages/3_Redes.py"), default_timeout=30)
    page.query_params["p3_rede"] = ["Privada", "inexistente"]
    page.run()
    assert not page.exception
    assert page.multiselect(key="p3_rede").value == ["Privada"]
    assert page.query_params["p3_rede"] == "Privada"
    page.multiselect(key="p3_rede").set_value(["Pública"]).run()
    assert page.query_params["p3_rede"] == "Pública"
    page.query_params["p3_rede"] = "Privada"
    page.run()
    assert page.multiselect(key="p3_rede").value == ["Privada"]
    page.button(key="p3_clear").click().run()
    assert not page.exception
    assert page.multiselect(key="p3_rede").value == []
    assert "p3_rede" not in page.query_params


def test_absent_number_is_distinct_from_zero():
    from components.dashboard import number
    assert number(None) == "—"
    assert number(float("nan")) == "—"
    assert number(0) == "0"
    assert number(1234.5, 1, "%") == "1.234,5%"
