"""Regras de tratamento; nunca preenche ausentes com zero ou soma taxas."""

import pandas as pd

RATES = {"TAP", "TCA", "TDA", "TCAN", "TADA"}


def clean_strings(frame: pd.DataFrame) -> pd.DataFrame:
    result = frame.astype("string").copy()
    for name in result:
        result[name] = result[name].str.strip().replace({"": pd.NA, ".": pd.NA})
    return result


def validate_rows(frame: pd.DataFrame, contract: dict) -> tuple[pd.DataFrame, pd.Series]:
    result = frame.copy()
    errors = pd.Series("", index=result.index, dtype="string")

    def flag(mask, reason):
        nonlocal errors
        errors.loc[mask.fillna(False)] += reason + ";"

    for key in contract["key"]:
        flag(result[key].isna(), "chave_ausente:" + key)
    for name in result:
        if name.startswith("CO_") and "CINE" not in name:
            value = result[name]
            flag(value.notna() & ~value.str.fullmatch(r"[0-9]+"), "codigo_invalido:" + name)
        if name.startswith("QT_") or name.startswith("NU_") or name in RATES:
            text = result[name]
            if name in RATES:
                text = text.str.replace(",", ".", regex=False)
            numeric = pd.to_numeric(text, errors="coerce")
            flag(result[name].notna() & numeric.isna(), "numero_invalido:" + name)
            flag(numeric.notna() & ~numeric.between(0, 100 if name in RATES else 2**53 - 1), "fora_da_faixa:" + name)
            if name not in RATES:
                invalid_int = numeric.notna() & ((numeric % 1 != 0) | ~numeric.between(0, 2**53 - 1))
                flag(invalid_int, "inteiro_invalido:" + name)
                result[name] = numeric.mask(invalid_int).astype("Int64")
            else:
                result[name] = numeric.astype("Float64")
    flag(~result["CO_MUNICIPIO"].str.fullmatch(r"51[0-9]{5}"), "municipio_incompativel_MT")
    flag(result["CO_MUNICIPIO"].isna(), "municipio_ausente")
    flag(~result["TP_MODALIDADE_ENSINO"].isin(["1", "2"]), "modalidade_invalida")
    if "TP_CATEGORIA_ADMINISTRATIVA" in result:
        flag(~result["TP_CATEGORIA_ADMINISTRATIVA"].isin(["1", "2", "3", "4", "5", "7"]), "categoria_invalida")
    if contract["source"] == "censo_curso":
        flag(result["NU_ANO_CENSO"].ne(contract["edition"]) | result["NU_ANO_CENSO"].isna(), "ano_incompativel")
        flag(~result["TP_DIMENSAO"].isin(["1", "2"]), "dimensao_invalida_MT")
        flag(result["TP_DIMENSAO"].ne(result["TP_MODALIDADE_ENSINO"]), "dimensao_modalidade_incompativel")
    else:
        cohort, reference = result["NU_ANO_INGRESSO"], result["NU_ANO_REFERENCIA"]
        flag(cohort.isna() | reference.isna() | (cohort < 1900) | (reference < cohort) | (reference > contract["edition"]), "periodo_incompativel")
        # Apenas diferença calendárica; convenção de 'ano de acompanhamento' ainda não aprovada.
        result["ANOS_DESDE_INGRESSO"] = reference - cohort
    return result, errors.str.rstrip(";")


def quality_profile(frame: pd.DataFrame) -> dict:
    """Perfil do recorte MT completo. Outliers são sinalizados, nunca excluídos."""
    profile = {"missing": {c: int(frame[c].isna().sum()) for c in frame}, "numeric": {}}
    for name in frame:
        if name.startswith("QT_") or name in RATES:
            values = pd.to_numeric(frame[name], errors="coerce").dropna()
            if values.empty:
                continue
            q1, q3 = values.quantile([0.25, 0.75]); iqr = q3 - q1
            outliers = int(((values < q1 - 1.5 * iqr) | (values > q3 + 1.5 * iqr)).sum()) if len(values) >= 4 and iqr > 0 else None
            profile["numeric"][name] = {"min": float(values.min()), "max": float(values.max()), "iqr_outliers": outliers}
    return profile
