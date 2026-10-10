"""Conferência privada de horizontes e chaves; não publica indicadores."""

import json
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pandas as pd
from src.analytics.metrics import trajectory, trajectory_summary
from src.ingestion.pipeline import sha256
from src.ingestion.supplements import DEST, RAW
from src.config import PROJECT_ROOT


def main():
    plan = json.loads((PROJECT_ROOT / "data/processed/stage4_plan.json").read_text(encoding="utf-8"))
    source_root = PROJECT_ROOT / "data/processed"
    def accepted(source, edition):
        item = next(x for x in plan["batches"] if x["source"] == source and x["edition"] == edition)
        path = source_root / item["batch_id"] / "accepted.csv"
        if sha256(path) != item["accepted_sha256"]:
            raise ValueError("Lote anterior alterado.")
        return pd.read_csv(path, dtype="string")
    first = trajectory(accepted("trajetoria", 2024))
    summary = []
    for year in range(2015, 2021):
        frame = first if year == 2015 else trajectory(pd.read_csv(DEST / f"trajetoria_mt_{year}_2024.csv", dtype="string"))
        selected = frame.loc[frame.horizonte.eq(4) & frame.modalidade.eq("Presencial")]
        result = trajectory_summary(selected, ["ano", "coorte"])
        result["horizonte"] = 4
        summary.append(result)
    pd.concat(summary, ignore_index=True).to_csv(DEST / "diagnostico_coortes_h4_privado.csv", index=False)
    population = pd.read_csv(DEST / "ibge_populacao_mt_2022.csv", dtype={"codigo_municipio": "string"})
    census = accepted("censo_curso", 2022)
    oncampus = census.loc[census.TP_MODALIDADE_ENSINO.eq("1") & census.TP_DIMENSAO.eq("1")]
    unknown = sorted(set(oncampus.CO_MUNICIPIO) - set(population.codigo_municipio))
    if unknown:
        raise ValueError("Municípios da oferta fora do cadastro 2022.")
    enade = pd.read_csv(DEST / "enade_licenciaturas_mt_2025.csv", dtype={"CO_IES": "string", "CO_CURSO": "string"})
    licensed = first.loc[first.ano.eq(2024) & first.grau.eq("Licenciatura")]
    primary = enade.loc[enade.modalidade.eq("Presencial")]
    joined = licensed.merge(primary[["CO_IES", "CO_CURSO", "status"]], how="left", on=["CO_IES", "CO_CURSO"], validate="one_to_one", indicator=True)
    report = {
        "comparacao_coortes": {"coortes": list(range(2015, 2021)), "horizonte_comum": 4,
                              "referencias": list(range(2019, 2025)), "modalidade": "Presencial"},
        "oferta_municipal": {"ano_populacao": 2022, "ano_censo": 2022, "cadastro_completo": len(population),
                             "municipios_com_registros_presenciais": int(oncampus.CO_MUNICIPIO.nunique()),
                             "municipios_fora_cadastro": unknown},
        "enade_trajetoria": {"cursos_licenciatura_trajetoria": len(licensed), "cursos_enade_presenciais_mt": len(primary),
                             "cursos_vinculados": int(joined._merge.eq("both").sum()),
                             "cursos_com_resultado_enade": int(joined.status.eq("calculavel").sum()),
                             "populacoes_distintas": True},
        "publicacao": "Bloqueada até integração/proteção no passo 3; arquivos administrativos.",
        "snapshot_atual_sha256": sha256(PROJECT_ROOT / "outputs/public_snapshot.json"),
    }
    (DEST / "scope_validation.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    (PROJECT_ROOT / "docs/fontes_complementares_manifest.json").write_text((RAW / "manifest.json").read_text(encoding="utf-8"), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=True, indent=2))


if __name__ == "__main__":
    main()
