"""Dashboard offline das sete perguntas, gerado do snapshot público validado."""
from pathlib import Path
import sys
from html import escape
import pandas as pd
import plotly.express as px
import plotly.io as pio

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.analytics.snapshots import read_snapshot
from src.analytics.answers import answers
from src.analytics.metrics import trajectory_summary


def generate_html(data):
    summaries = answers(data)
    sections = []
    bundled = False

    def chart(fig):
        nonlocal bundled
        fig.update_layout(template="plotly_white", font=dict(family="Arial"), margin=dict(l=20, r=20, t=35, b=35))
        result = pio.to_html(fig, full_html=False, include_plotlyjs=True if not bundled else False, config={"displaylogo": False, "responsive": True})
        bundled = True
        return result

    def table(frame):
        return '<div class="table-wrap">' + frame.to_html(index=False, escape=True, na_rep="—", float_format=lambda v: f"{v:.1f}".replace(".", ",")) + '</div>'

    def section(key, title, content):
        status, answer = summaries[key]
        sections.append(f'<section id="{key}"><small>{key.upper()} · {escape(status)}</small><h2>{escape(title)}</h2><p class="answer">{escape(answer)}</p>{content}</section>')

    timeline = pd.DataFrame(data["timeline"]).rename(columns={"ano": "Ano", "tda": "Desistência (%)", "tca": "Conclusão (%)", "tap": "Permanência (%)"})
    section("p1", "Quanto da turma fica pelo caminho?", chart(px.line(timeline, x="Ano", y=["Desistência (%)", "Conclusão (%)", "Permanência (%)"], markers=True)) + '<p>Denominador ajustado por falecimentos. Aumento da desistência acumulada não equivale a risco anual de evasão.</p>')
    courses = pd.DataFrame(data["courses"])
    cols = ["curso", "instituicao", "denominador", "tda"]
    labels = {"curso": "Curso", "instituicao": "Instituição", "denominador": "Ingressantes ajustados", "tda": "Desistência (%)", "area": "Área"}
    cohorts = pd.DataFrame(data["cohorts"])
    areas = trajectory_summary(courses, ["ano", "coorte", "area"]).sort_values("tda")
    section("p2", "Onde a rota mais se perde?", '<h3>Maiores taxas</h3>' + table(courses.nlargest(10, "tda")[cols].rename(columns=labels)) + '<h3>Menores taxas</h3>' + table(courses.nsmallest(10, "tda")[cols].rename(columns=labels)) + chart(px.bar(areas, x="tda", y="area", orientation="h", labels=labels)) + '<h3>Coortes no mesmo horizonte</h3><p>Quatro anos desde o ingresso, cinco observações. A composição de cursos varia entre coortes.</p>' + chart(px.line(cohorts, x="coorte", y=["tda", "tca", "tap"], markers=True, labels={"coorte": "Coorte", "value": "Taxa (%)", "variable": "Indicador"})) + '<p>TDA = desistência; TCA = conclusão; TAP = permanência. Rankings restritos aos cursos publicáveis.</p>')
    census = pd.DataFrame(data["census"])
    census["segmento"] = census.rede + " · " + census.modalidade
    flow = pd.DataFrame(data["annual_flow"])
    section("p3", "Pública × privada, presencial × EAD", chart(px.line(census, x="ano", y="matriculas", color="segmento", markers=True, labels={"ano": "Ano", "matriculas": "Matrículas", "segmento": "Rede / modalidade"})) + chart(px.bar(census, x="ano", y="variacao_pct", color="segmento", barmode="group", labels={"ano": "Ano", "variacao_pct": "Variação anual (%)"})) + chart(px.line(flow, x="periodo", y="evasao_sistema_pct", markers=True, labels={"periodo": "Transição anual", "evasao_sistema_pct": "Evasão estadual (%)"})) + '<p>Evasão oficial do total de MT, independente das séries de matrículas. Não há desagregação de evasão por rede ou modalidade.</p>')
    quality = pd.DataFrame(data["quality"])
    linked = quality.dropna(subset=["cpc"])
    section("p4", "Qualidade retém?", f'<p>{len(linked)} de {len(quality)} cursos publicáveis com CPC. {escape(data["cpc_note"])}</p>' + chart(px.scatter(linked, x="cpc", y="tda", color="rede", hover_name="curso", hover_data=["instituicao"], labels={"cpc": "CPC contínuo", "tda": "Desistência (%)", "rede": "Rede"})))
    enade = pd.DataFrame(data["enade"])
    section("p5", "O funil das licenciaturas", chart(px.bar(enade, x="proficiencia_pct", y="instituicao", color="area", orientation="h", labels={"proficiencia_pct": "No padrão 1 ou acima (%)", "instituicao": "Instituição", "area": "Área"})) + '<p>A proficiência tem como denominador os participantes publicáveis do Enade, não todos os concluintes da coorte 2015.</p>')
    municipal = pd.DataFrame(data["municipal"])
    section("b1", "Desertos de ensino superior", '<p>Vagas presenciais ÷ residentes de 18–24 anos × 100. Referência comum: 2022. Todos os municípios estão na tabela; zero vagas não comprova ausência de acesso.</p>' + table(municipal.sort_values(["vagas", "municipio"])[["municipio", "situacao", "vagas", "populacao_18_24", "vagas_por_100_jovens"]].rename(columns={"municipio": "Município", "situacao": "Registro de oferta", "vagas": "Vagas", "populacao_18_24": "Jovens 18–24", "vagas_por_100_jovens": "Vagas / 100 jovens"})))
    private = census.loc[census.rede.eq("Privada")]
    section("b2", "Financiamento e permanência", table(private[["ano", "modalidade", "matriculas", "fies_pct", "prouni_integral_pct", "prouni_parcial_pct"]].rename(columns={"ano": "Ano", "modalidade": "Modalidade", "matriculas": "Matrículas privadas", "fies_pct": "FIES (%)", "prouni_integral_pct": "ProUni integral (%)", "prouni_parcial_pct": "ProUni parcial (%)"})) + '<p>— indica indisponibilidade ou proteção, não zero. Não é possível estimar o efeito do financiamento sobre a permanência com esses agregados.</p>')
    nav = " ".join(f'<a href="#{key}">{key.upper()}</a>' for key in summaries)
    notes = "".join(f'<li>{escape(note)}</li>' for note in data["limitations"])
    return f'''<!doctype html><html lang="pt-BR"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Rota do Diploma · sete perguntas</title><style>body{{font:16px/1.6 Arial,sans-serif;background:#f8f9fa;color:#1a2b5e;margin:0}}header,main{{max-width:1150px;margin:auto;padding:24px}}section{{background:white;border:1px solid #dee2e6;border-radius:12px;padding:24px;margin:24px 0}}h1,h2{{line-height:1.2}}.answer{{border-left:4px solid #0066cc;padding:16px;background:#eef5ff}}nav a{{display:inline-block;padding:8px 16px;color:#1a2b5e}}small{{font-weight:bold}}.table-wrap{{overflow:auto;max-height:650px}}table{{border-collapse:collapse;width:100%;font-size:13px}}td,th{{padding:10px;border-bottom:1px solid #ddd;text-align:left}}@media print{{.table-wrap{{max-height:none;overflow:visible}}section{{break-before:page}}nav{{display:none}}}}</style></head><body><header><h1>Rota do Diploma</h1><p>De cada 100 que entram numa graduação em MT, quantos chegam ao diploma?</p><p>Cinco perguntas obrigatórias e dois bônus · INEP e IBGE</p><p>P3, P4 e B2 possuem respostas parciais. As limitações acompanham cada conclusão.</p><p>Dados atualizados em {escape(data['generated_at'])}. Visualização offline do snapshot público validado.</p><nav>{nav}</nav></header><main>{''.join(sections)}<section><h2>Fontes e limites</h2><ul>{notes}</ul>{table(pd.DataFrame(data['sources']))}</section></main></body></html>'''


def main():
    data = read_snapshot(ROOT / "outputs/public_snapshot.json")
    document = generate_html(data)
    (ROOT / "dashboard.html").write_text(document, encoding="utf-8")
    print("dashboard.html atualizado com as sete perguntas e dados validados; uso offline.")


if __name__ == "__main__":
    main()
