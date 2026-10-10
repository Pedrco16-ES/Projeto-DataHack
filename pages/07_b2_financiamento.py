"""Tela 8 — B2: Financiamento e permanência

Pergunta oficial:
"Qual é o peso de FIES e ProUni na rede privada entre 2021 e 2024? Cursos com mais financiados evadem menos?"
Fonte: Censo da Educação Superior do INEP (Cursos da Rede Privada em Mato Grosso).
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
from src.analytics.loader import load_b2_data

st.set_page_config(page_title="B2: Financiamento e Permanência · Rota do Diploma", page_icon="💰", layout="wide")
apply_custom_styles()

render_header(
    title="Financiamento e permanência (FIES e ProUni)",
    subtitle="Participação dos programas de financiamento estudantil e bolsas na rede privada de MT (2021–2024)",
    question_id="B2"
)

b2_df = load_b2_data()

# Dados mais recentes (2024)
d2024 = b2_df[b2_df["nu_ano_censo"] == 2024].iloc[0]

col1, col2, col3, col4 = st.columns(4)

with col1:
    render_kpi("Peso do FIES (Ingressantes 2024)", f"{d2024['pct_fies']:.1f}%", f"{d2024['ingressantes_fies']:,} estudantes".replace(",", "."), delta="FIES", delta_color="info")

with col2:
    render_kpi("Peso do ProUni (Ingressantes 2024)", f"{d2024['pct_prouni']:.1f}%", f"Bolsas integrais e parciais", delta="ProUni", delta_color="good")

with col3:
    render_kpi("Total Financiados / Bolsistas", f"{d2024['pct_apoio_total']:.1f}%", f"{d2024['total_financiados_bolsistas']:,} ingressantes".replace(",", "."), delta="Cobertura", delta_color="purple")

with col4:
    dif_pp = d2024["diferencial_permanencia_pp"]
    render_kpi("Vantagem de Retenção", f"-{dif_pp:.1f} p.p.", "Menor desvinculação em financiados", delta="Retenção", delta_color="good")

st.markdown("<br>", unsafe_allow_html=True)

# Diagnóstico Central
st.markdown(f"""
<div class="univag-callout univag-callout-good">
    <h3 style="margin-top:0; color:#1A2B5E; font-size: 18px;">💡 O que os dados revelam sobre o impacto do FIES e ProUni na Rede Privada de MT:</h3>
    <ul>
        <li><b>Peso dos Programas nos Ingressantes Privados:</b> Em 2024, <b>{d2024['pct_apoio_total']:.1f}%</b> dos novos estudantes contavam com apoio governamental ({d2024['pct_fies']:.1f}% via FIES e {d2024['pct_prouni']:.1f}% via bolsas ProUni Integral ou Parcial).</li>
        <li><b>Cursos com mais financiados evadem menos?</b> Sim, de forma substancial. Cursos e grupos com maior contingente de alunos financiados apresentam <b>taxa média de desvinculação anual de {d2024['taxa_desvinculacao_financiados']:.1f}%</b>, contra <b>{d2024['taxa_desvinculacao_nao_financiados']:.1f}%</b> entre estudantes sem financiamento (<b>diferencial de {dif_pp:.1f} pontos percentuais</b> a favor da permanência).</li>
        <li><b>Explicação Teórica e de Negócio:</b> A segurança de cobertura financeira das mensalidades protege os estudantes contra oscilações de renda familiar e desemprego, além de criar um compromisso formal com a continuidade acadêmica para manutenção da bolsa ou crédito.</li>
    </ul>
</div>
""", unsafe_allow_html=True)

# Gráficos
tab1, tab2 = st.tabs(["📈 Evolução do Apoio Financeiro (2021–2024)", "📊 Comparativo de Desvinculação Anual"])

with tab1:
    fig_evol = go.Figure()
    fig_evol.add_trace(go.Scatter(
        x=b2_df["nu_ano_censo"],
        y=b2_df["pct_fies"],
        mode="lines+markers",
        name="% FIES nos Ingressantes",
        line={"color": UNIVAG_COLORS["blue"], "width": 3}
    ))
    fig_evol.add_trace(go.Scatter(
        x=b2_df["nu_ano_censo"],
        y=b2_df["pct_prouni"],
        mode="lines+markers",
        name="% ProUni nos Ingressantes",
        line={"color": UNIVAG_COLORS["purple"], "width": 3}
    ))
    fig_evol.add_trace(go.Scatter(
        x=b2_df["nu_ano_censo"],
        y=b2_df["pct_apoio_total"],
        mode="lines+markers",
        name="% Total Financiados + Bolsistas",
        line={"color": UNIVAG_COLORS["good"], "width": 3, "dash": "dash"}
    ))
    fig_evol.update_layout(yaxis={"ticksuffix": "%", "title": "Participação nos Ingressantes (%)"})
    apply_theme(fig_evol, title="Evolução da Participação do FIES e ProUni na Rede Privada de MT (%)")
    st.plotly_chart(fig_evol, use_container_width=True)

with tab2:
    fig_comp = go.Figure()
    fig_comp.add_trace(go.Bar(
        x=b2_df["nu_ano_censo"],
        y=b2_df["taxa_desvinculacao_financiados"],
        name="Desvinculação: Estudantes Financiados / Bolsistas",
        marker_color=UNIVAG_COLORS["good"],
        text=[f"{v:.1f}%" for v in b2_df["taxa_desvinculacao_financiados"]],
        textposition="inside"
    ))
    fig_comp.add_trace(go.Bar(
        x=b2_df["nu_ano_censo"],
        y=b2_df["taxa_desvinculacao_nao_financiados"],
        name="Desvinculação: Não Financiados",
        marker_color=UNIVAG_COLORS["critical"],
        text=[f"{v:.1f}%" for v in b2_df["taxa_desvinculacao_nao_financiados"]],
        textposition="inside"
    ))
    fig_comp.update_layout(barmode="group", yaxis={"ticksuffix": "%", "title": "Taxa de Desvinculação Anual (%)"})
    apply_theme(fig_comp, title="Comparativo: Taxa de Desvinculação entre Alunos Financiados vs Não Financiados")
    st.plotly_chart(fig_comp, use_container_width=True)

st.markdown("---")

# Tabela Analítica
st.subheader("📋 Tabela Analítica de Financiamento na Rede Privada MT (2021 a 2024)")

b2_show = b2_df.rename(columns={
    "nu_ano_censo": "Ano Censo",
    "ingressantes_total": "Ingressantes Totais",
    "ingressantes_fies": "Ingressantes FIES",
    "ingressantes_prouni_integral": "ProUni Integral",
    "ingressantes_prouni_parcial": "ProUni Parcial",
    "total_financiados_bolsistas": "Total Financiados/Bolsistas",
    "pct_fies": "% FIES",
    "pct_prouni": "% ProUni",
    "pct_apoio_total": "% Apoio Total",
    "taxa_desvinculacao_financiados": "Desvinculação Financiados (%)",
    "taxa_desvinculacao_nao_financiados": "Desvinculação Não Financiados (%)",
    "diferencial_permanencia_pp": "Diferencial de Retenção (p.p.)"
})

cols_b2 = [
    "Ano Censo", "Ingressantes Totais", "Total Financiados/Bolsistas",
    "% FIES", "% ProUni", "% Apoio Total",
    "Desvinculação Financiados (%)", "Desvinculação Não Financiados (%)", "Diferencial de Retenção (p.p.)"
]
st.dataframe(b2_show[cols_b2], use_container_width=True, hide_index=True)

# Exportação protegida
render_export_buttons(b2_show[cols_b2], filename_base="b2_financiamento_permanencia_privada_mt", count_columns=["Ingressantes Totais", "Total Financiados/Bolsistas"])

with st.expander("🛡️ Nota Metodológica Obrigatória: Análise Agregada vs Individual"):
    st.markdown("""
    - **Nível da Análise:** Os dados do Censo de Cursos disponibilizados publicamente agregam as informações por curso/município.
    - Portanto, não é permitido afirmar a causalidade estrita no nível de microdados do estudante individual sem alertar que a comparação foi mensurada pela **composição agregada das turmas**.
    - **Sobreposição de Bolsas:** O FIES e o ProUni Parcial (50%) podem ser combinados legalmente pelo mesmo estudante. A soma das modalidades leva em consideração os grupos exclusivos documentados no contrato de ingestão para evitar contagem duplicada.
    """)
