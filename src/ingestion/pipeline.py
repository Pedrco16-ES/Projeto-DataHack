"""Lotes locais rastreáveis. Nenhuma conexão ou escrita PostgreSQL nesta etapa."""

from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import tempfile

import pandas as pd

from src.config import PROJECT_ROOT
from src.ingestion.readers import materialize, detect_layout, read_chunks
from src.ingestion.schema import IngestionError, load_contract, validate_mapping
from src.processing.validation import clean_strings, validate_rows, quality_profile

PIPELINE_VERSION = "3.0.0"
UF_CODES = {"11", "12", "13", "14", "15", "16", "17", "21", "22", "23", "24", "25", "26", "27", "28", "29", "31", "32", "33", "35", "41", "42", "43", "50", "51", "52", "53"}


def sha256(path: Path) -> str:
    with Path(path).open("rb") as file:
        return hashlib.file_digest(file, "sha256").hexdigest()


def pipeline_digest() -> str:
    paths = [Path(__file__), Path(__file__).with_name("readers.py"), Path(__file__).with_name("schema.py"),
             PROJECT_ROOT / "src/processing/validation.py"]
    return hashlib.sha256("".join(sha256(p) for p in paths).encode()).hexdigest()


def verify_existing(batch: Path) -> dict:
    try:
        report = json.loads((batch / "report.json").read_text(encoding="utf-8"))
        if report["status"] != "treated_not_approved":
            raise ValueError
        for name in ("accepted.csv", "rejected.csv", "excluded.csv"):
            if sha256(batch / name) != report["artifacts"][name]:
                raise ValueError
    except (OSError, ValueError, KeyError):
        raise IngestionError("Lote existente incompleto ou alterado. Preserve-o para revisão; não será sobrescrito.") from None
    return {**report, "reused": True, "batch_dir": str(batch)}


def process_file(path: Path, source: str, edition: int, *, output_root: Path | None = None,
                 chunksize: int = 25000, mapping=None, confirm_mapping=False, mapping_reason="",
                 member=None, sheet=None, encoding=None, separator=None) -> dict:
    path = Path(path).resolve()
    contract = load_contract(source, edition)
    mapping = validate_mapping(mapping, confirm_mapping, mapping_reason)
    if set(mapping.values()) - set(contract["columns"]):
        raise IngestionError("Destino de mapeamento não existe no contrato.")
    if not path.is_file():
        raise IngestionError("Arquivo não encontrado.")
    original_hash = sha256(path)
    decision = {"source": source, "edition": edition, "file_sha256": original_hash,
                "contract_sha256": contract["contract_sha256"], "pipeline_sha256": pipeline_digest(),
                "mapping": mapping, "mapping_reason": mapping_reason if mapping else "",
                "member": member, "sheet": sheet, "encoding": encoding, "separator": separator}
    batch_id = hashlib.sha256(json.dumps(decision, sort_keys=True).encode()).hexdigest()[:24]
    root = Path(output_root or PROJECT_ROOT / "data/processed").resolve()
    # Destinos administrativos não podem ficar na pasta de snapshots públicos ou na origem.
    if root == PROJECT_ROOT / "outputs" or (PROJECT_ROOT / "outputs") in root.parents:
        raise IngestionError("Lotes administrativos não podem ser gravados em outputs.")
    if root == path.parent or root in path.parents:
        raise IngestionError("Use uma pasta de tratamento separada da origem.")
    root.mkdir(parents=True, exist_ok=True)
    batch = root / batch_id
    if batch.exists():
        return verify_existing(batch)
    with tempfile.TemporaryDirectory(prefix=".pending-", dir=root) as temp:
        work = Path(temp)
        counts = Counter(received=0, accepted=0, rejected=0, excluded=0, mt_candidates=0, duplicate_rows=0)
        excluded_reasons = Counter()
        raw_missing = Counter()
        key_counts = Counter()
        with materialize(path, member) as (actual, selected_member):
            layout = detect_layout(actual, contract, mapping, sheet, encoding, separator)
            original_columns = layout.columns + ["_record_number"]
            candidate_columns = original_columns + (["ANOS_DESDE_INGRESSO"] if source == "trajetoria" else [])
            pd.DataFrame(columns=candidate_columns).to_csv(work / "candidates.csv", index=False)
            pd.DataFrame(columns=original_columns + ["_reasons"]).to_csv(work / "rejected.csv", index=False)
            pd.DataFrame(columns=["_record_number", "_reason"]).to_csv(work / "excluded.csv", index=False)
            for chunk in read_chunks(actual, layout, chunksize):
                raw = chunk.reset_index(drop=True)
                geo_columns = [contract["geography"]] + (["TP_DIMENSAO"] if "TP_DIMENSAO" in raw else [])
                clean = clean_strings(raw[geo_columns])
                row_ids = range(counts["received"] + 1, counts["received"] + len(raw) + 1)
                clean["_record_number"] = list(row_ids)
                raw["_record_number"] = clean["_record_number"]
                counts["received"] += len(raw)
                uf = clean[contract["geography"]]
                mt = uf.eq("51").fillna(False)
                other = uf.isin(UF_CODES - {"51"})
                nonlocalizable = ~uf.isin(UF_CODES) & clean.get("TP_DIMENSAO", pd.Series("", index=clean.index)).isin(["3", "4"])
                outside = other | nonlocalizable
                bad_geo = ~(mt | outside)
                for mask, reason in [(other, "fora_de_MT"), (nonlocalizable, "sem_alocacao_geografica")]:
                    excluded = pd.DataFrame({"_record_number": clean.loc[mask, "_record_number"], "_reason": reason})
                    excluded.to_csv(work / "excluded.csv", mode="a", header=False, index=False)
                    excluded_reasons[reason] += int(mask.sum())
                counts["excluded"] += int(outside.sum())
                if bad_geo.any():
                    rejected = raw.loc[bad_geo].copy(); rejected["_reasons"] = "UF_ausente_ou_invalida"
                    rejected.to_csv(work / "rejected.csv", mode="a", header=False, index=False)
                    counts["rejected"] += len(rejected)
                scope = clean_strings(raw.loc[mt])
                counts["mt_candidates"] += len(scope)
                raw_missing.update({c: int(scope[c].isna().sum()) for c in scope})
                if scope.empty:
                    continue
                treated, reasons = validate_rows(scope, contract)
                key_counts.update(treated[contract["key"]].dropna().astype("string").itertuples(index=False, name=None))
                invalid = reasons.ne("")
                if invalid.any():
                    rejected = raw.loc[reasons.index[invalid]].copy()
                    rejected["_reasons"] = reasons[invalid]
                    rejected.to_csv(work / "rejected.csv", mode="a", header=False, index=False)
                    counts["rejected"] += len(rejected)
                treated.loc[~invalid, candidate_columns].to_csv(work / "candidates.csv", mode="a", header=False, index=False)
        # Somente o recorte MT é materializado; o arquivo nacional passa em blocos.
        candidates = pd.read_csv(work / "candidates.csv", dtype="string", keep_default_na=False)
        duplicates = pd.Series([key_counts[key] > 1 for key in candidates[contract["key"]].itertuples(index=False, name=None)], index=candidates.index, dtype=bool)
        counts["duplicate_rows"] = sum(count for count in key_counts.values() if count > 1)
        if duplicates.any():
            rejected = candidates.loc[duplicates, original_columns].copy()
            rejected["_reasons"] = "chave_duplicada_no_lote"
            rejected.to_csv(work / "rejected.csv", mode="a", header=False, index=False)
            counts["rejected"] += len(rejected)
        accepted = candidates.loc[~duplicates].copy()
        accepted.to_csv(work / "accepted.csv", index=False, encoding="utf-8")
        counts["accepted"] = len(accepted)
        if counts["received"] != counts["accepted"] + counts["rejected"] + counts["excluded"]:
            raise IngestionError("Falha na reconciliação das contagens. Lote não concluído.")
        if sha256(path) != original_hash:
            raise IngestionError("Arquivo original mudou durante o processamento. Lote não concluído.")
        report = {
            **decision, "batch_id": batch_id, "pipeline_version": PIPELINE_VERSION,
            "filename": path.name, "created_at": datetime.now(timezone.utc).isoformat(),
            "status": "treated_not_approved", "database_rows_imported": 0,
            "layout": {**layout.to_dict(), "member": selected_member}, "key": contract["key"],
            "counts": dict(counts), "excluded_reasons": dict(excluded_reasons),
            "missing_before_validation_mt": dict(raw_missing),
            "missing_optional_columns": sorted(set(contract["columns"]) - set(layout.columns)),
            "quality": quality_profile(clean_strings(accepted)),
            "warnings": ["Lote administrativo: não aprovado para publicação ou métricas.",
                         "Ausentes preservados; IQR apenas sinaliza valores para revisão, não exclui registros.",
                         "Validação numérica detalhada restrita ao recorte MT; linhas de outras UFs foram apenas contabilizadas.",
                         "Regras de soma de taxas, falecimentos e compatibilidade entre contagens anuais/acumuladas pendentes.",
                         "Supressão de células pequenas ainda não implementada: não distribuir estes arquivos."],
            "artifacts": {name: sha256(work / name) for name in ["accepted.csv", "rejected.csv", "excluded.csv"]},
        }
        (work / "report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        # Move apenas os artefatos criados nesta execução; publica o diretório de uma vez.
        completed = work / "complete"
        completed.mkdir()
        for name in ["accepted.csv", "rejected.csv", "excluded.csv", "report.json"]:
            (work / name).rename(completed / name)
        try:
            completed.rename(batch)
        except FileExistsError:
            return verify_existing(batch)
        return {**report, "reused": False, "batch_dir": str(batch)}
