"""Tela 2 — P1: Quanto da turma fica pelo caminho?

Pergunta oficial:
"Coorte 2015, presencial: quanto desistiu, concluiu e seguia em 2024? Em que ano a perda é maior?"
Fonte: Indicadores de Trajetória da Educação Superior do INEP.
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go

from components.styles import apply_custom_styles
from components.header import render_header
from components.charts import apply_theme
from components.export import render_export_buttons
from src.analytics.loader import load_p1_data, load_p2_data

st.set_page_config(page_title="P1: Trajetória 2015-2024 · Rota do Diploma", page_icon="📉", layout="wide")
apply_custom_styles()

render_header(
    title="Quanto da turma fica pelo caminho?",
    subtitle="Coorte 2015 Presencial em Mato Grosso: 10 anos de acompanhamento (2015 a 2024)",
    question_id="P1"
)

p1_df = load_p1_data()
p2_df = load_p2_data()

# 1. Top Question Pill Banner (Fiel à imagem de referência)
st.markdown("""
<div style="background-color: #EFF6FF; border: 1.5px solid #BFDBFE; color: #1E3A8A; border-radius: 16px; padding: 14px 22px; font-size: 15px; font-weight: 600; margin-bottom: 20px; box-shadow: 0 1px 3px rgba(0,0,0,0.03);">
    De cada 100 que entram numa graduação em MT, quantos chegam ao diploma, e em quais cursos a rota se perde?
</div>
""", unsafe_allow_html=True)

# 2. Controle Deslizante Interativo de Ano
ano_selecionado = st.slider(
    "Selecione o ano de acompanhamento da coorte:",
    min_value=2015,
    max_value=2024,
    value=2024,
    step=1,
    help="Arraste para visualizar a migração dinâmica dos 100 ingressantes a cada ano."
)

row_ano = p1_df[p1_df["nu_ano_referencia"] == ano_selecionado].iloc[0]

# 3. Quatro Cartões de KPIs Idênticos ao Layout da Imagem
c1, c2, c3, c4 = st.columns(4)

with c1:
    st.markdown(f"""
    <div style="background: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 16px; padding: 18px 20px; box-shadow: 0 1px 3px rgba(0,0,0,0.04);">
        <div style="font-size: 12px; font-weight: 500; color: #64748B;">Taxa de conclusão</div>
        <div style="font-size: 32px; font-weight: 800; color: #2563EB; margin: 4px 0;">{row_ano['tca']:.1f}</div>
        <div style="font-size: 11px; color: #94A3B8;">a cada 100 alunos · {ano_selecionado}</div>
    </div>
    """, unsafe_allow_html=True)

with c2:
    st.markdown(f"""
    <div style="background: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 16px; padding: 18px 20px; box-shadow: 0 1px 3px rgba(0,0,0,0.04);">
        <div style="font-size: 12px; font-weight: 500; color: #64748B;">Taxa de desistência</div>
        <div style="font-size: 32px; font-weight: 800; color: #EF4444; margin: 4px 0;">{row_ano['tda']:.1f}</div>
        <div style="font-size: 11px; color: #94A3B8;">a cada 100 alunos · {ano_selecionado}</div>
    </div>
    """, unsafe_allow_html=True)

with c3:
    st.markdown(f"""
    <div style="background: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 16px; padding: 18px 20px; box-shadow: 0 1px 3px rgba(0,0,0,0.04);">
        <div style="font-size: 12px; font-weight: 500; color: #64748B;">Retidos / cursando</div>
        <div style="font-size: 32px; font-weight: 800; color: #0D9488; margin: 4px 0;">{row_ano['tap']:.1f}</div>
        <div style="font-size: 11px; color: #94A3B8;">a cada 100 alunos · {ano_selecionado}</div>
    </div>
    """, unsafe_allow_html=True)

with c4:
    st.markdown("""
    <div style="background: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 16px; padding: 18px 20px; box-shadow: 0 1px 3px rgba(0,0,0,0.04);">
        <div style="font-size: 12px; font-weight: 500; color: #64748B;">Ano crítico de perda</div>
        <div style="font-size: 32px; font-weight: 800; color: #EA580C; margin: 4px 0;">2016</div>
        <div style="font-size: 11px; color: #94A3B8;">maior aumento de desistentes (+16,96 p.p.)</div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# 4. Dois Cartões Principais (Donut Chart + Line Chart) lado a lado
col_left, col_right = st.columns([5, 7])

with col_left:
    st.markdown(f"""
    <div style="font-size: 16px; font-weight: 700; color: #0F172A;">Funil do diploma</div>
    <div style="font-size: 12px; color: #64748B; margin-bottom: 8px;">Os 100 ingressantes, em {ano_selecionado}</div>
    """, unsafe_allow_html=True)

    # Donut Chart
    fig_donut = go.Figure(data=[go.Pie(
        labels=["Concluíram", "Desistiram", "Retidos"],
        values=[row_ano["tca"], row_ano["tda"], row_ano["tap"]],
        hole=0.65,
        marker=dict(colors=["#2563EB", "#EF4444", "#94A3B8"], line=dict(color="#FFFFFF", width=3)),
        textinfo="none",
        hoverinfo="label+percent",
        sort=False
    )])
    fig_donut.update_layout(
        showlegend=True,
        legend=dict(orientation="h", yanchor="bottom", y=-0.15, xanchor="center", x=0.5),
        height=320,
        margin=dict(t=10, b=30, l=10, r=10),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        annotations=[dict(text=f"<b>{ano_selecionado}</b>", x=0.5, y=0.5, font_size=20, showarrow=False, font_color="#1E293B")]
    )
    st.plotly_chart(fig_donut, use_container_width=True)

with col_right:
    st.markdown("""
    <div style="font-size: 16px; font-weight: 700; color: #0F172A;">Evolução da coorte 2015</div>
    <div style="font-size: 12px; color: #64748B; margin-bottom: 8px;">Por 100 ingressantes, ano a ano</div>
    """, unsafe_allow_html=True)

    # Line Chart com 3 linhas (Concluiu, Desistiu, Retido)
    fig_lines = go.Figure()

    # Concluiu
    fig_lines.add_trace(go.Scatter(
        x=p1_df["nu_ano_referencia"],
        y=p1_df["tca"],
        name="Concluiu",
        mode="lines+markers",
        line=dict(color="#2563EB", width=2.5),
        marker=dict(size=6, color="#2563EB")
    ))

    # Desistiu
    fig_lines.add_trace(go.Scatter(
        x=p1_df["nu_ano_referencia"],
        y=p1_df["tda"],
        name="Desistiu",
        mode="lines+markers",
        line=dict(color="#EF4444", width=2.5),
        marker=dict(size=6, color="#EF4444")
    ))

    # Retido
    fig_lines.add_trace(go.Scatter(
        x=p1_df["nu_ano_referencia"],
        y=p1_df["tap"],
        name="Retido",
        mode="lines+markers",
        line=dict(color="#94A3B8", width=2.5),
        marker=dict(size=6, color="#94A3B8")
    ))

    fig_lines.update_layout(
        height=320,
        margin=dict(t=10, b=30, l=30, r=20),
        yaxis=dict(
            range=[0, 100],
            title="por 100 ingressantes",
            gridcolor="#F1F5F9",
            linecolor="#CBD5E1",
            tickvals=[0, 10, 20, 30, 40, 50, 60, 70, 80, 90, 100]
        ),
        xaxis=dict(
            tickmode="linear",
            tick0=2015,
            dtick=1,
            gridcolor="#F8FAFC",
            linecolor="#CBD5E1"
        ),
        legend=dict(orientation="h", yanchor="bottom", y=-0.22, xanchor="center", x=0.5),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)"
    )
    st.plotly_chart(fig_lines, use_container_width=True)

st.markdown("---")

# 5. Tabela Detalhada com Supressão e Exportação
st.subheader("🔍 Tabela Completa de Balanço da Trajetória (Mato Grosso)")

p1_table_display = p1_df.rename(columns={
    "nu_ano_referencia": "Ano Ref.",
    "ano_curso": "Ano de Curso",
    "qt_ingressante": "Ingressantes",
    "tca": "Conclusão (TCA %)",
    "tda": "Desistência (TDA %)",
    "delta_tda": "Salto Anual (Δ TDA p.p.)",
    "tap": "Retidos (TAP %)"
})

cols_p1_show = ["Ano Ref.", "Ano de Curso", "Ingressantes", "Conclusão (TCA %)", "Desistência (TDA %)", "Salto Anual (Δ TDA p.p.)", "Retidos (TAP %)"]
st.dataframe(p1_table_display[cols_p1_show], use_container_width=True, hide_index=True)

# Exportação protegida
render_export_buttons(p1_table_display[cols_p1_show], filename_base="p1_trajetoria_coorte2015_mt", count_columns=["Ingressantes"])

with st.expander("📖 Interpretação Oficial e Notas Metodológicas"):
    st.markdown("""
    - **Situação da Coorte 2015 em 2024 (10 anos):** **60,2% desistiram**, **38,8% concluíram** e **1,0% permaneceram cursando** em Mato Grosso.
    - **Ano de Maior Salto:** O **2º ano (2016)** registra o maior pico de abandono (+16,96 p.p.), seguido por um segundo pico no 5º ano (2019) quando termina o prazo regular de integralização da maioria dos cursos.
    - **Equação de Balanço do INEP:** $\\text{TDA} + \\text{TCA} + \\text{TAP} = 100,0\\%$ em qualquer ano da trajetória.
    """)
