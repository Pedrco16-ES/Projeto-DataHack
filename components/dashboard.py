"""Oito telas; toda interação consome somente o snapshot público protegido."""

import math
from datetime import datetime
from zoneinfo import ZoneInfo

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from src.analytics.metrics import AnalyticsError, trajectory_summary, correlation
from src.analytics.snapshots import load_public_data
from src.config import ConfigurationError
from src.export.public import public_csv, public_xlsx

NAV = [
    ("home", "Panorama", "Panorama do ensino superior", "app.py"),
    ("p1", "P1 · A trajetória", "Quanto da turma fica pelo caminho?", "pages/1_Trajetoria.py"),
    ("p2", "P2 · Cursos e áreas", "Onde a rota mais se perde?", "pages/2_Cursos.py"),
    ("p3", "P3 · Redes e modalidades", "Pública × privada. Presencial × EAD.", "pages/3_Redes.py"),
    ("p4", "P4 · Qualidade", "Qualidade retém?", "pages/4_Qualidade.py"),
    ("p5", "P5 · Licenciaturas", "O caminho de quem vai ensinar", "pages/5_Licenciaturas.py"),
    ("b1", "B1 · Oferta municipal", "Desertos de ensino superior", "pages/6_Municipios.py"),
    ("b2", "B2 · Financiamento", "Financiamento e permanência", "pages/7_Financiamento.py"),
]
COLORS = {"Desistência": "#e5704c", "Conclusão": "#258778", "Permanência": "#6f88ab",
          "Pública": "#258778", "Privada": "#e5704c", "Presencial": "#258778", "EAD": "#6f88ab"}
LABELS = {"ano": "Ano", "coorte": "Coorte", "curso": "Curso", "instituicao": "Instituição",
          "area": "Área", "rede": "Rede", "modalidade": "Modalidade", "grau": "Grau",
          "denominador": "Ingressantes ajustados", "desistentes": "Desistentes acumulados",
          "concluintes": "Concluintes acumulados", "permanentes": "Permanência",
          "tda": "Desistência (%)", "tca": "Conclusão (%)", "tap": "Permanência (%)",
          "matriculas": "Matrículas", "variacao_pct": "Variação anual (%)", "municipio": "Município",
          "vagas": "Vagas presenciais", "cpc": "CPC contínuo", "faixa_cpc": "Faixa CPC",
          "fies": "Matrículas FIES", "prouni_integral": "Matrículas ProUni integral",
          "prouni_parcial": "Matrículas ProUni parcial", "fies_pct": "FIES (%)",
          "prouni_integral_pct": "ProUni integral (%)", "prouni_parcial_pct": "ProUni parcial (%)",
          "cursos": "Cursos", "horizonte": "Anos desde ingresso", "ano_cpc": "Edição CPC",
          "categoria": "Categoria administrativa", "participantes": "Participantes",
          "proficientes": "No padrão 1 ou acima", "nao_proficientes": "Abaixo do padrão 1",
          "proficiencia_pct": "No padrão 1 ou acima (%)", "conceito": "Conceito Enade",
          "populacao_18_24": "População de 18–24 anos", "situacao": "Situação",
          "vagas_por_100_jovens": "Vagas por 100 jovens", "oferta_registrada": "Oferta registrada",
          "periodo": "Transição anual", "evasao_sistema_pct": "Evasão do sistema (%)"}


@st.cache_data(ttl=300, show_spinner=False)
def get_data():
    return load_public_data()


def number(value, decimals=0, suffix=""):
    if pd.isna(value):
        return "Indisponível"
    return f"{value:,.{decimals}f}".replace(",", "#").replace(".", ",").replace("#", ".") + suffix


def style():
    st.markdown("""<style>
    .stApp {background:#f6f7f3;color:#213a36;}
    [data-testid="stSidebar"] {background:#edf1eb;border-right:1px solid #dce3da;}
    .block-container {max-width:1260px;padding-top:2.4rem;padding-bottom:3rem;}
    h1,h2,h3 {font-family:Georgia,'Times New Roman',serif;letter-spacing:-.025em;color:#183e36;}
    h1 {font-size:2.7rem!important;line-height:1.1!important;}
    [data-testid="stMetric"] {background:white;padding:1.1rem 1.2rem;border:1px solid #e0e6dd;border-radius:12px;}
    [data-testid="stMetricValue"] {color:#1b6658;font-size:2rem;}
    [data-testid="stVerticalBlockBorderWrapper"] {border-radius:12px;}
    .eyebrow {color:#568171;font-size:.73rem;letter-spacing:.18em;font-weight:700;margin-bottom:.7rem;}
    .lead {font-size:1.12rem;color:#52645d;max-width:850px;line-height:1.65;margin-bottom:1.3rem;}
    .brand {font-family:Georgia,serif;font-size:1.7rem;font-weight:bold;color:#1a5548;line-height:1.1;}
    .subbrand {font-size:.7rem;letter-spacing:.13em;color:#6c8074;margin-top:.5rem;margin-bottom:1.3rem;}
    button[kind="secondary"] {border-color:#d9e1d6;}
    @media(max-width:700px){h1{font-size:2rem!important}.block-container{padding-top:1.1rem}}
    @media print{[data-testid="stSidebar"],header,button{display:none!important}.stApp{background:white}.block-container{max-width:100%;padding:0}}
    </style>""", unsafe_allow_html=True)


def chart(fig, key=None):
    fig.update_layout(template="plotly_white", paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                      font=dict(family="Arial", color="#29463e", size=13), margin=dict(l=10, r=10, t=25, b=15),
                      legend=dict(title=None, orientation="h", y=1.12), hoverlabel=dict(bgcolor="white"))
    fig.update_xaxes(showgrid=False)
    fig.update_yaxes(gridcolor="#e4e9e1", zeroline=False)
    st.plotly_chart(fig, width="stretch", key=key, config={"displaylogo": False, "scrollZoom": True,
                    "toImageButtonOptions": {"format": "png", "scale": 2, "filename": "rota_do_diploma"}})


def clear_filters(prefix):
    for key in list(st.session_state):
        if key.startswith(prefix + "_"):
            del st.session_state[key]


def filters(frame, fields, prefix):
    st.button("Limpar filtros", key=prefix + "_clear", on_click=clear_filters, args=(prefix,))
    result = frame.copy()
    cols = st.columns(min(len(fields), 4))
    for i, field in enumerate(fields):
        options = sorted(result[field].dropna().unique().tolist())
        with cols[i % len(cols)]:
            key = prefix + "_" + field
            if key in st.session_state:
                st.session_state[key] = [v for v in st.session_state[key] if v in options]
            selected = st.multiselect(LABELS.get(field, field), options, key=key, placeholder="Todos")
        if selected:
            result = result.loc[result[field].isin(selected)]
    return result


def metadata(data, source, denominator, coverage):
    return {"fonte": source, "atualizacao": data["generated_at"], "denominador": denominator,
            "cobertura": coverage, "protecao": "Células pequenas protegidas antes dos filtros. Consulte metodologia."}


def table(frame, data, key, source, denominator, coverage):
    with st.expander("Explorar tabela e baixar resultados", expanded=False):
        visible = frame.drop(columns=[c for c in ["CO_IES", "CO_CURSO", "curso_id"] if c in frame]).rename(columns=LABELS)
        query = st.text_input("Buscar na tabela", key=key + "_search", placeholder="Digite parte do nome ou valor")
        if query:
            mask = visible.astype(str).apply(lambda c: c.str.contains(query, case=False, regex=False)).any(axis=1)
            visible = visible.loc[mask]
        if visible.empty:
            st.info("Nenhum resultado para esta busca.")
            return
        sort_cols = st.columns([3, 1, 1])
        order = sort_cols[0].selectbox("Ordenar por", list(visible), key=key + "_sort")
        ascending = sort_cols[1].checkbox("Crescente", value=True, key=key + "_asc")
        size = sort_cols[2].selectbox("Linhas", [20, 50, 100], key=key + "_size")
        visible = visible.sort_values(order, ascending=ascending, kind="stable")
        pages = max(1, math.ceil(len(visible) / size))
        page_key = key + "_page"
        if st.session_state.get(page_key, 1) > pages:
            st.session_state[page_key] = 1
        page = st.number_input("Página", min_value=1, max_value=pages, value=1, key=page_key)
        st.dataframe(visible.iloc[(page - 1) * size:page * size], hide_index=True, width="stretch")
        st.caption(f"{len(visible)} linhas filtradas · página {page} de {pages}. Downloads incluem todas as linhas da busca.")
        meta = metadata(data, source, denominator, coverage)
        a, b = st.columns(2)
        a.download_button("Baixar CSV", public_csv(visible, meta), file_name=key + ".csv", mime="text/csv", key=key + "_csv")
        b.download_button("Baixar Excel", public_xlsx(visible, meta), file_name=key + ".xlsx",
                          mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", key=key + "_xlsx")


def course_notice(data):
    c = data["coverage"]
    st.info(f"Detalhamento protegido: {c['cursos_publicaveis']} de {c['cursos_trajetoria']} cursos. "
            "Cursos com células pequenas foram omitidos integralmente. Filtros e totais abaixo descrevem somente os cursos publicáveis, não todo MT.")


def empty(frame):
    if frame.empty:
        st.info("Não há dados publicáveis para a combinação selecionada. Limpe ou amplie os filtros.")
        return True
    return False


def trajectory_metrics(frame):
    d = frame.denominador.sum()
    cols = st.columns(4)
    cols[0].metric("Ingressantes ajustados", number(d), help="Ingressantes da coorte menos falecimentos acumulados. Cada curso é contado uma vez.")
    for col, field, title in zip(cols[1:], ["desistentes", "concluintes", "permanentes"], ["Desistência", "Conclusão", "Permanência"]):
        col.metric(title, number(frame[field].sum() / d * 100 if d else None, 1, "%"))


def trajectory_bar(frame):
    totals = frame[["desistentes", "concluintes", "permanentes"]].sum()
    denominator = frame.denominador.sum()
    fig = go.Figure()
    for field, name in [("desistentes", "Desistência"), ("concluintes", "Conclusão"), ("permanentes", "Permanência")]:
        value = totals[field] / denominator * 100
        fig.add_bar(y=["A cada 100"], x=[value], name=name, orientation="h", marker_color=COLORS[name],
                    text=[f"{value:.1f}%"], textposition="inside", hovertemplate=name + ": %{x:.2f}%<extra></extra>")
    fig.update_layout(barmode="stack", height=220, xaxis=dict(range=[0, 100], title="Percentual dos ingressantes ajustados"))
    chart(fig)


def home(data):
    st.markdown('<p class="lead">Do ingresso ao diploma, o que os dados revelam sobre o ensino superior em Mato Grosso?</p>', unsafe_allow_html=True)
    st.caption("RECORTE PRINCIPAL · COORTE 2015 · PRESENCIAL · ACOMPANHAMENTO ATÉ 2024")
    frame = pd.DataFrame(data["p1"])
    trajectory_metrics(frame)
    st.subheader("Uma turma. Três caminhos.")
    trajectory_bar(frame)
    st.caption("Denominador ajustado por falecimentos. Fonte: " + data["source_trajectory"])
    st.subheader("Explore as perguntas do desafio")
    censo = pd.DataFrame(data["census"])
    recent = censo.loc[censo.ano.eq(2024)]
    courses = pd.DataFrame(data["courses"])
    quality = pd.DataFrame(data["quality"])
    licensed = courses.loc[courses.grau.eq("Licenciatura")]
    private = recent.loc[recent.rede.eq("Privada")]
    fies = private.fies.sum(min_count=1) / private.matriculas.sum(min_count=1) * 100 if not private.empty and not private.protegido.any() else None
    stats = {
        "p1": (number(frame.tda.iloc[0], 1, "%"), "desistência acumulada · 2015 → 2024"),
        "p2": (number(len(courses)), "cursos publicáveis · referência 2024"),
        "p3": (number(recent.matriculas.sum(min_count=len(recent))), "matrículas · Censo 2024"),
        "p4": (number(int(quality.cpc.notna().sum())) if not quality.empty else "Pendente", f"cursos com CPC {data['cpc_year']} no recorte"),
        "p5": (number(licensed.desistentes.sum() / licensed.denominador.sum() * 100 if licensed.denominador.sum() else None, 1, "%"), "desistência · licenciaturas publicáveis · 2024"),
        "b1": (number(len(data["municipal"])), "municípios · vagas por 100 jovens · 2022"),
        "b2": (number(fies, 1, "%"), "matrículas privadas com FIES · 2024"),
    }
    for start in range(0, 7, 3):
        cols = st.columns(3)
        for col, item in zip(cols, NAV[1 + start:1 + start + 3]):
            key, label, title, path = item
            with col, st.container(border=True):
                st.caption(label.upper())
                st.markdown("### " + stats[key][0])
                st.write(title)
                st.caption(stats[key][1])
                st.page_link(path, label="Explorar análise →")
    st.subheader("Um sistema em transformação")
    visible = censo.loc[censo.matriculas.notna()].copy()
    visible["segmento"] = visible.rede + " · " + visible.modalidade
    chart(px.line(visible, x="ano", y="matriculas", color="segmento", markers=True, labels=LABELS,
                  color_discrete_sequence=["#258778", "#89ad9c", "#e5704c", "#6f88ab"]))
    st.caption("Matrículas são vínculos no ano. Não representam a mesma população da coorte 2015.")


def p1(data):
    st.markdown('<p class="lead">Coorte 2015, presencial: quanto desistiu, concluiu e seguia em 2024? Em que ano a perda é maior?</p>', unsafe_allow_html=True)
    frame = pd.DataFrame(data["p1"])
    trajectory_metrics(frame)
    trajectory_bar(frame)
    st.subheader("Como a trajetória mudou ano a ano")
    timeline = pd.DataFrame(data["timeline"])
    long = timeline.melt(id_vars=["ano", "coorte"], value_vars=["tda", "tca", "tap"], var_name="situação", value_name="percentual")
    long["situação"] = long["situação"].map({"tda": "Desistência", "tca": "Conclusão", "tap": "Permanência"})
    chart(px.line(long, x="ano", y="percentual", color="situação", markers=True, color_discrete_map=COLORS,
                  labels={"ano": "Ano de acompanhamento", "percentual": "Percentual acumulado / permanência (%)"}))
    st.success(f"O maior aumento entre anos consecutivos ocorreu em {data['peak_year']}: +{number(data['peak_delta_pp'], 1)} pontos percentuais de desistência acumulada.")
    st.caption("O primeiro ano não tem ano anterior na série. Este aumento não é risco anual de evasão; as curvas são arredondadas a 0,1 p.p.")
    st.markdown("**TDA**: parcela que desistiu até o ano. **TCA**: parcela que concluiu até o ano. **TAP**: parcela com vínculo ativo no ano. O denominador exclui falecimentos acumulados.")
    table(frame, data, "p1_total", data["source_trajectory"], "Ingressantes menos falecimentos acumulados", "Todos os cursos do recorte validado MT, coorte 2015 presencial")
    table(timeline, data, "p1_evolucao", data["source_trajectory"], "Taxas sobre ingressantes ajustados; arredondadas a 0,1 p.p.", "Série completa dos mesmos cursos")
    st.subheader("Detalhamento publicável por curso")
    course_notice(data)
    detail = filters(pd.DataFrame(data["courses"]), ["rede", "area", "curso"], "p1_detail")
    table(detail, data, "p1_cursos", data["source_trajectory"], "Ingressantes ajustados", "Somente cursos publicáveis; filtros não alteram o total estadual acima")


def p2(data):
    st.subheader("Seis coortes no mesmo horizonte")
    comparison = pd.DataFrame(data["cohorts"])
    long = comparison.melt(id_vars=["coorte", "ano"], value_vars=["tda", "tca", "tap"], var_name="indicador", value_name="percentual")
    long["indicador"] = long.indicador.map(LABELS)
    chart(px.line(long, x="coorte", y="percentual", color="indicador", markers=True,
                  labels={"coorte": "Ano de ingresso", "percentual": "Taxa no horizonte de quatro anos (%)"}))
    st.caption("Total estadual presencial · quatro anos desde o ingresso, incluindo o ano inicial (cinco observações). A composição dos cursos muda entre coortes. Os filtros abaixo não alteram esta comparação.")
    table(comparison, data, "p2_coortes", "INEP · Trajetória, coortes 2015–2020", "Ingressantes ajustados de cada coorte; taxas arredondadas a 0,1 p.p.", "MT presencial no horizonte comum de quatro anos")
    st.subheader("Detalhamento da coorte 2015")
    course_notice(data)
    st.caption("Coorte 2015 · referência 2024 · horizonte de 9 anos desde o ingresso (10 observações anuais).")
    frame = filters(pd.DataFrame(data["courses"]), ["rede", "area", "grau", "curso"], "p2")
    if empty(frame):
        return
    trajectory_metrics(frame)
    frame = frame.copy()
    frame["identificação"] = frame.curso + " · " + frame.CO_IES
    left, right = st.columns(2)
    for col, ascending, title, color in [(left, False, "Maior desistência", "#e5704c"), (right, True, "Menor desistência", "#258778")]:
        with col:
            st.subheader(title)
            ranked = frame.sort_values(["tda", "denominador"], ascending=[ascending, False]).head(10).sort_values("tda")
            fig = px.bar(ranked, x="tda", y="identificação", orientation="h", hover_data=["instituicao", "denominador"], labels=LABELS)
            fig.update_traces(marker_color=color)
            fig.update_layout(height=440, yaxis_title=None)
            chart(fig)
    st.subheader("Áreas do conhecimento")
    grouped = trajectory_summary(frame, ["ano", "coorte", "area"]).sort_values("tda")
    chart(px.bar(grouped, y="area", x="tda", orientation="h", hover_data=["cursos", "denominador"], labels=LABELS,
                 color_discrete_sequence=["#258778"]))
    st.caption("Taxas ponderadas pelo denominador compatível; o ranking não é uma comparação causal de qualidade.")
    table(frame.drop(columns="identificação"), data, "p2_ranking", data["source_trajectory"], "Ingressantes ajustados", "Cursos publicáveis no mesmo horizonte")


def p3(data):
    st.subheader("Evasão anual do sistema · total de MT")
    flow = pd.DataFrame(data["annual_flow"])
    chart(px.line(flow, x="periodo", y="evasao_sistema_pct", markers=True,
                  labels={"periodo": "Transição anual", "evasao_sistema_pct": "Evasão do sistema (%)"}))
    st.caption("Percentuais publicados pelo INEP. Este painel é estadual e não responde aos filtros de rede/modalidade abaixo. Não é desistência acumulada da coorte nem desvinculados ÷ matrículas.")
    table(flow, data, "p3_fluxo", "INEP · Indicadores de fluxo por UF 2010–2024", "Denominador numérico não fornecido nesta tabela; reprodução da taxa oficial", "Total MT; sem desagregação por rede/modalidade/curso")
    st.subheader("Matrículas por rede e modalidade")
    st.markdown('<p class="lead">O tamanho e a composição das matrículas mudaram entre 2021 e 2024. Compare redes e modalidades no mesmo período.</p>', unsafe_allow_html=True)
    frame = filters(pd.DataFrame(data["census"]), ["rede", "modalidade"], "p3")
    if empty(frame):
        return
    latest = frame.loc[frame.ano.eq(frame.ano.max())]
    earliest = frame.loc[frame.ano.eq(frame.ano.min())]
    total = latest.matriculas.sum(min_count=len(latest))
    base = earliest.matriculas.sum(min_count=len(earliest))
    a, b, c = st.columns(3)
    a.metric(f"Matrículas em {int(frame.ano.max())}", number(total))
    b.metric("Variação no período", number((total / base - 1) * 100 if base else None, 1, "%"))
    c.metric("Anos disponíveis", str(frame.ano.nunique()))
    frame["segmento"] = frame.rede + " · " + frame.modalidade
    chart(px.line(frame, x="ano", y="matriculas", color="segmento", markers=True, labels=LABELS))
    st.subheader("O ritmo da mudança")
    chart(px.bar(frame, x="ano", y="variacao_pct", color="segmento", barmode="group", labels=LABELS))
    st.info("Com quatro anos, as variações são descritivas; não classificamos um ano como outlier estatístico. A fonte da evasão estadual acima não fornece taxas por rede ou modalidade.")
    table(frame[["ano", "rede", "modalidade", "matriculas", "variacao_pct", "protegido"]], data, "p3_matriculas", data["source_census"], "Matrículas no ano; variação sobre ano anterior", "Dimensões municipais presenciais e EAD de MT")


def p4(data):
    course_notice(data)
    st.info(data["cpc_note"])
    all_rows = pd.DataFrame(data["quality"])
    if empty(all_rows):
        return
    frame = filters(all_rows, ["rede", "area", "grau", "faixa_cpc"], "p4")
    if empty(frame):
        return
    linked = frame.loc[frame.cpc.notna()]
    a, b, c = st.columns(3)
    a.metric("Cursos com CPC", number(len(linked)), help="Junção única por instituição e curso na edição selecionada.")
    b.metric("Cobertura por cursos", number(len(linked) / len(frame) * 100, 1, "%"))
    r = correlation(frame)
    c.metric("Correlação de Pearson", number(r, 2) if r is not None else "Insuficiente", help="Descritiva, não ponderada, entre cursos com CPC; mínimo de 10 cursos e variância em ambas as medidas.")
    if not linked.empty:
        chart(px.scatter(linked, x="cpc", y="tda", color="rede", size="denominador", hover_name="curso",
                         hover_data=["instituicao", "area"], color_discrete_map=COLORS, labels=LABELS, size_max=35))
    st.caption("Cada ponto é um curso publicável. Associação não implica causalidade; área, rede, perfil discente e seleção no CPC podem explicar diferenças. Não há teste inferencial ou ajuste de confundidores neste MVP.")
    grouped = trajectory_summary(frame, ["ano", "coorte", "faixa_cpc"])
    st.subheader("Desistência por faixa de CPC")
    chart(px.bar(grouped, x="faixa_cpc", y="tda", hover_data=["cursos", "denominador"], labels=LABELS, color_discrete_sequence=["#258778"]))
    st.caption(f"Cobertura por ingressantes ajustados no filtro: {number(linked.denominador.sum() / frame.denominador.sum() * 100, 1)}%. A categoria Sem CPC permanece na base.")
    table(grouped, data, "p4_faixas", f"{data['source_trajectory']} + CPC {data['cpc_year']}", "Ingressantes ajustados", "Subconjunto publicável; junção temporal por IES e curso")
    table(frame, data, "p4_cursos", f"INEP · CPC {data['cpc_year']} e Trajetória 2024", "Ingressantes ajustados", "Sem CPC preservado; nenhuma multiplicação na junção")


def p5(data):
    course_notice(data)
    frame = pd.DataFrame(data["courses"])
    frame = filters(frame.loc[frame.grau.eq("Licenciatura")], ["rede", "area", "curso"], "lic_traj")
    st.subheader("01 · Trajetória das licenciaturas")
    st.caption("Coorte 2015 · presencial · referência 2024 · cursos publicáveis")
    if not empty(frame):
        trajectory_metrics(frame)
        trajectory_bar(frame)
        table(frame, data, "p5_trajetoria", data["source_trajectory"], "Ingressantes ajustados das licenciaturas", "Subconjunto de cursos publicáveis")
    st.subheader("02 · Proficiência no Enade 2025")
    coverage = data["enade_coverage"]
    st.info(f"{coverage['cursos_publicaveis']} de {coverage['cursos_presenciais']} cursos presenciais publicáveis. Resultados incompletos ou com participantes, proficientes ou complemento entre 1 e 9 foram omitidos. Filtros independentes da trajetória acima.")
    enade = filters(pd.DataFrame(data["enade"]), ["categoria", "area", "instituicao"], "lic_enade")
    if not empty(enade):
        a, b, c = st.columns(3)
        a.metric("Participantes publicáveis", number(enade.participantes.sum()))
        b.metric("No padrão 1 ou acima", number(enade.proficientes.sum() / enade.participantes.sum() * 100, 1, "%"))
        c.metric("Cursos no filtro", number(len(enade)))
        grouped = enade.groupby("area", as_index=False)[["participantes", "proficientes"]].sum()
        grouped["proficiencia_pct"] = grouped.proficientes / grouped.participantes * 100
        chart(px.bar(grouped, x="proficiencia_pct", y="area", orientation="h", hover_data=["participantes"],
                     labels={"proficiencia_pct": "No padrão 1 ou acima (%)", "area": "Área"}, color_discrete_sequence=["#258778"]))
        table(enade, data, "p5_enade", "INEP · Enade Licenciaturas 2025", "Concluintes participantes; taxa ponderada pelos participantes", "Cursos presenciais publicáveis de MT; não representa todos os avaliados")
    st.write("Os concluintes avaliados pelo Enade não são necessariamente os mesmos estudantes da coorte 2015. Os painéis têm populações e denominadores próprios; não formam um funil individual contínuo.")


def b1(data):
    st.caption("Referência comum: 2022 · 141 municípios na malha territorial de 2022")
    st.markdown("**Vagas por 100 jovens:** vagas presenciais registradas ÷ população residente de 18 a 24 anos × 100. As vagas podem ser ocupadas por pessoas de outras idades e municípios; o indicador não mede acesso efetivo.")
    frame = filters(pd.DataFrame(data["municipal"]), ["situacao", "municipio"], "b1")
    if empty(frame):
        return
    a, b, c = st.columns(3)
    a.metric("Vagas presenciais registradas", number(frame.vagas.sum()))
    b.metric("Municípios no recorte", number(frame.municipio.nunique()))
    c.metric("Vagas por 100 jovens", number(frame.vagas.sum() / frame.populacao_18_24.sum() * 100, 1))
    fig = px.choropleth_map(frame, geojson=data["municipal_geometry"], locations="codigo_municipio",
                            featureidkey="properties.codarea", color="vagas_por_100_jovens",
                            hover_name="municipio", hover_data=["vagas", "populacao_18_24", "situacao"],
                            map_style="white-bg", center={"lat": -12.7, "lon": -55.8}, zoom=4.5,
                            color_continuous_scale="Teal", labels={"vagas_por_100_jovens": "Vagas / 100 jovens"})
    fig.update_layout(height=550)
    chart(fig)
    st.caption("Malha IBGE incorporada ao snapshot, sem mapa-base externo. Zero indica nenhuma vaga presencial registrada no recorte validado, não ausência comprovada de acesso. Ausência de população não é convertida em zero.")
    ranked = frame.nlargest(20, "vagas_por_100_jovens").sort_values("vagas_por_100_jovens")
    chart(px.bar(ranked, x="vagas_por_100_jovens", y="municipio", orientation="h", labels={"vagas_por_100_jovens": "Vagas por 100 jovens", "municipio": "Município"}, color_discrete_sequence=["#258778"]))
    table(frame, data, "b1_oferta", "INEP · Censo Superior 2022 + IBGE · Censo 2022", "População residente de 18–24 anos em 2022", "Cadastro e malha completos de 2022; sem oferta registrada identificado separadamente")


def b2(data):
    st.markdown('<p class="lead">Qual é o peso de FIES e ProUni nas matrículas da rede privada?</p>', unsafe_allow_html=True)
    frame = pd.DataFrame(data["census"])
    frame = filters(frame.loc[frame.rede.eq("Privada")], ["modalidade"], "b2")
    if empty(frame):
        return
    year = st.selectbox("Ano dos indicadores", sorted(frame.ano.unique(), reverse=True), key="b2_year")
    latest = frame.loc[frame.ano.eq(year)]
    denominator = latest.matriculas.sum(min_count=len(latest))
    cols = st.columns(3)
    for col, key, name in zip(cols, ["fies", "prouni_integral", "prouni_parcial"], ["FIES", "ProUni integral", "ProUni parcial"]):
        value = latest[key].sum(min_count=len(latest))
        col.metric(name, number(value / denominator * 100 if denominator else None, 1, "%"), help="Participação entre matrículas privadas do ano e modalidade selecionados.")
    st.subheader("Participação ao longo do tempo")
    long = frame.melt(id_vars=["ano", "modalidade"], value_vars=["fies_pct", "prouni_integral_pct", "prouni_parcial_pct"], var_name="programa", value_name="percentual")
    long["programa"] = long.programa.map(LABELS)
    chart(px.line(long, x="ano", y="percentual", color="programa", line_dash="modalidade", markers=True,
                  labels={"ano": "Ano", "percentual": "Participação nas matrículas (%)"}))
    st.info("Os benefícios são apresentados separadamente: a sobreposição não foi validada. A evasão anual disponível é estadual, sem recorte por curso ou financiamento; não permite calcular essa associação. Dados agregados não permitem concluir que um estudante financiado individualmente evada menos.")
    st.caption("Células protegidas aparecem vazias. Um total que dependa de parcela protegida fica indisponível; não somamos apenas as parcelas visíveis.")
    table(frame.drop(columns="variacao_pct"), data, "b2_financiamento", data["source_census"], "Matrículas privadas do mesmo ano e modalidade", "Agregação municipal de MT; FIES e modalidades ProUni sem soma")


def render(page="home"):
    style()
    with st.sidebar:
        st.markdown('<div class="brand">Rota do<br>Diploma<span style="color:#e5704c">.</span></div><div class="subbrand">DATAHACK · UNIVAG 2026</div>', unsafe_allow_html=True)
        st.caption("MATO GROSSO · ENSINO SUPERIOR")
        if st.button("Atualizar dados validados", width="stretch", help="Recarrega o snapshot ou a leitura pública. Não executa importação nem grava no banco."):
            get_data.clear()
            st.rerun()
    try:
        data, mode = get_data()
    except (AnalyticsError, ConfigurationError):
        st.title("Rota do Diploma")
        st.info("Resultados validados ainda não disponíveis. Execute a construção administrativa do snapshot conforme o README.")
        return
    title = next(item[2] for item in NAV if item[0] == page)
    st.markdown(f'<div class="eyebrow">ROTA DO DIPLOMA / {"PANORAMA" if page == "home" else page.upper()}</div>', unsafe_allow_html=True)
    st.title(title)
    updated = datetime.fromisoformat(data["generated_at"]).astimezone(ZoneInfo("America/Sao_Paulo")).strftime("%d/%m/%Y %H:%M")
    st.caption(f"{mode} · Atualizado em {updated} (Brasília)")
    {"home": home, "p1": p1, "p2": p2, "p3": p3, "p4": p4, "p5": p5, "b1": b1, "b2": b2}[page](data)
    st.divider()
    with st.expander("Fontes, cobertura e metodologia"):
        st.write("Dados reais de fontes oficiais, processados localmente. Aprovação técnica do MVP; publicação externa depende de revisão editorial.")
        for note in data["limitations"]:
            st.markdown("- " + note)
        st.dataframe(pd.DataFrame(data["sources"]), hide_index=True, width="stretch")
        st.markdown("[Indicadores de Trajetória · INEP](https://www.gov.br/inep/pt-br/acesso-a-informacao/dados-abertos/indicadores-educacionais/indicadores-de-trajetoria-da-educacao-superior) · [Microdados do Censo · INEP](https://www.gov.br/inep/pt-br/acesso-a-informacao/dados-abertos/microdados/censo-da-educacao-superior)")
    st.caption("Rota do Diploma · DataHack Univag 2026 | Entender a trajetória é o primeiro passo para transformá-la.")
