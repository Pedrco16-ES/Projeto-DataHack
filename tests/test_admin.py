from pathlib import Path

import pandas as pd
from streamlit.testing.v1 import AppTest

from src.config import Settings


def test_admin_requires_preview_of_selected_file(tmp_path, monkeypatch):
    monkeypatch.setattr("src.config.load_settings", lambda: Settings(data_dir=tmp_path))
    app = AppTest.from_file(str(Path(__file__).parents[1] / "admin.py"), default_timeout=20).run()
    assert not app.exception
    assert app.title[0].value.startswith("Rota do Diploma")
    app.radio[1].set_value("Processar recorte MT").run()
    app.button[0].click().run()
    assert not app.exception
    assert app.error[0].value == "Selecione um arquivo."


def test_admin_preview_survives_checkbox_rerun(tmp_path, monkeypatch):
    from tests.test_ingestion import census
    pd.DataFrame([census()]).to_csv(tmp_path / "sample.csv", sep=";", index=False)
    monkeypatch.setattr("src.config.load_settings", lambda: Settings(data_dir=tmp_path))
    app = AppTest.from_file(str(Path(__file__).parents[1] / "admin.py"), default_timeout=20).run()
    app.selectbox[0].set_value("censo_curso").run()
    app.selectbox[1].set_value(2024).run()
    app.button[0].click().run()
    assert not app.exception and not app.error
    assert len(app.dataframe) == 1
    app.checkbox[1].check().run()
    assert len(app.dataframe) == 1
    assert app.session_state["reviewed"]
    app.selectbox[1].set_value(2023).run()
    assert not app.session_state["reviewed"]
    assert len(app.dataframe) == 0
