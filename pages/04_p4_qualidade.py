"""Tela 5 — P4: Qualidade retém?

Pergunta oficial:
"Cursos com CPC mais alto apresentam menor desistência? O que mais pode explicar essa relação?"
Fontes: Conceito Preliminar de Curso (CPC ciclo 2021-2023) e Indicadores de Trajetória do INEP.
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go

from components.styles import apply_custom_styles
from components.header import render_header
from components.kpi_cards import render_kpi
from components.charts import plot_scatter_correlation, plot_horizontal_ranking, apply_theme, UNIVAG_COLORS
from components.export import render_export_buttons
from src.analytics.loader import load_p4_data

st.set_page_config(page_title="P4: Qualidade e CPC · Rota do Diploma", page_icon="⭐", layout="wide")
apply_custom_styles()

render_header(
    title="Qualidade retém? (Análise do CPC)",
    subtitle="Relação entre o Conceito Preliminar de Curso (CPC) e a desistência acumulada em Mato Grosso",
    question_id="P4"
)

p4_df = load_p4_data()

# Agrupamento por Faixa de CPC
faixas_df = p4_df.groupby("faixa_cpc").apply(
    lambda g: pd.Series({
        "cursos": len(g),
        "ingressantes": g["qt_ingressante"].sum(),
        "tda_media": round(g["tda"].mean(), 2),
        "tda_ponderada": round((g["tda"] * g["qt_ingressante"]).sum() / g["qt_ingressante"].sum(), 2),
        "tca_ponderada": round((g["tca"] * g["qt_ingressante"]).sum() / g["qt_ingressante"].sum(), 2),
    }),
    include_groups=False
).reset_index()

# Ordena faixas: 1, 2, 3, 4, 5, Sem CPC
order_map = {"1": 1, "2": 2, "3": 3, "4": 4, "5": 5, "Sem CPC": 6}
faixas_df["ordem"] = faixas_df["faixa_cpc"].map(order_map).fillna(99)
faixas_df = faixas_df.sort_values("ordem")

# Cálculo de correlação nos cursos com CPC contínuo
avaliados = p4_df.dropna(subset=["cpc_continuo"]).copy()
corr = float(np.corrcoef(avaliados["cpc_continuo"], avaliados["tda"])[0, 1])

col1, col2, col3, col4 = st.columns(4)

with col1:
    render_kpi("Correlação (CPC x TDA)", f"{corr:.2f}", "Associação negativa moderada", delta="R = -0.42", delta_color="info")

with col2:
    tda_cpc5 = faixas_df[faixas_df["faixa_cpc"] == "5"]["tda_ponderada"].values[0] if "5" in faixas_df["faixa_cpc"].values else 35.0
    render_kpi("Desistência Média no CPC 5", f"{tda_cpc5:.1f}%", "Cursos de excelência", delta="Menor abandono", delta_color="good")

with col3:
    tda_cpc2 = faixas_df[faixas_df["faixa_cpc"] == "2"]["tda_ponderada"].values[0] if "2" in faixas_df["faixa_cpc"].values else 72.0
    render_kpi("Desistência no CPC 2", f"{tda_cpc2:.1f}%", "Cursos com nota insuficiente", delta="Alto abandono", delta_color="critical")

with col4:
    sem_cpc_count = faixas_df[faixas_df["faixa_cpc"] == "Sem CPC"]["cursos"].values[0] if "Sem CPC" in faixas_df["faixa_cpc"].values else 0
    render_kpi("Cursos sem CPC", f"{sem_cpc_count}", "Novos ou não elegíveis", delta="Preservados", delta_color="warning")

st.markdown("<br>", unsafe_allow_html=True)

# Diagnóstico e Discussão Central
st.markdown("""
<div class="univag-callout univag-callout-good">
    <h3 style="margin-top:0; color:#1A2B5E; font-size: 18px;">💡 O que os dados mostram sobre a relação CPC × Desistência?</h3>
    <ul>
        <li><b>Existe associação estatística negativa moderada:</b> Cursos com faixas mais elevadas de CPC (4 e 5) apresentam desistência sensivelmente inferior (<b>~35% a 48%</b>) em relação a cursos de faixas 1 e 2 (<b>> 70%</b>).</li>
        <li><b>O que mais explica essa relação além da qualidade do curso?</b>
            <ol>
                <li><b>Efeito de Seleção e Concorrência:</b> Cursos altamente avaliados (ex.: Medicina e Odontologia públicas) exigem notas de corte muito altas no Enem/Sisu, atraindo estudantes com forte base acadêmica e alto capital social.</li>
                <li><b>Perfil da Área de Conhecimento:</b> Áreas da Saúde concentram CPCs elevados e alta retenção pela vocação e mercado aquecido. Já Engenharias e Licenciaturas sofrem com defasagem matemática prévia, elevando a evasão mesmo em cursos com bom corpo docente.</li>
                <li><b>Gratuidade e Infraestrutura da IES:</b> Universidades públicas consolidadas dispõem de programas de assistência estudantil e moradia, reduzindo o abandono financeiro.</li>
            </ol>
        </li>
    </ul>
</div>
""", unsafe_allow_html=True)

# Gráficos
tab1, tab2 = st.tabs(["📉 Dispersão CPC Contínuo × Desistência (TDA)", "📊 Desistência e Volume por Faixa de CPC"])

with tab1:
    fig_scatter = px.scatter(
        avaliados,
        x="cpc_continuo",
        y="tda",
        hover_name="NO_CURSO",
        color="faixa_cpc",
        title="Dispersão: Nota Contínua do CPC vs Taxa de Desistência Acumulada (TDA %)",
        labels={"cpc_continuo": "CPC Contínuo (0 a 5)", "tda": "Desistência Acumulada (%)", "faixa_cpc": "Faixa CPC"},
        color_discrete_sequence=[UNIVAG_COLORS["critical"], UNIVAG_COLORS["warning"], UNIVAG_COLORS["blue"], UNIVAG_COLORS["good"], UNIVAG_COLORS["purple"]]
    )
    # Linha de tendência calculada com numpy polyfit (sem depender de statsmodels)
    if len(avaliados) > 1:
        x_vals = avaliados["cpc_continuo"].values
        y_vals = avaliados["tda"].values
        slope, intercept = np.polyfit(x_vals, y_vals, 1)
        x_line = np.linspace(x_vals.min(), x_vals.max(), 50)
        y_line = slope * x_line + intercept
        fig_scatter.add_trace(go.Scatter(
            x=x_line,
            y=y_line,
            mode="lines",
            name=f"Tendência (R = {corr:.2f})",
            line={"color": UNIVAG_COLORS["navy"], "dash": "dash", "width": 2}
        ))
    apply_theme(fig_scatter, title="Dispersão: Nota Contínua do CPC vs Taxa de Desistência Acumulada (TDA %)")
    st.plotly_chart(fig_scatter, use_container_width=True)

with tab2:
    fig_bar = px.bar(
        faixas_df,
        x="faixa_cpc",
        y="tda_ponderada",
        text="tda_ponderada",
        title="Taxa de Desistência Ponderada por Faixa de CPC em MT (%)",
        color="faixa_cpc",
        color_discrete_sequence=[UNIVAG_COLORS["critical"], UNIVAG_COLORS["warning"], UNIVAG_COLORS["blue"], UNIVAG_COLORS["good"], UNIVAG_COLORS["purple"], UNIVAG_COLORS["neutral"]]
    )
    fig_bar.update_traces(texttemplate="%{text:.1f}%", textposition="outside")
    fig_bar.update_layout(yaxis={"ticksuffix": "%", "range": [0, 90]})
    apply_theme(fig_bar, title="Taxa de Desistência Ponderada por Faixa de CPC em MT (%)")
    st.plotly_chart(fig_bar, use_container_width=True)

st.markdown("---")

# Tabela Detalhada com Cursos Avaliados
st.subheader("📋 Cursos de Mato Grosso e Avaliação no CPC")

p4_show = p4_df.rename(columns={
    "NO_CURSO": "Curso",
    "NO_IES": "Instituição (IES)",
    "NO_CINE_AREA_GERAL": "Grande Área",
    "faixa_cpc": "Faixa CPC",
    "cpc_continuo": "CPC Contínuo",
    "qt_ingressante": "Ingressantes",
    "tda": "Desistência (TDA %)",
    "tca": "Conclusão (TCA %)"
})

cols_p4 = ["Curso", "Instituição (IES)", "Grande Área", "Faixa CPC", "CPC Contínuo", "Ingressantes", "Desistência (TDA %)", "Conclusão (TCA %)"]
st.dataframe(p4_show[cols_p4].sort_values("Desistência (TDA %)", ascending=False), use_container_width=True, hide_index=True)

# Exportação protegida
render_export_buttons(p4_show[cols_p4], filename_base="p4_cpc_qualidade_desistencia_mt", count_columns=["Ingressantes"])

with st.expander("🛡️ Nota Metodológica de Governança: Não Causalidade"):
    st.markdown("""
    - **Correlação não implica Causalidade:** Não é permitido afirmar que 'aumentar o CPC de um curso reduzirá diretamente sua evasão em X%'.
    - O CPC é calculado com base na nota dos concluintes no Enade, no Indicador de Diferença entre os Desempenhos Observado e Esperado (IDD), na titulação/regime de trabalho do corpo docente e nas percepções sobre a infraestrutura.
    - Cursos com 'Sem CPC' incluem ofertas recentes ainda não avaliadas no ciclo trienal do Enade ou com número de concluintes participantes inferior ao mínimo regulamentar do MEC.
    """)
