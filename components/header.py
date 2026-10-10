"""Componente de cabeçalho executivo para as páginas do dashboard Rota do Diploma."""

import streamlit as st
from src.analytics.loader import get_data_source_status


def render_header(title: str, subtitle: str, question_id: str | None = None):
    status = get_data_source_status()
    badge_status = f"🟢 {status['label']}" if status["is_live"] else f"📦 {status['label']}"

    badge_html = f"""
    <div style="margin-top: 10px; display: flex; flex-wrap: wrap; gap: 8px;">
        <span class="univag-badge">{badge_status}</span>
        <span class="univag-badge">📍 Recorte: Mato Grosso (MT)</span>
        <span class="univag-badge">📅 Atualização: 10/10/2026</span>
    </div>
    """

    prefix = f"<span style='background: #00AEF0; color: #1A2B5E; padding: 2px 8px; border-radius: 4px; font-size: 16px; margin-right: 8px; font-weight: 800;'>{question_id}</span> " if question_id else ""

    html = f"""
    <div class="univag-header-box">
        <div style="display: flex; justify-content: space-between; align-items: flex-start;">
            <div>
                <div style="font-size: 13px; font-weight: 600; text-transform: uppercase; letter-spacing: 1px; color: #00AEF0; margin-bottom: 4px;">
                    DataHack Univag 2026 · Rota do Diploma
                </div>
                <h1 class="univag-header-title">{prefix}{title}</h1>
                <div class="univag-header-sub">{subtitle}</div>
                {badge_html}
            </div>
            <div style="background: rgba(255,255,255,0.12); padding: 10px 16px; border-radius: 8px; border: 1px solid rgba(255,255,255,0.25); text-align: right; min-width: 140px;">
                <div style="font-size: 11px; text-transform: uppercase; color: #E0E7FF; font-weight: 600;">Status do Pipeline</div>
                <div style="font-size: 14px; font-weight: 700; color: #FFFFFF; margin-top: 2px;">Etapas 1 a 8</div>
                <div style="font-size: 11px; color: #A5F3FC;">Versão 1.0 Oficial</div>
            </div>
        </div>
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)
