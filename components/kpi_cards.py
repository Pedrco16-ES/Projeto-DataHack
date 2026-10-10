"""Componente de cartões de indicadores (KPI cards) com estilos oficiais Univag."""

import streamlit as st


def render_kpi(label: str, value: str, note: str = "", delta: str | None = None, delta_color: str = "good"):
    color_map = {
        "good": ("#28A745", "#EAF6EC"),
        "warning": ("#FFC107", "#FFF8E1"),
        "critical": ("#DC3545", "#FFEBEE"),
        "info": ("#0066CC", "#E0F2FE"),
    }
    ink, bg = color_map.get(delta_color, ("#6C757D", "#E9ECEF"))

    delta_html = f"""
    <span style="display: inline-block; font-size: 11px; font-weight: 700; background: {bg}; color: {ink}; padding: 2px 8px; border-radius: 12px; margin-left: 6px;">
        {delta}
    </span>
    """ if delta else ""

    html = f"""
    <div class="univag-kpi-card">
        <div class="univag-kpi-label">{label}</div>
        <div class="univag-kpi-value">{value} {delta_html}</div>
        <div class="univag-kpi-note">{note}</div>
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)


def render_question_card(
    question_id: str,
    title: str,
    main_number: str,
    period: str,
    description: str,
    target_page: str,
    tag: str = "Obrigatória"
):
    tag_color = "#0066CC" if "Obrigatória" in tag else "#6F42C1"
    html = f"""
    <div style="background: #FFFFFF; border: 1px solid #DEE2E6; border-radius: 10px; padding: 20px; box-shadow: 0 2px 6px rgba(0,0,0,0.03); margin-bottom: 16px; border-top: 4px solid {tag_color};">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
            <span style="font-size: 13px; font-weight: 800; color: {tag_color}; background: #F0F4FF; padding: 3px 10px; border-radius: 4px;">
                {question_id} · {tag}
            </span>
            <span style="font-size: 12px; color: #6C757D; font-weight: 500;">
                📅 {period}
            </span>
        </div>
        <div style="font-size: 16px; font-weight: 700; color: #1A2B5E; margin-bottom: 6px;">
            {title}
        </div>
        <div style="font-size: 26px; font-weight: 800; color: #0066CC; margin-bottom: 8px;">
            {main_number}
        </div>
        <div style="font-size: 13px; color: #495057; line-height: 1.4; margin-bottom: 14px;">
            {description}
        </div>
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)
    if st.button(f"Explorar análise completa de {question_id} →", key=f"btn_nav_{question_id}", use_container_width=True):
        st.switch_page(target_page)
