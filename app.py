"""Entrada pública local: navegação de oito telas, somente dados protegidos."""

import streamlit as st
from components.dashboard import render

st.set_page_config(page_title="Rota do Diploma · DataHack 2026", page_icon="🎓", layout="wide")
pages = [
    st.Page(lambda: render("home"), title="Panorama", icon=":material/dashboard:", default=True),
    st.Page("pages/1_Trajetoria.py", title="A trajetória", icon=":material/route:"),
    st.Page("pages/2_Cursos.py", title="Cursos e áreas", icon=":material/school:"),
    st.Page("pages/3_Redes.py", title="Redes e modalidades", icon=":material/stacked_line_chart:"),
    st.Page("pages/4_Qualidade.py", title="Qualidade", icon=":material/scatter_plot:"),
    st.Page("pages/5_Licenciaturas.py", title="Licenciaturas", icon=":material/local_library:"),
    st.Page("pages/6_Municipios.py", title="Oferta municipal", icon=":material/location_on:"),
    st.Page("pages/7_Financiamento.py", title="Financiamento", icon=":material/payments:"),
]
st.navigation(pages).run()