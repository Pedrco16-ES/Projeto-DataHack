"""Entrada pública local: navegação de oito telas, somente dados protegidos."""

import streamlit as st
from components.dashboard import render

st.set_page_config(page_title="Rota do Diploma · DataHack 2026", page_icon="🎓", layout="wide")
pages = [
    st.Page(lambda: render("home"), title="Panorama", icon=":material/dashboard:", default=True),
    st.Page("pages/1_Trajetoria.py", title="P1 · A trajetória", icon=":material/route:"),
    st.Page("pages/2_Cursos.py", title="P2 · Cursos e áreas", icon=":material/school:"),
    st.Page("pages/3_Redes.py", title="P3 · Redes e modalidades", icon=":material/stacked_line_chart:"),
    st.Page("pages/4_Qualidade.py", title="P4 · Qualidade", icon=":material/scatter_plot:"),
    st.Page("pages/5_Licenciaturas.py", title="P5 · Licenciaturas", icon=":material/local_library:"),
    st.Page("pages/6_Municipios.py", title="B1 · Oferta municipal", icon=":material/location_on:"),
    st.Page("pages/7_Financiamento.py", title="B2 · Financiamento", icon=":material/payments:"),
]
st.navigation(pages).run()