"""Tela 3 — P2: Onde a rota mais se perde?

Pergunta oficial:
"Quais cursos e áreas possuem maior e menor desistência? Como comparar as coortes?"
Fonte: Indicadores de Trajetória da Educação Superior do INEP.
"""

import streamlit as st
import pandas as pd
import plotly.express as px

from components.styles import apply_custom_styles
from components.header import render_header
from components.kpi_cards import render_kpi
from components.charts import plot_horizontal_ranking, apply_theme, UNIVAG_COLORS
from components.export import render_export_buttons
from src.analytics.loader import load_p2_data

st.set_page_config(page_title="P2: Cursos e Áreas · Rota do Diploma", page_icon="🧭", layout="wide")
apply_custom_styles()

render_header(
    title="Onde a rota mais se perde?",
    subtitle="Rankings de maior e menor desistência por curso (rótulo CINE) e grandes áreas do conhecimento em MT",
    question_id="P2"
)

p2_df = load_p2_data()

# Filtro de proteção: Cursos com representatividade (>= 50 ingressantes para ranking robusto)
cursos_sig = p2_df[p2_df["qt_ingressante"] >= 50].copy()

top_maior = cursos_sig.sort_values("tda", ascending=False).head(5)
top_menor = cursos_sig.sort_values("tda", ascending=True).head(5)

# KPIs no topo
col1, col2, col3, col4 = st.columns(4)

with col1:
    maior_curso = top_maior.iloc[0]
    render_kpi("Maior Desistência (Curso)", f"{maior_curso['tda']:.1f}%", f"{maior_curso['NO_CINE_ROTULO']}", delta="Crítico", delta_color="critical")

with col2:
    menor_curso = top_menor.iloc[0]
    render_kpi("Menor Desistência (Curso)", f"{menor_curso['tda']:.1f}%", f"{menor_curso['NO_CINE_ROTULO']}", delta="Alta retenção", delta_color="good")

with col3:
    render_kpi("Área com Maior Desistência", "71,9%", "Computação e TIC", delta="Perda massiva", delta_color="critical")

with col4:
    render_kpi("Área com Menor Desistência", "53,9%", "Saúde e Bem-Estar", delta="Maior conclusão", delta_color="good")

st.markdown("<br>", unsafe_allow_html=True)

# Cartão de Diagnóstico
st.markdown("""
<div class="univag-callout univag-callout-good">
    <h3 style="margin-top:0; color:#1A2B5E; font-size: 18px;">💡 Resumo dos Achados — Cursos e Áreas em Mato Grosso:</h3>
    <ul>
        <li><b>Concentração da Evasão:</b> Cursos de <b>Engenharias e Ciências Exatas / TI</b> apresentam taxas de desistência acumulada entre <b>75% e 87%</b>. Engenharia Ambiental (87,4%), Licenciatura em Matemática (84,3%) e Ciência da Computação (76,4%) figuram no topo das maiores perdas.</li>
        <li><b>Cursos com Alta Retenção:</b> <b>Medicina</b> tem apenas <b>14,8% de desistência</b> (85,2% de conclusão), seguida por <b>Odontologia (33,7%)</b> e <b>Pedagogia (41,1%)</b>.</li>
        <li><b>Comparação entre Áreas CINE:</b> A área de <i>Computação e Tecnologias da Informação</i> perde mais de 7 a cada 10 estudantes, enquanto <i>Saúde e Bem-Estar</i> conclui mais de 45% dos ingressantes.</li>
    </ul>
</div>
""", unsafe_allow_html=True)

# Gráficos de Ranking
st.subheader("📊 Rankings Comparativos de Desistência Acumulada (TDA)")

col_g1, col_g2 = st.columns(2)

with col_g1:
    fig_maior = plot_horizontal_ranking(
        top_maior,
        cat_col="NO_CINE_ROTULO",
        val_col="tda",
        title="Top 5 Cursos com MAIOR Desistência (TDA %)",
        color=UNIVAG_COLORS["critical"]
    )
    st.plotly_chart(fig_maior, use_container_width=True)

with col_g2:
    fig_menor = plot_horizontal_ranking(
        top_menor,
        cat_col="NO_CINE_ROTULO",
        val_col="tda",
        title="Top 5 Cursos com MENOR Desistência (TDA %)",
        color=UNIVAG_COLORS["good"]
    )
    st.plotly_chart(fig_menor, use_container_width=True)

st.markdown("---")

# Comparação por Grande Área do Conhecimento
st.subheader("🏛️ Desistência Acumulada por Grande Área CINE")

# Agregação por Área
area_df = p2_df.groupby("NO_CINE_AREA_GERAL").apply(
    lambda g: pd.Series({
        "ingressantes": g["qt_ingressante"].sum(),
        "tda_ponderada": round((g["tda"] * g["qt_ingressante"]).sum() / g["qt_ingressante"].sum(), 2),
        "tca_ponderada": round((g["tca"] * g["qt_ingressante"]).sum() / g["qt_ingressante"].sum(), 2)
    }),
    include_groups=False
).reset_index().sort_values("tda_ponderada", ascending=True)

fig_area = plot_horizontal_ranking(
    area_df,
    cat_col="NO_CINE_AREA_GERAL",
    val_col="tda_ponderada",
    title="Desistência Acumulada Ponderada por Grande Área CINE (%)",
    color=UNIVAG_COLORS["purple"]
)
st.plotly_chart(fig_area, use_container_width=True)

st.markdown("---")

# Tabela Completa com Filtros e Exportação
st.subheader("🔍 Tabela Completa de Cursos (Rótulo CINE)")

c_f1, c_f2 = st.columns(2)
with c_f1:
    areas = ["Todas"] + sorted(p2_df["NO_CINE_AREA_GERAL"].dropna().unique().tolist())
    area_sel = st.selectbox("Filtrar Grande Área CINE", areas)
with c_f2:
    graus = ["Todos"] + sorted(p2_df["grau_academico"].dropna().unique().tolist())
    grau_sel = st.selectbox("Filtrar Grau", graus)

tab_df = p2_df.copy()
if area_sel != "Todas":
    tab_df = tab_df[tab_df["NO_CINE_AREA_GERAL"] == area_sel]
if grau_sel != "Todos":
    tab_df = tab_df[tab_df["grau_academico"] == grau_sel]

tab_df = tab_df.rename(columns={
    "NO_CINE_ROTULO": "Curso (Rótulo CINE)",
    "NO_CINE_AREA_GERAL": "Grande Área",
    "grau_academico": "Grau",
    "qt_ingressante": "Ingressantes",
    "tda": "Desistência (TDA %)",
    "tca": "Conclusão (TCA %)",
    "tap": "Permanência (TAP %)"
})

cols_t = ["Curso (Rótulo CINE)", "Grande Área", "Grau", "Ingressantes", "Desistência (TDA %)", "Conclusão (TCA %)", "Permanência (TAP %)"]
st.dataframe(tab_df[cols_t].sort_values("Desistência (TDA %)", ascending=False), use_container_width=True, hide_index=True)

# Exportação protegida
render_export_buttons(tab_df[cols_t], filename_base="p2_cursos_areas_desistencia_mt", count_columns=["Ingressantes"])

with st.expander("⚠️ Alerta Metodológico: Como comparar coortes?"):
    st.markdown("""
    - **Horizontes Equivalentes:** Para comparar turmas de anos de ingresso diferentes (ex.: Coorte 2015 vs Coorte 2018), é obrigatório comparar no **mesmo ano relativo de curso** (ex.: comparar ambas no 4º ano de acompanhamento). Nunca compare uma turma com 10 anos de histórico com outra recém-iniciada no 2º ano.
    - **Proteção para Turmas Pequenas:** Cursos com menos de 10 alunos são suprimidos e agrupados para preservar o sigilo estatístico e evitar distorções amostrais.
    """)
