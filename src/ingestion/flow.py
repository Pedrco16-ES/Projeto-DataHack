"""Taxa oficial de evasão do sistema: reprodução estadual, não taxa por curso."""

from io import BytesIO
import json
import pandas as pd
from zipfile import ZipFile

from src.analytics.metrics import AnalyticsError
from src.ingestion.supplements import checked_source, DEST
from src.ingestion.pipeline import sha256


def read_flow(path):
    with ZipFile(path) as archive:
        with archive.open("INDIC_UF_2010_2024.xlsx") as stream:
            frame = pd.read_excel(BytesIO(stream.read()), sheet_name="TX_EVASAO", header=None)
    if str(frame.iloc[5, 0]).strip() != "Ano Fluxo" or str(frame.iloc[5, 2]).strip() != "Total":
        raise AnalyticsError("Cabeçalho da taxa oficial de fluxo foi alterado.")
    data = frame.iloc[8:].copy()
    # Apenas os rótulos de células mescladas; jamais preencher medidas ausentes.
    data[0] = data[0].ffill()
    result = data.loc[data[1].eq("Mato Grosso"), [0, 2]].copy()
    result.columns = ["periodo", "evasao_sistema_pct"]
    if not result.periodo.str.fullmatch(r"20\d{2}-20\d{2}").all() or result.periodo.duplicated().any():
        raise AnalyticsError("Períodos de fluxo inválidos ou duplicados.")
    result["ano_base"] = result.periodo.str[:4].astype(int)
    result["ano_destino"] = result.periodo.str[5:].astype(int)
    result["evasao_sistema_pct"] = pd.to_numeric(result.evasao_sistema_pct, errors="raise")
    if not result.evasao_sistema_pct.between(0, 100).all() or not (result.ano_destino - result.ano_base).eq(1).all():
        raise AnalyticsError("Escala/período de fluxo incompatível.")
    if set(result.ano_destino) != set(range(2011, 2025)):
        raise AnalyticsError("Série estadual de fluxo incompleta.")
    result["CO_UF"] = "51"
    result["recorte"] = "Total estadual publicado pelo INEP; sem rede/modalidade/curso"
    result["denominador_numerico_disponivel"] = False
    return result.reset_index(drop=True)


def main():
    source = checked_source("fluxo_uf_2010_2024.zip")
    frame = read_flow(source)
    DEST.mkdir(parents=True, exist_ok=True)
    output = DEST / "fluxo_evasao_sistema_mt_2010_2024.csv"
    frame.to_csv(output, index=False)
    report = {"fonte_sha256": sha256(source), "saida_sha256": sha256(output), "linhas": len(frame),
              "unidade": "percentual publicado; não reconstruído de matrículas",
              "recortes_ausentes": ["rede", "modalidade", "curso", "financiamento"],
              "status": "validated_private_not_public"}
    (DEST / "fluxo.report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print("Fluxo MT: 14 transições anuais validadas; desagregações de rede/modalidade/curso indisponíveis.")


if __name__ == "__main__":
    main()
