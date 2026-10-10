"""Apresentação HTML autocontida, imprimível em PDF, sem rede ou dados brutos."""

import html
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pandas as pd
from src.analytics.snapshots import read_snapshot
from src.config import load_settings


def num(value, digits=0):
    return f"{value:,.{digits}f}".replace(",", "#").replace(".", ",").replace("#", ".")


def main():
    settings = load_settings()
    data = read_snapshot(settings.outputs_dir / "public_snapshot.json")
    p1 = data["p1"][0]
    courses = pd.DataFrame(data["courses"])
    census = pd.DataFrame(data["census"])
    quality = pd.DataFrame(data["quality"])
    licensed = courses.loc[courses.grau.eq("Licenciatura")]
    title = "Rota do Diploma · DataHack Univag 2026"
    sections = []
    def section(label, heading, content):
        sections.append(f'<section><small>{html.escape(label)}</small><h2>{html.escape(heading)}</h2>{content}</section>')
    bars = "".join(f'<div class="bar" style="width:{p1[k]}%;background:{color}">{num(p1[k],1)}%</div>'
                   for k, color in [("tda", "#ce6647"), ("tca", "#258778"), ("tap", "#6f88ab")])
    section("01 / TRAJETÓRIA", "Quanto da turma fica pelo caminho?",
            f'<p>Coorte 2015 · presencial · Mato Grosso · referência 2024</p><div class="stack">{bars}</div>'
            f'<p><strong>{num(p1["tda"],1)}% desistência · {num(p1["tca"],1)}% conclusão · {num(p1["tap"],1)}% permanência.</strong></p>'
            f'<p>Denominador: {num(p1["denominador"])} ingressantes ajustados por falecimentos, em {num(p1["cursos"])} cursos.</p>'
            f'<p>Maior aumento entre anos consecutivos: {data["peak_year"]}, +{num(data["peak_delta_pp"],1)} p.p. Não equivale a risco anual de evasão.</p>')
    ranking = courses.nlargest(10, "tda")[["curso", "instituicao", "denominador", "tda"]].rename(columns={"curso": "Curso", "instituicao": "Instituição", "denominador": "Denominador", "tda": "TDA (%)"})
    section("02 / CURSOS E ÁREAS", "Onde a rota mais se perde?", '<p>Dez maiores taxas no recorte publicável. Apenas coorte 2015; horizonte de 9 anos desde ingresso.</p>' + ranking.to_html(index=False, float_format=lambda v: num(v, 1), escape=True))
    sections[-1] += '<section><h2>Coortes no mesmo horizonte</h2><p>MT presencial; quatro anos desde o ingresso, cinco observações. Taxas estaduais arredondadas a 0,1 p.p. Composição de cursos variável entre coortes.</p>' + pd.DataFrame(data["cohorts"]).to_html(index=False, escape=True) + '</section>'
    section("03 / MATRÍCULAS", "Pública × privada. Presencial × EAD.", census[["ano", "rede", "modalidade", "matriculas", "variacao_pct"]].to_html(index=False, float_format=lambda v: num(v, 1), na_rep="—") + '<h3>Evasão anual do sistema</h3>' + pd.DataFrame(data["annual_flow"])[["periodo", "evasao_sistema_pct"]].to_html(index=False) + '<p>Taxas oficiais INEP para o total de MT, sem recorte por rede/modalidade/curso. Denominadores numéricos não publicados nesta tabela. Variações descritivas.</p>')
    linked = int(quality.cpc.notna().sum()) if not quality.empty else 0
    section("04 / QUALIDADE", "Qualidade retém?", f'<p>{linked} cursos publicáveis vinculados ao CPC {data["cpc_year"]}.</p><p>{html.escape(data["cpc_note"])}</p><p>Correlação descritiva: {num(data["correlation"],2) if data["correlation"] is not None else "insuficiente"}. Associação não é causalidade.</p>')
    tda = licensed.desistentes.sum() / licensed.denominador.sum() * 100 if len(licensed) else None
    enade = pd.DataFrame(data["enade"])
    proficiency = enade.proficientes.sum() / enade.participantes.sum() * 100
    section("05 / LICENCIATURAS", "O caminho de quem vai ensinar", f'<p>Desistência no subconjunto publicável da trajetória: {num(tda,1) + "%" if tda is not None else "pendente"}.</p><p>Enade 2025: {num(proficiency,1)}% no padrão 1 ou acima, sobre {num(enade.participantes.sum())} participantes em {len(enade)} de {data["enade_coverage"]["cursos_presenciais"]} cursos presenciais. Cursos com dados incompletos ou células pequenas omitidos.</p><p>Populações distintas: não formam um funil individual.</p>')
    municipal = pd.DataFrame(data["municipal"])
    section("06 / TERRITÓRIO", "Oferta por 100 jovens em 2022", f'<p>141 municípios; {num(municipal.vagas.sum())} vagas presenciais registradas e {num(municipal.populacao_18_24.sum())} residentes de 18–24 anos. {int((~municipal.oferta_registrada).sum())} municípios sem oferta presencial registrada no recorte validado. Não é uma medida de acesso efetivo.</p><p>Censo Superior e IBGE: referência comum 2022. Mapa completo disponível no dashboard.</p>' + municipal.nlargest(15, "vagas_por_100_jovens")[["municipio", "vagas", "populacao_18_24", "vagas_por_100_jovens"]].to_html(index=False, float_format=lambda v: num(v,1), escape=True))
    private = census.loc[census.rede.eq("Privada")]
    section("07 / FINANCIAMENTO", "Qual é o peso de FIES e ProUni?", private[["ano", "modalidade", "matriculas", "fies_pct", "prouni_integral_pct", "prouni_parcial_pct"]].to_html(index=False, float_format=lambda v: num(v, 1), na_rep="—") + '<p>Percentuais sobre matrículas privadas compatíveis. Benefícios separados, sem presumir ausência de sobreposição. Associação com evasão pendente.</p>')
    notes = "".join('<li>' + html.escape(n) + '</li>' for n in data["limitations"])
    section("08 / MÉTODO", "O que estes resultados permitem afirmar", f'<p>Detalhamento da trajetória: {len(courses)} de {p1["cursos"]} cursos publicáveis. Comparação estadual entre coortes e Enade possuem coberturas próprias.</p><ul>{notes}</ul><p>Fontes: INEP, Trajetória 2015–2024, Censo 2021–2024, CPC 2023, Enade Licenciaturas 2025 e fluxo por UF; IBGE Censo e malha 2022.</p>')
    document = f'''<!doctype html><html lang="pt-BR"><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>{title}</title>
<style>body{{font:17px/1.6 Arial,sans-serif;background:#f6f7f3;color:#243e36;margin:0}}header,section{{max-width:1100px;margin:auto;padding:48px}}header{{background:#173f35;color:white}}h1,h2{{font-family:Georgia,serif;line-height:1.15}}h1{{font-size:52px}}h2{{font-size:34px}}small{{letter-spacing:.15em}}section{{border-bottom:1px solid #d9e0d6;break-inside:avoid}}.stack{{display:flex;height:70px;overflow:hidden;border-radius:10px}}.bar{{display:flex;align-items:center;justify-content:center;color:white;min-width:0;font-weight:bold}}table{{width:100%;border-collapse:collapse;font-size:12px}}th,td{{padding:8px;text-align:left;border-bottom:1px solid #d9e0d6}}th{{background:#e7eee5}}@media print{{body{{background:white;font-size:12px}}header,section{{padding:20px;page-break-after:always}}h1{{font-size:38px}}h2{{font-size:27px}}table{{font-size:9px}}}}</style>
<header><small>MATO GROSSO / ENSINO SUPERIOR</small><h1>Rota do Diploma.</h1><p>DataHack Univag 2026 · Dos dados à compreensão da trajetória.</p><p>Atualização: {html.escape(data['generated_at'])}. Documento offline com dados reais protegidos.</p></header>{''.join(sections)}</html>'''
    path = settings.outputs_dir / "apresentacao.html"
    path.write_text(document, encoding="utf-8")
    print("Apresentação offline criada em outputs/apresentacao.html")


if __name__ == "__main__":
    main()
