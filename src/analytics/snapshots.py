"""Snapshots aprovados localmente; conexão pública sem fallback privilegiado."""

import json
import os
from pathlib import Path

import pandas as pd
from sqlalchemy import text

from src.analytics.build import digest
from src.analytics.disclosure import small, STATES
from src.analytics.metrics import AnalyticsError
from src.config import load_settings
from src.database.connection import create_database_engine


def validate_envelope(envelope):
    if envelope.get("status") != "approved_local_mvp" or not envelope.get("approval_reason", "").strip():
        raise AnalyticsError("Snapshot sem aprovação local registrada.")
    payload = envelope.get("payload", {})
    if payload.get("schema_version") != 2 or envelope.get("sha256") != digest(payload):
        raise AnalyticsError("Snapshot alterado ou incompatível.")
    for name in ["p1", "courses"]:
        frame = pd.DataFrame(payload.get(name, []))
        if frame.empty or small(frame, STATES).any():
            raise AnalyticsError("Snapshot sem dados seguros de trajetória.")
    for key in ["timeline", "census", "quality", "offers", "sources", "limitations"]:
        if not isinstance(payload.get(key), list):
            raise AnalyticsError("Snapshot incompleto.")
    from src.ingestion.supplements import validate_geometry
    enade = pd.DataFrame(payload.get("enade", []))
    if enade.empty or small(enade, ["participantes", "proficientes", "nao_proficientes"]).any() or enade.participantes.lt(10).any() or "inscritos" in enade:
        raise AnalyticsError("Enade sem proteção válida.")
    if not (enade.proficientes + enade.nao_proficientes).eq(enade.participantes).all():
        raise AnalyticsError("Enade não reconciliado.")
    if enade[["proficientes", "nao_proficientes"]].lt(0).any().any() or (enade.proficiencia_pct - enade.proficientes / enade.participantes * 100).abs().gt(1e-7).any():
        raise AnalyticsError("Taxa Enade incompatível.")
    municipal = pd.DataFrame(payload.get("municipal", []))
    if len(municipal) != 141 or municipal.codigo_municipio.duplicated().any() or not municipal.ano.eq(2022).all():
        raise AnalyticsError("Cadastro municipal incompleto.")
    validate_geometry(payload.get("municipal_geometry", {}), municipal.codigo_municipio)
    expected = municipal.vagas / municipal.populacao_18_24.where(municipal.populacao_18_24.gt(0)) * 100
    if municipal.vagas.lt(0).any() or municipal.vagas_por_100_jovens.isna().ne(expected.isna()).any() or (municipal.vagas_por_100_jovens - expected).abs().gt(1e-7).any():
        raise AnalyticsError("Indicador municipal incompatível.")
    cohorts = pd.DataFrame(payload.get("cohorts", []))
    if len(cohorts) != 6 or set(cohorts.coorte) != set(range(2015, 2021)) or not (cohorts.ano - cohorts.coorte).eq(4).all():
        raise AnalyticsError("Comparação de coortes incompatível.")
    flow = pd.DataFrame(payload.get("annual_flow", []))
    if len(flow) != 4 or not flow.evasao_sistema_pct.between(0, 100).all():
        raise AnalyticsError("Fluxo estadual incompleto.")
    return payload


def write_snapshot(payload, path, reason):
    envelope = {"status": "approved_local_mvp", "approval_reason": reason,
                "sha256": digest(payload), "payload": payload}
    validate_envelope(envelope)
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    # Arquivo anterior preservado: reversão local sem recalcular dados.
    if path.exists():
        previous = path.with_suffix(".previous.json")
        previous.write_bytes(path.read_bytes())
    temporary = path.with_suffix(".tmp")
    temporary.write_text(json.dumps(envelope, ensure_ascii=False, indent=2, allow_nan=False), encoding="utf-8")
    os.replace(temporary, path)
    return envelope["sha256"]


def read_snapshot(path):
    try:
        return validate_envelope(json.loads(Path(path).read_text(encoding="utf-8")))
    except (OSError, ValueError, KeyError, TypeError):
        raise AnalyticsError("Snapshot ausente ou inválido. Gere os resultados pela CLI administrativa.") from None


def load_public_data(settings=None):
    settings = settings or load_settings()
    fallback_note = "Snapshot local validado · disponível offline"
    if settings.public_database_url:
        engine = None
        try:
            engine = create_database_engine(settings, public=True)
            with engine.connect() as conn:
                envelope = conn.execute(text("SELECT document FROM marts.public_snapshots WHERE active IS TRUE ORDER BY created_at DESC LIMIT 1")).scalar_one()
                return validate_envelope(envelope), "PostgreSQL · conexão pública somente leitura"
        except Exception:
            fallback_note = "Banco público indisponível · usando último snapshot local validado"
        finally:
            if engine is not None:
                engine.dispose()
    return read_snapshot(settings.outputs_dir / "public_snapshot.json"), fallback_note
