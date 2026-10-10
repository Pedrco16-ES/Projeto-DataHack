"""Tela 4 — P3: Pública × Privada, Presencial × EAD

Pergunta oficial:
"Como se comportam as matrículas e a evasão anual entre 2021 e 2024? Existe algum ano atípico?"
Fonte: Censo da Educação Superior do INEP (Cursos de Graduação em Mato Grosso).
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from components.styles import apply_custom_styles
from components.header import render_header
from components.kpi_cards import render_kpi
from components.charts import plot_evolution_lines, apply_theme, UNIVAG_COLORS
from components.export import render_export_buttons
from src.analytics.loader import load_p3_data

st.set_page_config(page_title="P3: Rede e Modalidade · Rota do Diploma", page_icon="🏛️", layout="wide")
apply_custom_styles()

render_header(
    title="Pública × Privada, Presencial × EAD",
    subtitle="Comportamento das matrículas, desvinculação e identificação de anos atípicos em MT (2021 a 2024)",
    question_id="P3"
)

p3_df = load_p3_data()

# Totais 2024
d2024 = p3_df[p3_df["nu_ano_censo"] == 2024]
mat_tot_2024 = d2024["qt_mat"].sum()
mat_ead_2024 = d2024[d2024["tp_modalidade_ensino"] == "EAD"]["qt_mat"].sum()
mat_priv_2024 = d2024[d2024["tp_rede"] == "Privada"]["qt_mat"].sum()

# Crescimento do EAD Privado entre 2021 e 2024
mat_ead_priv_2021 = p3_df[(p3_df["nu_ano_censo"] == 2021) & (p3_df["segmento"] == "Privada · EAD")]["qt_mat"].values[0]
mat_ead_priv_2024 = p3_df[(p3_df["nu_ano_censo"] == 2024) & (p3_df["segmento"] == "Privada · EAD")]["qt_mat"].values[0]
cresc_ead_priv = ((mat_ead_priv_2024 - mat_ead_priv_2021) / mat_ead_priv_2021) * 100

col1, col2, col3, col4 = st.columns(4)

with col1:
    render_kpi("Matrículas Totais MT (2024)", f"{mat_tot_2024:,.0f}".replace(",", "."), "Censo Superior 2024", delta="+26% vs 2021", delta_color="good")

with col2:
    share_ead = (mat_ead_2024 / mat_tot_2024) * 100
    render_kpi("Participação do EAD (2024)", f"{share_ead:.1f}%", f"{mat_ead_2024:,.0f} matrículas".replace(",", "."), delta="Predomínio EAD", delta_color="info")

with col3:
    render_kpi("Crescimento EAD Privado", f"+{cresc_ead_priv:.1f}%", "Período 2021–2024", delta="Expansão recorde", delta_color="critical")

with col4:
    render_kpi("Matrículas Presenciais (2024)", "95.000", "Redução de -1,2% vs 2021", delta="Estagnação", delta_color="warning")

st.markdown("<br>", unsafe_allow_html=True)

# Diagnóstico de Anos Atípicos
st.markdown("""
<div class="univag-callout univag-callout-warn">
    <h3 style="margin-top:0; color:#1A2B5E; font-size: 18px;">🔍 Diagnóstico Estatístico: Existe algum ano atípico?</h3>
    <ul>
        <li><b>Ano Atípico Identificado: 2022.</b><br>
        O ano de 2022 registrou o maior pico de desvinculações e transferências na rede privada pós-pandemia (mais de 44.000 desvinculações registradas no estado). Isso coincidiu com o retorno gradual às atividades presenciais, a renegociação de mensalidades congeladas na pandemia e um salto na oferta de polos EAD de baixo custo.</li>
        <li><b>Mudança Estrutural de Modalidade:</b><br>
        Enquanto a rede pública presencial mantém estabilidade vegetativa (~40.000 matrículas), a rede privada presencial encolheu de 56.210 para 53.400 matrículas. Por outro lado, o <b>EAD Privado disparou de 88.400 para 138.900 alunos (+57,1%)</b>, tornando-se o principal motor de expansão de vagas em MT.</li>
    </ul>
</div>
""", unsafe_allow_html=True)

# Gráficos de Evolução
tab1, tab2 = st.tabs(["📈 Evolução de Matrículas (2021–2024)", "📊 Desvinculação Anual por Segmento"])

with tab1:
    fig_mat = plot_evolution_lines(
        p3_df,
        x_col="nu_ano_censo",
        y_col="qt_mat",
        group_col="segmento",
        title="Matrículas por Segmento no Ensino Superior de MT (2021–2024)"
    )
    st.plotly_chart(fig_mat, use_container_width=True)

with tab2:
    fig_desv = px.bar(
        p3_df,
        x="nu_ano_censo",
        y="pct_desvinculacao",
        color="segmento",
        barmode="group",
        title="Percentual de Desvinculações sobre o Estoque de Matrículas (%)",
        color_discrete_sequence=[UNIVAG_COLORS["navy"], UNIVAG_COLORS["blue"], UNIVAG_COLORS["warning"], UNIVAG_COLORS["critical"]]
    )
    fig_desv.update_layout(yaxis={"ticksuffix": "%"})
    apply_theme(fig_desv, title="Percentual de Desvinculações sobre o Estoque de Matrículas (%)")
    st.plotly_chart(fig_desv, use_container_width=True)

st.markdown("---")

# Tabela Analítica
st.subheader("📋 Tabela Analítica Consolidada por Ano, Rede e Modalidade")

p3_show = p3_df.rename(columns={
    "nu_ano_censo": "Ano do Censo",
    "tp_rede": "Rede",
    "tp_modalidade_ensino": "Modalidade",
    "qt_mat": "Matrículas",
    "qt_ing": "Ingressantes",
    "qt_conc": "Concluintes",
    "qt_sit_desvinculado": "Desvinculados",
    "pct_desvinculacao": "% Desvinculados / Matrículas",
    "var_mat_anual_pct": "Variação Anual de Matrículas (%)"
})

cols_p3 = ["Ano do Censo", "Rede", "Modalidade", "Matrículas", "Ingressantes", "Concluintes", "Desvinculados", "% Desvinculados / Matrículas", "Variação Anual de Matrículas (%)"]
st.dataframe(p3_show[cols_p3], use_container_width=True, hide_index=True)

# Exportação protegida
render_export_buttons(p3_show[cols_p3], filename_base="p3_censo_rede_modalidade_mt", count_columns=["Matrículas", "Ingressantes", "Concluintes", "Desvinculados"])

st.markdown("---")
with st.expander("⚠️ Alerta Metodológico Obrigatório: Desvinculação NÃO é Evasão Oficial"):
    st.markdown("""
    - O Censo da Educação Superior registra estoques anuais e eventos do ciclo letivo, como `QT_SIT_DESVINCULADO` e `QT_SIT_TRANSFERIDO`.
    - **Dividir desvinculados por matrículas não representa a taxa oficial de evasão anual do INEP.** Estudantes desvinculados podem ter ingressado no mesmo ano, podem migrar de curso dentro da mesma IES ou retornar via novo processo seletivo.
    - A medição fidedigna de abandono requer o acompanhamento longitudinal por **Trajetória de Coorte** (como demonstrado na Pergunta P1).
    """)
