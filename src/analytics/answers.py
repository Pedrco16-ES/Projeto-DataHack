"""Respostas editoriais calculadas exclusivamente sobre dados públicos validados."""

import pandas as pd
from src.analytics.metrics import correlation


def number(value):
    return f"{value:.1f}".replace(".", ",")


def answers(data):
    p = data["p1"][0]
    courses = pd.DataFrame(data["courses"])
    licensed = courses.loc[courses.grau.eq("Licenciatura")]
    enade = pd.DataFrame(data["enade"])
    municipal = pd.DataFrame(data["municipal"])
    census = pd.DataFrame(data["census"])
    flow = pd.DataFrame(data["annual_flow"])
    peak = flow.loc[flow.evasao_sistema_pct.idxmax()]
    changes = census.dropna(subset=["variacao_pct"])
    change = changes.loc[changes.variacao_pct.abs().idxmax()]
    r = correlation(pd.DataFrame(data["quality"]))
    r_text = "indisponível" if r is None else f"{r:.3f}".replace(".", ",")
    highest = courses.loc[courses.tda.idxmax()]
    lowest = courses.loc[courses.tda.idxmin()]
    return {
        "p1": ("Respondida", f"De cada 100 ingressantes ajustados, {number(p['tda'])} desistiram, {number(p['tca'])} concluíram e {number(p['tap'])} permaneciam em 2024. Maior aumento entre anos consecutivos: {data['peak_year']} (+{number(data['peak_delta_pp'])} p.p.). Coorte 2015 presencial de MT."),
        "p2": ("Respondida no recorte", f"Entre os cursos publicáveis, a maior taxa é {number(highest.tda)}% ({highest.curso}, {highest.instituicao}) e a menor é {number(lowest.tda)}% ({lowest.curso}, {lowest.instituicao}). Ranking: coorte 2015 até 2024. A comparação das coortes 2015–2020 usa quatro anos desde o ingresso e é estadual, sem detalhamento entre coortes por curso."),
        "p3": ("Parcial", f"A maior evasão estadual da série é {number(peak.evasao_sistema_pct)}%, em {peak.periodo}. A maior variação absoluta anual de matrículas por segmento é {number(change.variacao_pct)}%, em {int(change.ano)} ({change.rede}, {change.modalidade}). Isso destaca uma mudança, sem provar anomalia estatística. Falta evasão por rede e modalidade para responder à comparação completa."),
        "p4": ("Parcial", f"Correlação linear entre CPC e desistência: r = {r_text}, no recorte publicável com CPC. Esse resultado não demonstra que qualidade retém. Área, rede e perfil discente são hipóteses a investigar; suas contribuições não foram estimadas. CPC 2023, sem ajuste de confundidores ou inferência causal."),
        "p5": ("Respondida no recorte", f"Nas licenciaturas publicáveis, {number(licensed.desistentes.sum() / licensed.denominador.sum() * 100)}% desistiram (coorte 2015 até 2024). No Enade 2025, {number(enade.proficientes.sum() / enade.participantes.sum() * 100)}% dos participantes publicáveis estão no padrão 1 ou acima: {int(enade.proficientes.sum())} de {int(enade.participantes.sum())}, em {len(enade)} de {data['enade_coverage']['cursos_presenciais']} cursos presenciais. São populações distintas, não um funil individual nem um resultado de todo MT."),
        "b1": ("Respondida no recorte", f"Em 2022, há {number(municipal.vagas.sum() / municipal.populacao_18_24.sum() * 100)} vagas presenciais por 100 jovens de 18–24 anos em MT. Dos {len(municipal)} municípios, {int((~municipal.oferta_registrada).sum())} não têm registro de oferta e {int((municipal.oferta_registrada & municipal.vagas.eq(0)).sum())} têm registro com zero vagas: {int(municipal.vagas.eq(0).sum())} com zero vagas no total. Isso não comprova ausência de acesso ao ensino superior."),
        "b2": ("Parcial", "As séries mostram o peso de FIES e ProUni nas matrículas privadas de 2021–2024, separadamente e por modalidade. Não é possível afirmar se cursos com mais financiados evadem menos: falta uma taxa de evasão comparável por curso. Não somar benefícios, pois a sobreposição não foi validada."),
    }
