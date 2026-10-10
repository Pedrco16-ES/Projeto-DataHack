"""Constrói o snapshot local rastreável a partir dos lotes reconciliados."""

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import unicodedata

import pandas as pd

from src.analytics.metrics import (AnalyticsError, trajectory, trajectory_summary,
                                   census, census_summary, join_quality, correlation)
from src.analytics.disclosure import public_courses, public_census, small, STATES
from src.config import PROJECT_ROOT
from src.ingestion.pipeline import sha256

SOURCE_TRAJECTORY = "INEP · Indicadores de Trajetória 2015–2024"
SOURCE_CENSUS = "INEP · Censo da Educação Superior 2021–2024"


def records(frame):
    return json.loads(frame.to_json(orient="records", force_ascii=False, double_precision=10))


def digest(payload):
    return hashlib.sha256(json.dumps(payload, sort_keys=True, ensure_ascii=False, allow_nan=False).encode("utf-8")).hexdigest()


def read_batches(plan_path):
    plan_path = Path(plan_path)
    plan = json.loads(plan_path.read_text(encoding="utf-8"))
    frames = {"trajetoria": [], "censo_curso": []}
    provenance = []
    seen = set()
    for batch in plan["batches"]:
        # Relocável: não depende do caminho absoluto da máquina original.
        directory = plan_path.parent / batch["batch_id"]
        if not directory.is_dir():
            directory = Path(batch["batch_dir"])
        if sha256(directory / "report.json") != batch["report_sha256"] or sha256(directory / "accepted.csv") != batch["accepted_sha256"]:
            raise AnalyticsError("Lote alterado após a reconciliação: construção bloqueada.")
        report = json.loads((directory / "report.json").read_text(encoding="utf-8"))
        scope = (batch["source"], batch["edition"])
        if scope in seen or scope[0] not in frames:
            raise AnalyticsError("Fonte duplicada ou não suportada no plano.")
        seen.add(scope)
        frame = pd.read_csv(directory / "accepted.csv", dtype="string")
        if len(frame) != batch["counts"]["accepted"]:
            raise AnalyticsError("Contagem do lote divergente.")
        frames[scope[0]].append(frame)
        provenance.append({"fonte": scope[0], "edicao": scope[1], "lote": batch["batch_id"],
                           "sha256": batch["accepted_sha256"], "registros": len(frame),
                           "recebidos": batch["counts"]["received"], "rejeitados": batch["counts"]["rejected"],
                           "arquivo_original_sha256": report["file_sha256"]})
    if not all(frames.values()):
        raise AnalyticsError("Plano precisa de Trajetória e Censo.")
    return {k: pd.concat(v, ignore_index=True) for k, v in frames.items()}, provenance


def normalize(value):
    return " ".join("".join(c for c in unicodedata.normalize("NFKD", str(value)) if not unicodedata.combining(c)).replace("*", "").strip().lower().split())


def read_cpc(path, edition):
    # Primeira aba oficial de resultados; abas de atualizações são metadados.
    frame = pd.read_excel(path, sheet_name=0, dtype="string")
    mapping = {"codigo da ies": "CO_IES", "codigo do curso": "CO_CURSO", "ano": "ano_cpc",
               "cpc (continuo)": "cpc", "cpc (faixa)": "faixa_cpc"}
    cols = {c: mapping[normalize(c)] for c in frame if normalize(c) in mapping}
    if len(cols) != len(mapping):
        raise AnalyticsError("Layout CPC incompatível: confira as colunas da edição.")
    out = frame[list(cols)].rename(columns=cols)
    for c in ["CO_IES", "CO_CURSO"]:
        out[c] = out[c].str.strip().str.replace(r"\.0$", "", regex=True)
        if out[c].isna().any() or not out[c].str.fullmatch(r"\d+").all():
            raise AnalyticsError("Código inválido no CPC.")
    out["ano_cpc"] = pd.to_numeric(out.ano_cpc, errors="raise").astype(int)
    if not out.ano_cpc.eq(edition).all():
        raise AnalyticsError("Arquivo CPC contém edição diferente da selecionada.")
    for c in ["cpc", "faixa_cpc"]:
        original = out[c].str.strip().str.replace(",", ".", regex=False)
        parsed = pd.to_numeric(original, errors="coerce")
        if (parsed.isna() & original.notna() & ~original.str.upper().isin(["SC", "-", "", "NAN"])).any():
            raise AnalyticsError("Valor CPC não reconhecido; mapeamento manual necessário.")
        out[c] = parsed
    if (~out.cpc.dropna().between(0, 5)).any() or (~out.faixa_cpc.dropna().isin([1, 2, 3, 4, 5])).any():
        raise AnalyticsError("CPC fora da escala oficial.")
    if out[["cpc", "faixa_cpc"]].isna().any(axis=1).ne(out[["cpc", "faixa_cpc"]].isna().all(axis=1)).any():
        raise AnalyticsError("CPC contínuo e faixa com ausência incompatível.")
    out["faixa_cpc"] = out.faixa_cpc.map(lambda x: str(int(x)) if pd.notna(x) else "Sem CPC")
    return out


def build(plan_path, data_dir, cpc_year=2023):
    frames, sources = read_batches(plan_path)
    traj = trajectory(frames["trajetoria"])
    censo = census(frames["censo_curso"])
    fixed = traj.loc[traj.coorte.eq(2015) & traj.modalidade.eq("Presencial")].copy()
    if fixed.empty or fixed.ano.max() != 2024:
        raise AnalyticsError("P1 exige coorte 2015 presencial até 2024.")
    if fixed.groupby("curso_id").size().ne(10).any():
        raise AnalyticsError("P1 exige painel completo 2015–2024.")
    summary = trajectory_summary(fixed, ["ano", "coorte"])
    final = fixed.loc[fixed.ano.eq(2024)].copy()
    courses = public_courses(final)
    p1 = summary.loc[summary.ano.eq(2024)].copy()
    if small(p1, STATES).any():
        raise AnalyticsError("Total P1 necessita proteção adicional; publicação bloqueada.")
    # Evolução pública apenas em taxas arredondadas, sem contagens/denominadores
    # intermediários que permitiriam reconstruir óbitos anuais menores que 10.
    timeline = summary[["ano", "coorte", "tda", "tca", "tap"]].copy()
    timeline[["tda", "tca", "tap"]] = timeline[["tda", "tca", "tap"]].round(1)
    raw_delta = summary.tda.diff()
    peak = int(summary.loc[raw_delta.idxmax(), "ano"])
    cpc_files = sorted(p for p in Path(data_dir).rglob("*.xlsx") if "cpc" in p.name.lower() and str(cpc_year) in p.name and not p.name.startswith("~$"))
    cpc_note = "CPC não localizado: análise de associação pendente."
    quality_records = []
    corr = None
    if len(cpc_files) > 1:
        raise AnalyticsError("Mais de um CPC candidato; selecione uma fonte inequívoca.")
    if cpc_files:
        q = read_cpc(cpc_files[0], cpc_year)
        joined = join_quality(courses, q, cpc_year)
        quality_records = records(joined)
        corr = correlation(joined)
        sources.append({"fonte": "CPC", "edicao": cpc_year, "arquivo": cpc_files[0].name,
                        "sha256": sha256(cpc_files[0]), "registros": len(q)})
        cpc_note = f"CPC {cpc_year}, edição única anterior à referência 2024. Abrange somente as áreas avaliadas nesse ciclo; Sem CPC inclui cursos não avaliados e sem conceito. A nota foi medida depois do ingresso em 2015: associação descritiva, não causalidade."
    cs = public_census(census_summary(censo))
    offers = censo.loc[censo.modalidade.eq("Presencial")].groupby(
        ["ano", "CO_MUNICIPIO", "NO_MUNICIPIO"], dropna=False).QT_VG_TOTAL.sum(min_count=1).reset_index()
    offers = offers.rename(columns={"CO_MUNICIPIO": "codigo_municipio", "NO_MUNICIPIO": "municipio", "QT_VG_TOTAL": "vagas"})
    from src.analytics.extensions import build_extensions
    extensions, extra_sources = build_extensions(traj, censo)
    sources.extend(extra_sources)
    code_files = sorted((PROJECT_ROOT / "src/analytics").glob("*.py"))
    payload = {
        "schema_version": 2,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "scope": "MVP local · dados oficiais · validação técnica automática",
        "source_trajectory": SOURCE_TRAJECTORY,
        "source_census": SOURCE_CENSUS,
        "sources": sources,
        "code_sha256": digest({p.name: sha256(p) for p in code_files}),
        "p1": records(p1), "timeline": records(timeline), "courses": records(courses),
        "census": records(cs), "quality": quality_records, "offers": records(offers),
        "peak_year": peak, "peak_delta_pp": round(float(raw_delta.max()), 1),
        "cpc_year": cpc_year, "correlation": corr, "cpc_note": cpc_note,
        "coverage": {"cursos_trajetoria": len(final), "cursos_publicaveis": len(courses),
                     "cursos_omitidos": len(final) - len(courses)},
        "limitations": [
            "P1 descreve todos os cursos presenciais de MT da coorte 2015 presentes no lote validado. Localização e atributos são os do último ano da fonte.",
            "P2, P4 e trajetória de P5 usam apenas o mesmo subconjunto de cursos publicáveis. Seus totais não representam todo o estado.",
            "Cursos com estado positivo menor que 10 são omitidos integralmente; proteção complementar verifica também o resíduo contra P1. Nenhum total completo por área, rede, CPC ou grau é divulgado.",
            "A evolução P1 usa taxas arredondadas a 0,1 ponto percentual; não divulga óbitos ou denominadores anuais. Diferenças acumuladas não são risco anual de evasão.",
            "Comparação estadual entre coortes 2015–2020 no horizonte de quatro anos desde o ingresso (cinco observações). Taxas arredondadas a 0,1 p.p.; composição de cursos pode mudar entre coortes.",
            "Censo agregado por ano, rede e modalidade, nas dimensões municipais 1 e 2. Registros sem localização válida não são atribuídos a MT.",
            "Evasão anual do sistema reproduz o percentual oficial estadual do INEP, sem desagregação por rede, modalidade ou curso. Não é TDA acumulada nem desvinculados divididos por matrículas. Variações são descritivas.",
            "FIES, ProUni integral e parcial usam matrículas como denominador e são apresentados separadamente, sem soma de benefícios ou inferência individual.",
            "Enade 2025: cursos presenciais de MT com participantes, proficientes e complemento publicáveis. Taxa ponderada por participantes; inscritos e totais da população omitida não são divulgados. População diferente da trajetória 2015–2024.",
            "B1 combina vagas presenciais registradas no Censo Superior 2022 com população IBGE 18–24 e malha de 2022 (141 municípios). Zero significa nenhuma vaga registrada no recorte validado; não prova ausência de acesso. Vagas não são exclusivas dessa faixa etária.",
            "A associação financiamento–evasão por curso permanece indisponível: a taxa anual obtida é estadual, sem recorte compatível de financiamento.",
        ],
    }
    payload.update(extensions)
    return payload
