"""Tela 7 — B1: Desertos de ensino superior

Pergunta oficial:
"Quantas vagas presenciais existem por 100 jovens de 18 a 24 anos em cada município? Onde não há oferta?"
Fontes: Censo da Educação Superior 2024 (INEP) e População 18-24 anos do Censo Demográfico 2022 (IBGE SIDRA).
"""

import streamlit as st
import pandas as pd
import plotly.express as px

from components.styles import apply_custom_styles
from components.header import render_header
from components.kpi_cards import render_kpi
from components.charts import plot_horizontal_ranking, apply_theme, UNIVAG_COLORS
from components.export import render_export_buttons
from src.analytics.loader import load_b1_data

st.set_page_config(page_title="B1: Desertos de Ensino Superior · Rota do Diploma", page_icon="🏜️", layout="wide")
apply_custom_styles()

render_header(
    title="Desertos de ensino superior",
    subtitle="Vagas presenciais por 100 jovens de 18 a 24 anos e mapeamento da ausência de oferta nos municípios de MT",
    question_id="B1"
)

b1_df = load_b1_data()

# Estatísticas Gerais
total_mun = len(b1_df)
desertos_df = b1_df[b1_df["vagas_presenciais"] == 0]
qtd_desertos = len(desertos_df)
pct_desertos = (qtd_desertos / total_mun) * 100

vagas_tot = b1_df["vagas_presenciais"].sum()
pop_jovens_tot = b1_df["pop_18_24"].sum()
indicador_estadual = round((vagas_tot / pop_jovens_tot) * 100, 2)

col1, col2, col3, col4 = st.columns(4)

with col1:
    render_kpi("Média Estadual MT", f"{indicador_estadual:.1f}", "Vagas presenciais / 100 jovens", delta="Média estadual", delta_color="info")

with col2:
    render_kpi("Municípios sem Oferta", f"{qtd_desertos}", f"{pct_desertos:.1f}% dos municípios de MT", delta="Deserto presencial", delta_color="critical")

with col3:
    render_kpi("Vagas Presenciais Ofertadas", f"{vagas_tot:,.0f}".replace(",", "."), "Censo Superior 2024", delta="Presencial", delta_color="good")

with col4:
    render_kpi("Jovens de 18 a 24 anos", f"{pop_jovens_tot:,.0f}".replace(",", "."), "Censo IBGE 2022", delta="Demografia MT", delta_color="warning")

st.markdown("<br>", unsafe_allow_html=True)

# Diagnóstico Central
st.markdown(f"""
<div class="univag-callout univag-callout-warn">
    <h3 style="margin-top:0; color:#1A2B5E; font-size: 18px;">💡 Onde estão os vazios e a concentração de ensino superior em MT?</h3>
    <ul>
        <li><b>Alta Concentração nos Polos Regionais:</b> Quatro municípios concentram a esmagadora maioria das vagas presenciais: <b>Cuiabá (27,7 vagas/100 jovens)</b>, <b>Várzea Grande (22,3)</b>, <b>Rondonópolis (21,4)</b> e <b>Sinop (23,8)</b>.</li>
        <li><b>Desertos de Ensino Superior Presencial:</b> <b>{qtd_desertos} dos municípios analisados ({pct_desertos:.1f}%)</b> não registram nenhuma vaga presencial de graduação ativa. Jovens desses municípios dependem exclusivamente do deslocamento diário, mudança de cidade ou de polos EAD.</li>
        <li><b>Fórmula Oficial Aplicada:</b> <code>Vagas por 100 jovens = (Vagas Presenciais / População de 18 a 24 anos) × 100</code>.</li>
    </ul>
</div>
""", unsafe_allow_html=True)

# Gráficos
tab1, tab2 = st.tabs(["📊 Top Polos com Maior Oferta (Vagas / 100 Jovens)", "🏜️ Panorama da Distribuição Municipal"])

with tab1:
    top_polos = b1_df[b1_df["vagas_presenciais"] > 0].sort_values("vagas_por_100_jovens", ascending=False).head(10)
    fig_top = plot_horizontal_ranking(
        top_polos,
        cat_col="no_municipio",
        val_col="vagas_por_100_jovens",
        title="Top 10 Municípios com Maior Oferta Presencial (Vagas por 100 Jovens de 18 a 24 Anos)",
        color=UNIVAG_COLORS["blue"],
        suffix=" vagas/100"
    )
    st.plotly_chart(fig_top, use_container_width=True)

with tab2:
    classif_df = b1_df["classificacao"].value_counts().reset_index()
    classif_df.columns = ["Classificação", "Municípios"]
    fig_pie = px.pie(
        classif_df,
        names="Classificação",
        values="Municípios",
        title="Distribuição dos Municípios de MT por Nível de Oferta Presencial",
        color="Classificação",
        color_discrete_map={
            "Deserto de Ensino Superior (0 vagas)": UNIVAG_COLORS["critical"],
            "Alta Oferta (>= 20 vagas/100)": UNIVAG_COLORS["good"],
            "Oferta Moderada (< 20 vagas/100)": UNIVAG_COLORS["warning"]
        }
    )
    apply_theme(fig_pie, title="Distribuição dos Municípios de MT por Nível de Oferta Presencial")
    st.plotly_chart(fig_pie, use_container_width=True)

st.markdown("---")

# Tabela Municipal com Filtro
st.subheader("📋 Tabela Completa de Indicadores Municipais de Mato Grosso")

c_sel1, c_sel2 = st.columns(2)
with c_sel1:
    classif_filtro = ["Todas as Classificações"] + sorted(b1_df["classificacao"].unique().tolist())
    classif_escolhida = st.selectbox("Filtrar por Nível de Oferta", classif_filtro)
with c_sel2:
    busca_nome = st.text_input("Buscar Município pelo Nome")

b1_tabela = b1_df.copy()
if classif_escolhida != "Todas as Classificações":
    b1_tabela = b1_tabela[b1_tabela["classificacao"] == classif_escolhida]
if busca_nome:
    b1_tabela = b1_tabela[b1_tabela["no_municipio"].str.contains(busca_nome, case=False, na=False)]

b1_show = b1_tabela.rename(columns={
    "co_municipio": "Código IBGE",
    "no_municipio": "Município",
    "pop_18_24": "População 18-24 Anos (IBGE)",
    "vagas_presenciais": "Vagas Presenciais de Graduação",
    "vagas_por_100_jovens": "Vagas por 100 Jovens",
    "classificacao": "Classificação"
})

cols_b1 = ["Código IBGE", "Município", "População 18-24 Anos (IBGE)", "Vagas Presenciais de Graduação", "Vagas por 100 Jovens", "Classificação"]
st.dataframe(b1_show[cols_b1].sort_values("Vagas por 100 Jovens", ascending=False), use_container_width=True, hide_index=True)

# Exportação protegida
render_export_buttons(b1_show[cols_b1], filename_base="b1_oferta_municipal_desertos_mt", count_columns=["População 18-24 Anos (IBGE)", "Vagas Presenciais de Graduação"])

with st.expander("🛡️ Nota Metodológica: Diferença entre Ausência de Oferta e Dados Faltantes"):
    st.markdown("""
    - **Ausência de Oferta Comprovada:** O município foi checado no Censo da Educação Superior 2024 e não possui registro de cursos de graduação presencial em funcionamento (Vagas = 0).
    - **População Censitária:** A população na faixa etária de 18 a 24 anos provém dos resultados oficiais por idade do Censo Demográfico 2022 do IBGE (Tabela 9514 do SIDRA).
    - Municípios que contam exclusivamente com polos de apoio presencial para cursos EAD não entram na contagem de vagas presenciais tradicionais de graduação.
    """)
