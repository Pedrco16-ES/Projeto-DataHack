"""Tela 6 — P5: O funil das licenciaturas

Pergunta oficial:
"Quanto desiste nas licenciaturas e quanto dos concluintes é proficiente no Enade 2025?"
Fontes: Indicadores de Trajetória da Educação Superior e Conceito Enade 2025 (Licenciaturas).
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from components.styles import apply_custom_styles
from components.header import render_header
from components.kpi_cards import render_kpi
from components.charts import plot_horizontal_ranking, apply_theme, UNIVAG_COLORS
from components.export import render_export_buttons
from src.analytics.loader import load_p5_data

st.set_page_config(page_title="P5: O Funil das Licenciaturas · Rota do Diploma", page_icon="📚", layout="wide")
apply_custom_styles()

render_header(
    title="O funil das licenciaturas",
    subtitle="Diagnóstico duplo da formação docente em MT: abandono na graduação e proficiência no Enade",
    question_id="P5"
)

p5_df = load_p5_data()

# Totais das Licenciaturas
tot_ing_lic = p5_df["qt_ingressante"].sum()
tda_lic_medio = round((p5_df["tda"] * p5_df["qt_ingressante"]).sum() / tot_ing_lic, 1)
tca_lic_medio = round((p5_df["tca"] * p5_df["qt_ingressante"]).sum() / tot_ing_lic, 1)
prof_media = round((p5_df["enade_proficiente_pct"] * p5_df["concluintes_avaliados_enade"]).sum() / p5_df["concluintes_avaliados_enade"].sum(), 1)

col1, col2, col3, col4 = st.columns(4)

with col1:
    render_kpi("Ingressantes em Licenciaturas", f"{tot_ing_lic:,.0f}".replace(",", "."), "Coorte 2015 MT", delta="Docência", delta_color="info")

with col2:
    render_kpi("Desistência Média (TDA)", f"{tda_lic_medio:.1f}%", "Perda ao longo do curso", delta="Abandono massivo", delta_color="critical")

with col3:
    render_kpi("Conclusão Média (TCA)", f"{tca_lic_medio:.1f}%", "Concluíram o curso", delta="Formados", delta_color="good")

with col4:
    render_kpi("Proficiência Enade 2025", f"{prof_media:.1f}%", "Atingem padrão de proficiência", delta="Alerta pedagógico", delta_color="warning")

st.markdown("<br>", unsafe_allow_html=True)

# Diagnóstico Central
st.markdown("""
<div class="univag-callout univag-callout-warn">
    <h3 style="margin-top:0; color:#1A2B5E; font-size: 18px;">💡 O Duplo Funil da Formação de Professores em Mato Grosso:</h3>
    <ul>
        <li><b>1º Gargalo (Abandono na Graduação):</b> Nas licenciaturas de Mato Grosso, <b>57,5% dos ingressantes desistem</b>. Em áreas exatas como <b>Matemática (84,3%)</b>, <b>Química (82,5%)</b> e <b>Física (79,1%)</b>, a evasão é catastrófica, restando menos de 20 formados a cada 100 ingressantes.</li>
        <li><b>2º Gargalo (Proficiência no Enade 2025):</b> Entre os poucos estudantes que concluem a licenciatura, apenas <b>21,8% em Matemática</b> e <b>19,5% em Física</b> alcançam o nível desejado de proficiência na avaliação docente do Enade.</li>
        <li><b>Conclusão de Impacto:</b> O estado de Mato Grosso enfrenta uma severa escassez qualitativa e quantitativa de docentes de Ciências e Matemática para o ensino básico.</li>
    </ul>
</div>
""", unsafe_allow_html=True)

# Dois Painéis Visuais: Painel A (Trajetória) e Painel B (Enade 2025)
st.subheader("📊 Painel Duplo: Trajetória da Turma vs Proficiência Docente Enade")

c_p1, c_p2 = st.columns(2)

with c_p1:
    st.markdown("#### 📉 Painel A: Desistência na Trajetória (TDA %)")
    fig_a = plot_horizontal_ranking(
        p5_df,
        cat_col="NO_CINE_ROTULO",
        val_col="tda",
        title="Taxa de Desistência por Área de Licenciatura (MT)",
        color=UNIVAG_COLORS["critical"]
    )
    st.plotly_chart(fig_a, use_container_width=True)
    st.caption("Fonte: Indicadores de Trajetória INEP (Coorte 2015 MT). População: Ingressantes no curso.")

with c_p2:
    st.markdown("#### 🎯 Painel B: Proficiência no Enade 2025 (%)")
    fig_b = plot_horizontal_ranking(
        p5_df,
        cat_col="NO_CINE_ROTULO",
        val_col="enade_proficiente_pct",
        title="% Concluintes com Padrão de Proficiência (Enade Licenciaturas)",
        color=UNIVAG_COLORS["blue"]
    )
    st.plotly_chart(fig_b, use_container_width=True)
    st.caption("Fonte: Conceito Enade 2025 Licenciaturas. População: Concluintes participantes da prova.")

st.markdown("---")

# Tabela Detalhada com Supressão
st.subheader("📋 Indicadores Integrados por Área de Licenciatura")

p5_show = p5_df.rename(columns={
    "NO_CINE_ROTULO": "Área da Licenciatura",
    "qt_cursos": "Cursos em MT",
    "qt_ingressante": "Ingressantes",
    "tda": "Desistência (TDA %)",
    "tca": "Conclusão (TCA %)",
    "enade_proficiente_pct": "Proficiência Enade 2025 (%)",
    "concluintes_avaliados_enade": "Concluintes Avaliados Enade"
})

cols_p5 = ["Área da Licenciatura", "Cursos em MT", "Ingressantes", "Desistência (TDA %)", "Conclusão (TCA %)", "Proficiência Enade 2025 (%)", "Concluintes Avaliados Enade"]
st.dataframe(p5_show[cols_p5].sort_values("Desistência (TDA %)", ascending=False), use_container_width=True, hide_index=True)

# Exportação protegida
render_export_buttons(p5_show[cols_p5], filename_base="p5_licenciaturas_funil_enade_mt", count_columns=["Ingressantes", "Concluintes Avaliados Enade"])

with st.expander("🛡️ Nota Metodológica Obrigatória: Diferença de Populações e Denominadores"):
    st.markdown("""
    - **Populações Distintas:** A união entre a Trajetória e o Enade ocorre pelo código/rótulo do curso, **mas as populações são diferentes**.
    - Os ingressantes da Trajetória (Painel A) pertencem à coorte que ingressou em 2015.
    - Os concluintes avaliados no Enade 2025 (Painel B) são os estudantes que realizaram a avaliação teórica e prática docente em 2025.
    - Portanto, os dois painéis devem ser interpretados como análises complementares da formação docente em MT, e não como um funil individual fechado.
    """)
