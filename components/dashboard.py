"""Oito telas; toda interação consome somente o snapshot público protegido."""

import math
from pathlib import Path
from html import escape
from datetime import datetime
from zoneinfo import ZoneInfo

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from src.analytics.metrics import AnalyticsError, trajectory_summary, correlation
from src.analytics.answers import answers
from src.analytics.snapshots import load_public_data
from src.config import ConfigurationError
from src.export.public import public_csv, public_xlsx

NAV = [
    ("home", "Panorama", "Panorama do ensino superior", "app.py"),
    ("p1", "A trajetória", "Quanto da turma fica pelo caminho?", "pages/1_Trajetoria.py"),
    ("p2", "Cursos e áreas", "Onde a rota mais se perde?", "pages/2_Cursos.py"),
    ("p3", "Redes e modalidades", "Pública × privada. Presencial × EAD.", "pages/3_Redes.py"),
    ("p4", "Qualidade", "Qualidade retém?", "pages/4_Qualidade.py"),
    ("p5", "Licenciaturas", "O caminho de quem vai ensinar", "pages/5_Licenciaturas.py"),
    ("b1", "Oferta municipal", "Desertos de ensino superior", "pages/6_Municipios.py"),
    ("b2", "Financiamento", "Financiamento e permanência", "pages/7_Financiamento.py"),
]
COLORS = {"Desistência": "#DC3545", "Conclusão": "#28A745", "Permanência": "#0066CC",
          "Pública": "#1A2B5E", "Privada": "#6F42C1", "Presencial": "#1A2B5E", "EAD": "#0066CC"}
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
        return "—"
    return f"{value:,.{decimals}f}".replace(",", "#").replace(".", ",").replace("#", ".") + suffix


def style():
    css = Path(__file__).with_name("univag.css").read_text(encoding="utf-8")
    st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)
    st.markdown('<a class="skip-link" href="#conteudo-principal">Pular para o conteúdo</a>', unsafe_allow_html=True)


def chart(fig, key=None, *, legend_top=False):
    fig.update_layout(template="plotly_white", paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                      separators=",.", font=dict(family="Segoe UI", color="#495057", size=12), margin=dict(l=10, r=20, t=25, b=15),
                      legend=dict(title=None, orientation="h", y=-.18, x=.5, xanchor="center"), hoverlabel=dict(bgcolor="white"))
    if legend_top:
        # Separa a legenda do título do eixo nas barras horizontais compactas.
        fig.update_layout(
            margin=dict(l=10, r=35, t=80, b=70),
            legend=dict(y=1.15, yanchor="bottom", x=0, xanchor="left", traceorder="normal"),
        )
    fig.update_xaxes(showgrid=False, automargin=True)
    fig.update_yaxes(automargin=True, gridcolor="#E9ECEF", zeroline=False)
    st.plotly_chart(fig, width="stretch", key=key, config={"displaylogo": False, "scrollZoom": True,
                    "toImageButtonOptions": {"format": "png", "scale": 2, "filename": "rota_do_diploma"}})


    # Alternativa tabular usa os mesmos pontos do gráfico e mantém valores ausentes.
    rows = []
    for trace in fig.data:
        xs = getattr(trace, "x", None)
        ys = getattr(trace, "y", None)
        if trace.type == "pie":
            xs, ys = trace.labels, trace.values
        if xs is not None and ys is not None:
            for x, y in zip(xs, ys):
                def display(value):
                    if pd.isna(value):
                        return "—"
                    return number(value, 2 if float(value) % 1 else 0) if pd.api.types.is_number(value) else str(value)
                rows.append({"Série": trace.name or "Indicador", "Eixo X / categoria": display(x), "Eixo Y / valor": display(y)})
    if rows:
        with st.expander("Ver tabela do gráfico"):
            st.caption("Mesmos pontos e unidades dos eixos do gráfico. Valores ausentes não representam zero.")
            st.table(pd.DataFrame(rows))


def clear_filters(prefix):
    for key in list(st.session_state):
        if key.startswith(prefix + "_"):
            del st.session_state[key]
    for key in list(st.query_params):
        if key.startswith(prefix + "_"):
            del st.query_params[key]


def sync_filter_url(key):
    selected = st.session_state.get(key, [])
    if selected:
        st.query_params[key] = [str(v) for v in selected]
    elif key in st.query_params:
        del st.query_params[key]


def filters(frame, fields, prefix):
    st.button("Limpar filtros", key=prefix + "_clear", on_click=clear_filters, args=(prefix,))
    result = frame.copy()
    cols = st.columns(min(len(fields), 4))
    active = []
    for i, field in enumerate(fields):
        options = sorted(result[field].dropna().unique().tolist())
        with cols[i % len(cols)]:
            key = prefix + "_" + field
            requested = st.query_params.get_all(key)
            st.session_state[key] = [v for v in options if str(v) in requested]
            selected = st.multiselect(LABELS.get(field, field), options, key=key, placeholder="Todos",
                                      on_change=sync_filter_url, args=(key,))
        if selected:
            st.query_params[key] = [str(v) for v in selected]
            active.append(f"{LABELS.get(field, field)}: {', '.join(map(str, selected))}")
            result = result.loc[result[field].isin(selected)]
        elif key in st.query_params:
            del st.query_params[key]
    st.caption("Filtros ativos · " + (" · ".join(active) if active else "Todos os registros publicáveis deste painel"))
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
            st.info("Nenhum resultado para esta busca. Apague ou altere o termo de busca para ver os registros disponíveis.")
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
    fig.update_layout(barmode="stack", height=300,
                      xaxis=dict(range=[0, 100], title=dict(text="Percentual dos ingressantes ajustados", standoff=18)))
    chart(fig, legend_top=True)


@st.fragment(run_every="1s")
def cohort_simulator(data):
    timeline = pd.DataFrame(data["timeline"]).sort_values("ano")
    if empty(timeline):
        return
    years = timeline.ano.astype(int).tolist()
    if st.session_state.get("cohort_playing", False):
        current = st.session_state.get("cohort_year", years[-1])
        index = years.index(current) if current in years else len(years) - 1
        st.session_state.cohort_year = years[min(index + 1, len(years) - 1)]
        if st.session_state.cohort_year == years[-1]:
            st.session_state.cohort_playing = False
    with st.container(border=True):
        control, slider = st.columns([1, 2])
        with control:
            st.markdown("**Simulador da turma · coorte 2015**")
            playing = st.session_state.get("cohort_playing", False)
            if st.button("Pausar" if playing else "▶ Reproduzir", key="cohort_toggle"):
                st.session_state.cohort_playing = not playing
                if not playing and st.session_state.get("cohort_year", years[-1]) == years[-1]:
                    st.session_state.cohort_year = years[0]
                st.rerun()
        with slider:
            year = st.select_slider("Ano de acompanhamento", options=years, value=years[-1], key="cohort_year")
    row = timeline.loc[timeline.ano.eq(year)].iloc[0]
    cards = [("Taxa de conclusão", number(row.tca, 1), "#0066CC", f"a cada 100 ingressantes · {year}"),
             ("Taxa de desistência", number(row.tda, 1), "#DC3545", f"a cada 100 ingressantes · {year}"),
             ("Retidos / cursando", number(row.tap, 1), "#1B5E20", f"a cada 100 ingressantes · {year}"),
             ("Ano crítico de perda", str(data["peak_year"]), "#7A5A00", f"maior salto na série completa: +{number(data['peak_delta_pp'], 1)} p.p.")]
    for col, (label, value, color, note) in zip(st.columns(4), cards):
        col.markdown(f'<div class="kpi"><div class="kpi-label">{escape(label)}</div><div class="kpi-value" style="color:{color}">{escape(value)}</div><div class="kpi-note">{escape(note)}</div></div>', unsafe_allow_html=True)
    st.write("")
    left, right = st.columns([2, 3])
    with left, st.container(border=True):
        st.markdown("**Funil do diploma**")
        st.caption(f"A cada 100 ingressantes ajustados · {year}")
        fig = go.Figure(go.Pie(labels=["Conclusão", "Desistência", "Permanência"], values=[row.tca, row.tda, row.tap],
                               hole=.7, sort=False, marker=dict(colors=[COLORS[x] for x in ["Conclusão", "Desistência", "Permanência"]], line=dict(color="white", width=3)),
                               textinfo="none", hovertemplate="%{label}: %{value:.1f} a cada 100<extra></extra>"))
        fig.update_layout(height=355, annotations=[dict(text=f"<b>{year}</b><br>ANO REF.", x=.5, y=.5, showarrow=False, font_size=20)])
        chart(fig, "cohort_donut")
    with right, st.container(border=True):
        st.markdown("**Evolução da coorte 2015**")
        st.caption("Por 100 ingressantes ajustados, ano a ano")
        fig = go.Figure()
        for field, label in [("tca", "Conclusão"), ("tda", "Desistência"), ("tap", "Permanência")]:
            fig.add_scatter(x=timeline.ano, y=timeline[field], name=label, mode="lines+markers", line=dict(color=COLORS[label], width=3), hovertemplate="%{x}: %{y:.1f}<extra>%{fullData.name}</extra>")
        fig.add_vline(x=year, line_dash="dot", line_color="#cbd5e1")
        fig.update_layout(height=355, yaxis=dict(range=[0, 100], title="Por 100 ingressantes"), xaxis=dict(dtick=1), hovermode="x unified")
        chart(fig, "cohort_lines")
    st.caption("Denominador ajustado por falecimentos; taxas arredondadas a 0,1 p.p. O ano crítico considera toda a série. Fonte: " + data["source_trajectory"])


def course_ranking(data, frame=None, key="home_ranking"):
    with st.container(border=True):
        st.subheader("Em quais cursos a rota mais se perde?")
        st.caption("Desistência acumulada · coorte 2015 presencial · referência 2024")
        course_notice(data)
        frame = pd.DataFrame(data["courses"]) if frame is None else frame.copy()
        if empty(frame):
            return
        mode = st.radio("Visualizar ranking", ["Críticos (> 70%)", "Menor perda", "Por área CINE", "Ver todos"], horizontal=True, key=key)
        group = "area" if mode == "Por área CINE" else "curso"
        ranked = trajectory_summary(frame, ["ano", "coorte", group])
        ranked = ranked.sort_values(["tda", group], ascending=[mode == "Menor perda", True])
        if mode == "Críticos (> 70%)":
            ranked = ranked.loc[ranked.tda.gt(70)].head(10)
        elif mode == "Menor perda":
            ranked = ranked.head(10)
        if ranked.empty:
            st.info("Nenhum curso com desistência acima de 70% neste recorte.")
            return
        color = "#1B5E20" if mode == "Menor perda" else "#0066CC" if group == "area" else "#DC3545"
        fig = px.bar(ranked, x="tda", y=group, orientation="h", text="tda", hover_data=["denominador", "tca"], labels=LABELS)
        fig.update_traces(marker_color=color, texttemplate="%{x:.1f}%", textposition="outside", cliponaxis=False)
        fig.update_layout(height=max(380, len(ranked) * 32 + 90), yaxis=dict(title=None, categoryorder="array", categoryarray=ranked[group].tolist()[::-1]), xaxis=dict(range=[0, 105], ticksuffix="%", title=None))
        chart(fig, key + "_chart")
        st.caption("Taxas ponderadas pelos ingressantes ajustados. Cursos de mesmo nome são agrupados apenas entre registros publicáveis; não representam todo MT.")


def home(data):
    st.markdown('<div class="question">De cada 100 que entram numa graduação em MT, quantos chegam ao diploma e em quais cursos a rota se perde?</div>', unsafe_allow_html=True)
    st.info("Cobertura do desafio: P1 respondida; P2, P5 e B1 respondidas nos recortes disponíveis; P3, P4 e B2 parciais. Consulte as respostas e limitações em cada painel.")
    frame = pd.DataFrame(data["p1"])
    cohort_simulator(data)
    course_ranking(data)
    st.subheader("Explore as perguntas do desafio")
    summaries = answers(data)
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
                st.markdown(f"**{summaries[key][0]}**")
                st.write(summaries[key][1])
                st.page_link(path, label="Explorar análise →")
    st.subheader("Um sistema em transformação")
    visible = censo.loc[censo.matriculas.notna()].copy()
    visible["segmento"] = visible.rede + " · " + visible.modalidade
    chart(px.line(visible, x="ano", y="matriculas", color="segmento", markers=True, labels=LABELS,
                  color_discrete_sequence=["#1A2B5E", "#89ad9c", "#6F42C1", "#0066CC"]))
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
    for col, ascending, title, color in [(left, False, "Maior desistência", "#6F42C1"), (right, True, "Menor desistência", "#1A2B5E")]:
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
                 color_discrete_sequence=["#1A2B5E"]))
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
    chart(px.bar(grouped, x="faixa_cpc", y="tda", hover_data=["cursos", "denominador"], labels=LABELS, color_discrete_sequence=["#1A2B5E"]))
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
                     labels={"proficiencia_pct": "No padrão 1 ou acima (%)", "area": "Área"}, color_discrete_sequence=["#1A2B5E"]))
        table(enade, data, "p5_enade", "INEP · Enade Licenciaturas 2025", "Concluintes participantes; taxa ponderada pelos participantes", "Cursos presenciais publicáveis de MT; não representa todos os avaliados")
    st.write("Os concluintes avaliados pelo Enade não são necessariamente os mesmos estudantes da coorte 2015. Os painéis têm populações e denominadores próprios; não formam um funil individual contínuo.")


def b1(data):
    st.caption("Referência comum: 2022 · 141 municípios na malha territorial de 2022")
    st.markdown("**Vagas por 100 jovens:** vagas presenciais registradas ÷ população residente de 18 a 24 anos × 100. As vagas podem ser ocupadas por pessoas de outras idades e municípios; o indicador não mede acesso efetivo.")
    frame = filters(pd.DataFrame(data["municipal"]), ["situacao", "municipio"], "b1")
    if empty(frame):
        return
    st.subheader("Municípios com zero vagas presenciais no recorte")
    st.dataframe(frame.loc[frame.vagas.eq(0), ["municipio", "situacao", "vagas", "populacao_18_24"]].rename(columns=LABELS), hide_index=True, width="stretch")
    a, b, c = st.columns(3)
    a.metric("Vagas presenciais registradas", number(frame.vagas.sum()))
    b.metric("Municípios no recorte", number(frame.municipio.nunique()))
    c.metric("Vagas por 100 jovens", number(frame.vagas.sum() / frame.populacao_18_24.sum() * 100, 1))
    map_frame = frame.copy()
    map_frame["escala_cor"] = map_frame.vagas_por_100_jovens.map(
        lambda value: math.log1p(value) if pd.notna(value) else float("nan"))
    # Keep the color range stable when filtering municipalities.
    map_max = max(1.0, pd.DataFrame(data["municipal"]).vagas_por_100_jovens.max())
    ticks = [value for value in [0, 1, 5, 10, 25, 50, 100, 250, 500, 1000] if value < map_max]
    ticks.append(map_max)
    fig = px.choropleth_map(map_frame, geojson=data["municipal_geometry"], locations="codigo_municipio",
                            featureidkey="properties.codarea", color="escala_cor",
                            hover_name="municipio", hover_data={"vagas_por_100_jovens": ":.2f", "vagas": True,
                                                               "populacao_18_24": True, "situacao": True, "escala_cor": False},
                            map_style="white-bg", center={"lat": -12.7, "lon": -55.8}, zoom=4.5,
                            color_continuous_scale=[[0, "#DCE2E8"], [.12, "#B9DDF1"], [.35, "#62B5D5"],
                                                    [.6, "#2286B5"], [.8, "#1260A0"], [1, "#123566"]],
                            range_color=(0, math.log1p(map_max)),
                            labels={"vagas_por_100_jovens": "Vagas / 100 jovens"})
    fig.update_traces(marker_line_color="#FFFFFF", marker_line_width=.7)
    fig.update_layout(height=550, coloraxis_colorbar=dict(
        title="Vagas / 100 jovens<br>(escala logarítmica)",
        tickvals=[math.log1p(value) for value in ticks],
        ticktext=[number(value, 1) if value == map_max else str(value) for value in ticks]))
    chart(fig)
    st.caption("Cores em escala logarítmica (logₑ(1 + valor)) para destacar diferenças nos valores baixos. Cinza indica zero vagas; azul mais escuro indica maior oferta. Legenda e detalhes exibem valores originais.")
    st.caption("Malha IBGE incorporada ao snapshot, sem mapa-base externo. Zero indica nenhuma vaga presencial registrada no recorte validado, não ausência comprovada de acesso. Ausência de população não é convertida em zero.")
    ranked = frame.nlargest(20, "vagas_por_100_jovens").sort_values("vagas_por_100_jovens")
    chart(px.bar(ranked, x="vagas_por_100_jovens", y="municipio", orientation="h", labels={"vagas_por_100_jovens": "Vagas por 100 jovens", "municipio": "Município"}, color_discrete_sequence=["#1A2B5E"]))
    table(frame, data, "b1_oferta", "INEP · Censo Superior 2022 + IBGE · Censo 2022", "População residente de 18–24 anos em 2022", "Cadastro e malha completos de 2022; sem oferta registrada identificado separadamente")


def b2(data):
    st.markdown('<p class="lead">Qual é o peso de FIES e ProUni nas matrículas da rede privada?</p>', unsafe_allow_html=True)
    frame = pd.DataFrame(data["census"])
    private = frame.loc[frame.rede.eq("Privada")]
    frame = filters(private, ["modalidade"], "b2")
    if empty(frame):
        return
    year = st.selectbox("Ano dos indicadores", sorted(frame.ano.unique(), reverse=True), key="b2_year")
    latest = frame.loc[frame.ano.eq(year)]
    cols = st.columns(3)
    for col, key, name in zip(cols, ["fies", "prouni_integral", "prouni_parcial"], ["FIES", "ProUni integral", "ProUni parcial"]):
        selected = private.loc[private.ano.eq(year) & private.modalidade.eq("Presencial")] if key == "fies" else latest
        denominator = selected.matriculas.sum(min_count=max(1, len(selected)))
        value = selected[key].sum(min_count=max(1, len(selected)))
        percentage = value / denominator * 100 if pd.notna(denominator) and denominator > 0 else None
        help_text = ("Participação entre matrículas privadas presenciais do ano selecionado. Este card permanece fixo no presencial, independentemente do filtro de modalidade."
                     if key == "fies" else "Participação entre matrículas privadas do ano e modalidade selecionados.")
        col.metric("FIES · presencial" if key == "fies" else name, number(percentage, 1, "%"), help=help_text)
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
        st.markdown('<div class="brand">Rota do<br>Diploma<span style="color:#6F42C1">.</span></div><div class="subbrand">DATAHACK · UNIVAG 2026</div>', unsafe_allow_html=True)
        st.caption("MATO GROSSO · ENSINO SUPERIOR")
        if st.button("Atualizar dados validados", width="stretch", help="Recarrega o snapshot ou a leitura pública. Não executa importação nem grava no banco."):
            get_data.clear()
            st.rerun()
    try:
        with st.spinner("Carregando dados validados…"):
            data, mode = get_data()
    except (AnalyticsError, ConfigurationError):
        st.title("Rota do Diploma")
        st.error("Não foi possível carregar os resultados validados. Seus filtros foram preservados. Tente novamente; se o problema continuar, solicite a atualização da base ao responsável.")
        if st.button("Tentar novamente"):
            get_data.clear()
            st.rerun()
        return
    title = next(item[2] for item in NAV if item[0] == page)
    page_class = "dashboard-home" if page == "home" else "dashboard-detail"
    st.markdown(f'<div id="conteudo-principal" class="{page_class}" tabindex="-1"></div>', unsafe_allow_html=True)
    if page == "home":
        heading, export = st.columns([4, 1], vertical_alignment="center")
        heading.markdown('<div class="eyebrow">ROTA DO DIPLOMA / PANORAMA</div>', unsafe_allow_html=True)
        export.download_button("Exportar CSV", public_csv(pd.DataFrame(data["timeline"]).rename(columns=LABELS),
                               metadata(data, data["source_trajectory"], "Ingressantes ajustados", "MT · coorte 2015 presencial")),
                               file_name="rota_do_diploma_trajetoria.csv", mime="text/csv", type="primary")
        st.title("Rota do Diploma — Dashboard Executivo")
        st.caption("DataHack Univag 2026 · Mato Grosso · Ensino superior · Fontes oficiais INEP e IBGE")
    else:
        st.markdown(f'<div class="eyebrow">ROTA DO DIPLOMA / {page.upper()}</div>', unsafe_allow_html=True)
        st.title(title)
    updated = datetime.fromisoformat(data["generated_at"]).astimezone(ZoneInfo("America/Sao_Paulo")).strftime("%d/%m/%Y %H:%M")
    st.caption(f"{mode} · Atualizado em {updated} (Brasília)")
    if page != "home":
        status, answer = answers(data)[page]
        st.markdown(f"**Resposta ao desafio · {status}**")
        st.write(answer)
        st.caption("Síntese do recorte completo disponível nesta página. Os filtros abaixo alteram os gráficos e tabelas, não esta síntese.")
    {"home": home, "p1": p1, "p2": p2, "p3": p3, "p4": p4, "p5": p5, "b1": b1, "b2": b2}[page](data)
    st.divider()
    with st.expander("Fontes, cobertura e metodologia"):
        st.write("Dados reais de fontes oficiais, processados localmente. Aprovação técnica do MVP; publicação externa depende de revisão editorial.")
        for note in data["limitations"]:
            st.markdown("- " + note)
        st.dataframe(pd.DataFrame(data["sources"]), hide_index=True, width="stretch")
        st.markdown("[Indicadores de Trajetória · INEP](https://www.gov.br/inep/pt-br/acesso-a-informacao/dados-abertos/indicadores-educacionais/indicadores-de-trajetoria-da-educacao-superior) · [Microdados do Censo · INEP](https://www.gov.br/inep/pt-br/acesso-a-informacao/dados-abertos/microdados/censo-da-educacao-superior)")
    st.caption("Rota do Diploma · DataHack Univag 2026 | Entender a trajetória é o primeiro passo para transformá-la.")
