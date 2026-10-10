"""Novos indicadores com períodos compatíveis e proteção antes dos filtros."""
import json
import pandas as pd

from src.analytics.metrics import AnalyticsError, trajectory, trajectory_summary
from src.analytics.disclosure import small
from src.ingestion.pipeline import sha256


def build_extensions(traj, censo):
    from src.analytics.build import records
    from src.ingestion.supplements import (DEST, RAW, checked_source, population_from_json,
                                          validate_geometry, enade_from_frame)
    from src.ingestion.flow import read_flow

    cohorts = [traj.loc[traj.horizonte.eq(4) & traj.modalidade.eq("Presencial")]]
    used = []
    for year in range(2016, 2021):
        name = f"trajetoria_{year}_2024.zip"
        source = checked_source(name)
        path = DEST / f"trajetoria_mt_{year}_2024.csv"
        report = json.loads(path.with_suffix(".report.json").read_text(encoding="utf-8"))
        if report["source_sha256"] != sha256(source) or report["output_sha256"] != sha256(path):
            raise AnalyticsError("Coorte processada divergente da fonte validada.")
        frame = trajectory(pd.read_csv(path, dtype="string"))
        if not frame.coorte.eq(year).all():
            raise AnalyticsError("Coorte incompatível com a edição.")
        cohorts.append(frame.loc[frame.horizonte.eq(4) & frame.modalidade.eq("Presencial")])
        used.append(name)
    comparison = trajectory_summary(pd.concat(cohorts), ["ano", "coorte"])
    comparison = comparison[["ano", "coorte", "cursos", "tda", "tca", "tap"]].copy()
    comparison[["tda", "tca", "tap"]] = comparison[["tda", "tca", "tap"]].round(1)
    comparison["horizonte"] = 4

    enade_name = "enade_licenciaturas_2025.xlsx"
    enade, _ = enade_from_frame(pd.read_excel(checked_source(enade_name),
                               sheet_name="Conceito Enade Licenciaturas", dtype="string"))
    enade = enade.loc[enade.modalidade.eq("Presencial")].copy()
    coverage = {"cursos_presenciais": len(enade)}
    enade["nao_proficientes"] = enade.participantes - enade.proficientes
    safe = ~small(enade, ["participantes", "proficientes", "nao_proficientes"]) & enade.participantes.ge(10)
    enade = enade.loc[safe, ["ano", "CO_IES", "CO_CURSO", "area", "instituicao", "categoria",
                           "modalidade", "municipio", "participantes", "proficientes",
                           "nao_proficientes", "proficiencia_pct", "conceito"]].copy()
    coverage["cursos_publicaveis"] = len(enade)
    coverage["cursos_omitidos"] = coverage["cursos_presenciais"] - len(enade)

    population_name = "ibge_18_24_municipios_mt_2022.json"
    geometry_name = "ibge_malha_mt_2022.geojson"
    _, population = population_from_json(json.loads(checked_source(population_name).read_text(encoding="utf-8")))
    geometry = json.loads(checked_source(geometry_name).read_text(encoding="utf-8"))
    validate_geometry(geometry, population.codigo_municipio)
    offers = censo.loc[censo.ano.eq(2022) & censo.modalidade.eq("Presencial")].groupby("CO_MUNICIPIO").QT_VG_TOTAL.sum(min_count=1)
    if not set(offers.index).issubset(set(population.codigo_municipio)) or len(population) != 141:
        raise AnalyticsError("Cadastro municipal e oferta incompatíveis em 2022.")
    municipal = population.copy()
    municipal["oferta_registrada"] = municipal.codigo_municipio.isin(offers.index)
    municipal["vagas"] = municipal.codigo_municipio.map(offers)
    municipal.loc[~municipal.oferta_registrada, "vagas"] = 0
    municipal["vagas_por_100_jovens"] = municipal.vagas / municipal.populacao_18_24.where(municipal.populacao_18_24.gt(0)) * 100
    municipal["situacao"] = municipal.oferta_registrada.map({True: "Com oferta registrada", False: "Sem oferta presencial registrada"})
    municipal.loc[municipal.vagas_por_100_jovens.isna(), "situacao"] = "Indicador indisponível"
    flow_name = "fluxo_uf_2010_2024.zip"
    flow = read_flow(checked_source(flow_name)).query("ano_destino >= 2021")
    used += [enade_name, population_name, geometry_name, flow_name]
    manifest = json.loads((RAW / "manifest.json").read_text(encoding="utf-8"))["files"]
    sources = [{"fonte": name, "sha256": manifest[name]["sha256"], "url": manifest[name]["url"]} for name in used]
    return {"cohorts": records(comparison), "enade": records(enade), "enade_coverage": coverage,
            "municipal": records(municipal), "municipal_geometry": geometry,
            "annual_flow": records(flow)}, sources
