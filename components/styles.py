"""Estilos globais e tokens de design oficiais Univag para o dashboard Rota do Diploma."""

from pathlib import Path
import streamlit as st

UNIVAG_CSS = """
<style>
/* =====================================================================
   UNIVAG — Guia de Estilos para Dashboards — DataHack 2026
   Tokens de Cores e Tipografia Oficial
   ===================================================================== */
:root {
    --brand-navy: #1A2B5E;
    --brand-blue: #0066CC;
    --brand-light: #00AEF0;
    --brand-white: #FFFFFF;
    --brand-purple: #6F42C1;
    --brand-pink: #E83E8C;
    --page: #F8F9FA;
    --surface: #FFFFFF;
    --surface-muted: #E9ECEF;
    --border: #DEE2E6;
    --ink: #1A2B5E;
    --ink-2: #6C757D;
    --action: #0066CC;
    --status-good: #28A745;
    --status-good-bg: #EAF6EC;
    --status-good-ink: #1B5E20;
    --status-warning: #FFC107;
    --status-warning-bg: #FFF8E1;
    --status-warning-ink: #7A5A00;
    --status-critical: #DC3545;
    --status-critical-bg: #FFEBEE;
    --status-critical-ink: #B71C1C;
    --status-info: #17A2B8;
    --status-info-bg: #E0F2F1;
    --status-info-ink: #004D40;
}

/* Fundo da aplicação */
.stApp {
    background-color: #F8F9FA;
    color: #1A2B5E;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
}

/* Cabeçalho do App */
.univag-header-box {
    background: linear-gradient(135deg, #1A2B5E 0%, #0066CC 100%);
    color: #FFFFFF;
    padding: 24px 32px;
    border-radius: 12px;
    margin-bottom: 24px;
    box-shadow: 0 4px 12px rgba(26, 43, 94, 0.12);
}
.univag-header-title {
    font-size: 28px;
    font-weight: 700;
    margin: 0;
    color: #FFFFFF !important;
    letter-spacing: -0.5px;
}
.univag-header-sub {
    font-size: 15px;
    color: #E0E7FF;
    margin-top: 6px;
    margin-bottom: 12px;
}
.univag-badge {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    font-size: 12px;
    font-weight: 600;
    padding: 3px 12px;
    border-radius: 20px;
    background: rgba(255, 255, 255, 0.18);
    color: #FFFFFF;
    border: 1px solid rgba(255, 255, 255, 0.3);
    margin-right: 8px;
}

/* Cartões de Indicadores (KPIs) */
.univag-kpi-card {
    background: #FFFFFF;
    border: 1px solid #DEE2E6;
    border-radius: 10px;
    padding: 18px 20px;
    box-shadow: 0 2px 6px rgba(0, 0, 0, 0.04);
    transition: transform 0.2s, box-shadow 0.2s;
    height: 100%;
}
.univag-kpi-card:hover {
    box-shadow: 0 4px 12px rgba(26, 43, 94, 0.08);
}
.univag-kpi-label {
    font-size: 12px;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    color: #6C757D;
    margin-bottom: 4px;
}
.univag-kpi-value {
    font-size: 30px;
    font-weight: 700;
    color: #1A2B5E;
    line-height: 1.15;
    margin-bottom: 6px;
}
.univag-kpi-note {
    font-size: 12px;
    color: #6C757D;
}

/* Alertas e Notas Metodológicas */
.univag-callout {
    background: #FFFFFF;
    border-left: 4px solid #0066CC;
    border-radius: 6px;
    padding: 14px 18px;
    margin: 16px 0;
    border-top: 1px solid #DEE2E6;
    border-right: 1px solid #DEE2E6;
    border-bottom: 1px solid #DEE2E6;
}
.univag-callout-warn {
    border-left-color: #FFC107;
    background: #FFFDF5;
}
.univag-callout-good {
    border-left-color: #28A745;
    background: #F6FCF7;
}

/* Barra lateral */
[data-testid="stSidebar"] {
    background-color: #FFFFFF;
    border-right: 1px solid #DEE2E6;
}
[data-testid="stSidebar"] h1, [data-testid="stSidebar"] h2, [data-testid="stSidebar"] h3 {
    color: #1A2B5E;
}

/* Botões */
button[kind="primary"] {
    background-color: #0066CC !important;
    border-color: #0066CC !important;
    color: #FFFFFF !important;
    font-weight: 600;
    border-radius: 6px;
}
button[kind="primary"]:hover {
    background-color: #1A2B5E !important;
    border-color: #1A2B5E !important;
}

/* Tabelas */
.dataframe {
    border-radius: 8px !important;
    overflow: hidden !important;
}
</style>
"""


def apply_custom_styles():
    st.markdown(UNIVAG_CSS, unsafe_allow_html=True)
    css = Path(__file__).with_name("univag.css").read_text(encoding="utf-8")
    st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)
