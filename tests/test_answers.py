"""Impede regressão das conclusões divergentes e da entrega offline."""
from pathlib import Path
from html.parser import HTMLParser

from src.analytics.answers import answers
from src.analytics.snapshots import read_snapshot
from scripts.generate_unified_dashboard_html import generate_html

ROOT = Path(__file__).resolve().parents[1]


def test_public_answers_and_offline_html():
    data = read_snapshot(ROOT / "outputs/public_snapshot.json")
    responses = answers(data)
    assert set(responses) == {"p1", "p2", "p3", "p4", "p5", "b1", "b2"}
    assert all(responses[key][0] == "Parcial" for key in ["p3", "p4", "b2"])
    assert "59,9" in responses["p1"][1] and "1,3" in responses["p1"][1]
    assert "0,045" in responses["p4"][1]
    assert "53,1" in responses["p5"][1] and "11 de 84" in responses["p5"][1]
    assert all(value in responses["b1"][1] for value in ["99", "103", "21,3"])
    document = generate_html(data)
    class Inspect(HTMLParser):
        external_scripts = []
        sections = []
        def handle_starttag(self, tag, attrs):
            attrs = dict(attrs)
            if tag == "script" and "src" in attrs:
                self.external_scripts.append(attrs["src"])
            if tag == "section" and "id" in attrs:
                self.sections.append(attrs["id"])
    parsed = Inspect()
    parsed.feed(document)
    assert not parsed.external_scripts
    assert set(parsed.sections) == set(responses)
    assert "R = -0,42" not in document
    assert "fortíssimo escudo" not in document
    assert "Desist?ncia" not in document
    assert "Desistência (%)" in document
