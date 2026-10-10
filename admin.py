"""Interface administrativa local, separada do futuro dashboard público."""

import json
from pathlib import Path
import tempfile

import pandas as pd
import streamlit as st

from src.config import load_settings
from src.export.administrative import csv_bytes, xlsx_bytes
from src.ingestion.pipeline import process_file
from src.ingestion.readers import preview
from src.ingestion.schema import IngestionError, load_contract, validate_mapping

st.set_page_config(page_title="Rota do Diploma — Importação local", page_icon="🎓", layout="wide")
st.title("Rota do Diploma · Preparação dos dados")
st.caption("Administração local · Etapa 3 · Trajetória e Censo de cursos")
st.warning("Esta tela contém dados administrativos sem supressão. Execute somente em localhost. Não é o dashboard público.")
settings = load_settings()
source = st.selectbox("Fonte", ["trajetoria", "censo_curso"])
edition = st.selectbox("Edição do arquivo", [2024] if source == "trajetoria" else [2021, 2022, 2023, 2024])
st.caption("Na Trajetória, edição 2024 pode conter vários anos de referência. O processamento preserva esses anos.")
mode = st.radio("Origem do arquivo", ["Disco local", "Upload"], horizontal=True)
selected_path = None
upload = None
if mode == "Disco local":
    files = sorted(p for p in settings.data_dir.rglob("*") if p.is_file() and p.suffix.lower() in {".csv", ".xlsx", ".zip", ".json"} and not p.name.startswith("~$")) if settings.data_dir.exists() else []
    selected_path = st.selectbox("Arquivo em DATA_DIR", files, format_func=lambda p: str(p.relative_to(settings.data_dir))) if files else None
    if not files:
        st.info("Nenhum arquivo encontrado. Confira DATA_DIR na configuração local.")
else:
    upload = st.file_uploader("Arquivo oficial", type=["csv", "xlsx", "zip", "json"])
    st.caption("Para arquivos grandes, use Disco local ou o comando Python; uploads consomem memória.")
with st.expander("Aba, ZIP e mapeamento manual"):
    sheet = st.text_input("Nome da aba (obrigatório se houver mais de uma)") or None
    member = st.text_input("Membro do ZIP (obrigatório se houver mais de um arquivo)") or None
    mapping_text = st.text_area("Mapeamento JSON de coluna original para coluna do contrato", value="{}")
    mapping_reason = st.text_input("Justificativa do mapeamento")
    confirmed = st.checkbox("Confirmo o significado das colunas mapeadas e autorizo registrar esta decisão")

action = st.radio("Ação", ["Visualizar amostra", "Processar recorte MT"])
st.caption("Processar gera um lote local com aceitos, rejeitados, exclusões e relatório. Não importa dados no Supabase.")
file_identity = None
if selected_path is not None:
    stat = selected_path.stat()
    file_identity = [str(selected_path), stat.st_size, stat.st_mtime_ns]
elif upload is not None:
    import hashlib
    file_identity = [upload.name, hashlib.sha256(upload.getbuffer()).hexdigest()]
selection = json.dumps([file_identity, source, edition, sheet, member, mapping_text, mapping_reason, confirmed])
if st.session_state.get("selection") != selection:
    st.session_state["selection"] = selection
    st.session_state["reviewed"] = False
acknowledged = st.checkbox("Revisei a amostra e confirmo fonte e edição", key="reviewed")
if st.button("Executar", type="primary"):
    try:
        mapping = validate_mapping(json.loads(mapping_text), confirmed, mapping_reason)
        if selected_path is None and upload is None:
            raise IngestionError("Selecione um arquivo.")
        if action == "Processar recorte MT" and (not acknowledged or st.session_state.get("preview_selection") != selection):
            raise IngestionError("Visualize a amostra e confirme fonte e edição antes de processar.")
        with tempfile.TemporaryDirectory(prefix="rota_upload_") as temp:
            path = selected_path
            if upload is not None:
                path = Path(temp) / Path(upload.name).name
                path.write_bytes(upload.getbuffer())
            if action == "Visualizar amostra":
                frame, layout = preview(path, load_contract(source, edition), mapping=mapping, member=member, sheet=sheet)
                st.session_state["preview_selection"] = selection
                st.session_state["preview_frame"] = frame
                st.session_state["preview_layout"] = layout
            else:
                with st.spinner("Lendo, validando e preparando lote local…"):
                    result = process_file(path, source, edition, mapping=mapping, confirm_mapping=confirmed,
                                          mapping_reason=mapping_reason, member=member, sheet=sheet)
                st.session_state["batch_result"] = result
    except IngestionError as error:
        st.error(str(error))
    except Exception:
        st.error("Não foi possível ler/processar o arquivo. Confira formato e permissões; conteúdo não exibido.")

if st.session_state.get("preview_selection") == selection:
    st.subheader("Amostra do arquivo selecionado")
    st.write("Leitura detectada", st.session_state["preview_layout"])
    st.dataframe(st.session_state["preview_frame"], hide_index=True)

if result := st.session_state.get("batch_result"):
    st.subheader("Último lote tratado — ainda não aprovado")
    st.code(result["batch_id"])
    st.json(result["counts"])
    st.caption("Reutilizado após verificação dos hashes." if result["reused"] else "Novo lote concluído.")
    st.info("Próxima etapa: revisar rejeições e qualidade antes de definir a carga PostgreSQL.")
    with st.expander("Relatório de qualidade e rastreabilidade"):
        st.json({k: v for k, v in result.items() if k != "batch_dir"})
    artifact = st.selectbox("Tabela administrativa", ["accepted.csv", "rejected.csv", "excluded.csv"])
    table = pd.read_csv(Path(result["batch_dir"]) / artifact, dtype="string", keep_default_na=False)
    st.dataframe(table.head(100), hide_index=True)
    st.caption(f"Prévia de até 100 registros; arquivo completo com {len(table):,} linhas. Uso local, sem aprovação pública.")
    st.download_button("CSV administrativo", csv_bytes(table), file_name=artifact, mime="text/csv")
    st.download_button("XLSX administrativo", xlsx_bytes(table), file_name=Path(artifact).stem + ".xlsx",
                       mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    st.download_button("Relatório JSON", json.dumps(result, ensure_ascii=False, indent=2).encode("utf-8"),
                       file_name="report.json", mime="application/json")
