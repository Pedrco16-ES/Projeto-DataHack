"""Módulo de carregamento e provimento de dados para o dashboard Rota do Diploma.

Suporta leitura transacional do Supabase (quando DATABASE_URL estiver configurada)
e modo offline com fallback para os snapshots públicos aprovados em outputs/.
"""

from pathlib import Path
import json
import pandas as pd
import streamlit as st

from src.config import load_settings

PROJECT_ROOT = Path(__file__).resolve().parents[2]
OUTPUTS_DIR = PROJECT_ROOT / "outputs"


@st.cache_data(ttl=3600)
def get_data_source_status() -> dict:
    """Verifica disponibilidade da conexão PostgreSQL ou ativação do modo offline snapshot."""
    settings = load_settings()
    if settings.database_url:
        try:
            from src.database.connection import get_connection
            with get_connection(settings, public=False) as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT count(*) FROM meta.importacoes WHERE status='loaded'")
                    count = cur.fetchone()[0]
                    return {
                        "mode": "online",
                        "label": "Supabase PostgreSQL (Online)",
                        "detail": f"{count} lotes ativos",
                        "is_live": True
                    }
        except Exception:
            pass

    return {
        "mode": "snapshot",
        "label": "Snapshot Local Aprovado (Offline)",
        "detail": "Bases locais verificadas em outputs/",
        "is_live": False
    }


def _read_table(name: str) -> pd.DataFrame:
    parquet_path = OUTPUTS_DIR / f"{name}.parquet"
    csv_path = OUTPUTS_DIR / f"{name}.csv"
    if parquet_path.exists():
        return pd.read_parquet(parquet_path)
    elif csv_path.exists():
        return pd.read_csv(csv_path)
    else:
        raise FileNotFoundError(f"Arquivo analítico '{name}' não encontrado em outputs/.")


@st.cache_data(ttl=3600)
def load_p1_data() -> pd.DataFrame:
    return _read_table("p1_trajetoria_coorte2015")


@st.cache_data(ttl=3600)
def load_p2_data() -> pd.DataFrame:
    return _read_table("p2_cursos_areas")


@st.cache_data(ttl=3600)
def load_p3_data() -> pd.DataFrame:
    return _read_table("p3_censo_rede_modalidade")


@st.cache_data(ttl=3600)
def load_p4_data() -> pd.DataFrame:
    return _read_table("p4_qualidade_cpc")


@st.cache_data(ttl=3600)
def load_p5_data() -> pd.DataFrame:
    return _read_table("p5_licenciaturas")


@st.cache_data(ttl=3600)
def load_b1_data() -> pd.DataFrame:
    return _read_table("b1_oferta_municipal")


@st.cache_data(ttl=3600)
def load_b2_data() -> pd.DataFrame:
    return _read_table("b2_financiamento")


@st.cache_data(ttl=3600)
def load_metadata() -> dict:
    meta_path = OUTPUTS_DIR / "metadata.json"
    if meta_path.exists():
        with open(meta_path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}
