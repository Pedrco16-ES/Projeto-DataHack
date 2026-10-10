"""Componentes de exportação segura de planilhas e dados públicos.

Aplica estritamente a regra do desafio de não divulgar células com menos de 10 alunos.
"""

import io
import pandas as pd
import streamlit as st


def sanitize_public_dataframe(df: pd.DataFrame, count_columns: list[str]) -> pd.DataFrame:
    """Aplica supressão de células com contagem menor que 10."""
    clean_df = df.copy()
    for col in count_columns:
        if col in clean_df.columns:
            # Substitui contagens menores que 10 por '< 10'
            mask = clean_df[col].apply(lambda x: pd.notnull(x) and isinstance(x, (int, float)) and 0 < x < 10)
            clean_df[col] = clean_df[col].astype(object)
            clean_df.loc[mask, col] = "< 10 (suprimido)"
    return clean_df


def render_export_buttons(df: pd.DataFrame, filename_base: str, count_columns: list[str] | None = None):
    """Renderiza botões para download em CSV e XLSX protegidos."""
    if count_columns:
        export_df = sanitize_public_dataframe(df, count_columns)
    else:
        export_df = df.copy()

    col1, col2 = st.columns(2)

    with col1:
        csv_bytes = export_df.to_csv(index=False, encoding="utf-8-sig").encode("utf-8-sig")
        st.download_button(
            label="📥 Baixar Tabela em CSV (UTF-8)",
            data=csv_bytes,
            file_name=f"{filename_base}.csv",
            mime="text/csv",
            use_container_width=True
        )

    with col2:
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine="openpyxl") as writer:
            export_df.to_excel(writer, index=False, sheet_name="Rota_do_Diploma")
        xlsx_bytes = output.getvalue()
        st.download_button(
            label="📊 Baixar Tabela em Excel (.xlsx)",
            data=xlsx_bytes,
            file_name=f"{filename_base}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )
