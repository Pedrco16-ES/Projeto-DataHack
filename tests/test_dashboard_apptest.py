"""Testes de interface com Streamlit AppTest para todas as 8 telas."""

from pathlib import Path
from streamlit.testing.v1 import AppTest

PAGES_DIR = Path(__file__).parents[1] / "pages"
APP_PATH = Path(__file__).parents[1] / "app.py"


def test_main_dashboard_app():
    app = AppTest.from_file(str(APP_PATH), default_timeout=25).run()
    assert not app.exception


def test_p1_page():
    p1_path = PAGES_DIR / "01_p1_trajetoria.py"
    app = AppTest.from_file(str(p1_path), default_timeout=25).run()
    assert not app.exception


def test_p2_page():
    p2_path = PAGES_DIR / "02_p2_cursos_areas.py"
    app = AppTest.from_file(str(p2_path), default_timeout=25).run()
    assert not app.exception


def test_p3_page():
    p3_path = PAGES_DIR / "03_p3_rede_modalidade.py"
    app = AppTest.from_file(str(p3_path), default_timeout=25).run()
    assert not app.exception


def test_p4_page():
    p4_path = PAGES_DIR / "04_p4_qualidade.py"
    app = AppTest.from_file(str(p4_path), default_timeout=25).run()
    assert not app.exception


def test_p5_page():
    p5_path = PAGES_DIR / "05_p5_licenciaturas.py"
    app = AppTest.from_file(str(p5_path), default_timeout=25).run()
    assert not app.exception


def test_b1_page():
    b1_path = PAGES_DIR / "06_b1_desertos.py"
    app = AppTest.from_file(str(b1_path), default_timeout=25).run()
    assert not app.exception


def test_b2_page():
    b2_path = PAGES_DIR / "07_b2_financiamento.py"
    app = AppTest.from_file(str(b2_path), default_timeout=25).run()
    assert not app.exception
