"""Métricas administrativas verificadas; publicação passa por disclosure.py."""

import numpy as np
import pandas as pd


class AnalyticsError(ValueError):
    pass


COURSE_KEY = ["CO_IES", "CO_CURSO", "NU_ANO_INGRESSO"]


def require(frame, columns):
    missing = sorted(set(columns) - set(frame))
    if missing:
        raise AnalyticsError("Colunas necessárias ausentes: " + ", ".join(missing))


def numeric(frame, columns):
    result = frame.copy()
    require(result, columns)
    for col in columns:
        result[col] = pd.to_numeric(result[col], errors="coerce")
        if result[col].isna().any() or not np.isfinite(result[col]).all() or (result[col] < 0).any():
            raise AnalyticsError(f"Valores ausentes, negativos ou inválidos em {col}.")
    return result


def rate(numerator, denominator):
    return numerator.div(denominator.where(denominator.gt(0))).mul(100)


def trajectory(frame):
    """Acumula contagens ANUAIS antes de filtrar anos; confere taxas oficiais."""
    counts = ["QT_INGRESSANTE", "QT_PERMANENCIA", "QT_CONCLUINTE", "QT_DESISTENCIA", "QT_FALECIDO"]
    x = numeric(frame, counts + ["NU_ANO_INGRESSO", "NU_ANO_REFERENCIA", "TDA", "TCA", "TAP"])
    require(x, COURSE_KEY + ["CO_UF", "TP_MODALIDADE_ENSINO", "TP_GRAU_ACADEMICO",
                            "TP_CATEGORIA_ADMINISTRATIVA", "NO_CURSO", "NO_IES", "NO_CINE_AREA_GERAL"])
    if not x.CO_UF.astype(str).eq("51").all():
        raise AnalyticsError("Trajetória deve conter exclusivamente MT.")
    if x[COURSE_KEY].isna().any().any() or x.duplicated(COURSE_KEY + ["NU_ANO_REFERENCIA"]).any():
        raise AnalyticsError("Chaves de trajetória inválidas ou repetidas.")
    if (x[counts + ["NU_ANO_INGRESSO", "NU_ANO_REFERENCIA"]] % 1 != 0).any().any():
        raise AnalyticsError("Contagens e anos devem ser inteiros.")
    x = x.sort_values(COURSE_KEY + ["NU_ANO_REFERENCIA"]).copy()
    groups = x.groupby(COURSE_KEY, dropna=False)
    expected = x.NU_ANO_INGRESSO + groups.cumcount()
    if not expected.eq(x.NU_ANO_REFERENCIA).all() or groups.QT_INGRESSANTE.nunique().gt(1).any():
        raise AnalyticsError("Série incompleta ou ingressantes inconsistentes: acumulação bloqueada.")
    for source, target in [("QT_DESISTENCIA", "desistentes"), ("QT_CONCLUINTE", "concluintes"),
                           ("QT_FALECIDO", "falecidos")]:
        x[target] = groups[source].cumsum()
    x["permanentes"] = x.QT_PERMANENCIA
    x["denominador"] = x.QT_INGRESSANTE - x.falecidos
    if (x.denominador <= 0).any():
        raise AnalyticsError("Denominador de trajetória nulo ou negativo.")
    if not x[["desistentes", "concluintes", "permanentes"]].sum(axis=1).eq(x.denominador).all():
        raise AnalyticsError("Estados de trajetória não reconciliam com ingressantes menos falecidos.")
    for count, official in [("desistentes", "TDA"), ("concluintes", "TCA"), ("permanentes", "TAP")]:
        if not np.allclose(rate(x[count], x.denominador), x[official], atol=0.02, rtol=0):
            raise AnalyticsError(f"Contagens acumuladas incompatíveis com {official} oficial.")
    x["ano"] = x.NU_ANO_REFERENCIA.astype(int)
    x["coorte"] = x.NU_ANO_INGRESSO.astype(int)
    x["horizonte"] = x.ano - x.coorte
    x["rede"] = x.TP_CATEGORIA_ADMINISTRATIVA.astype(str).map(
        {"1": "Pública", "2": "Pública", "3": "Pública", "4": "Privada", "5": "Privada", "7": "Especial"}
    ).fillna("Não informada")
    x["modalidade"] = x.TP_MODALIDADE_ENSINO.astype(str).map({"1": "Presencial", "2": "EAD"})
    x["grau"] = x.TP_GRAU_ACADEMICO.astype(str).map({"1": "Bacharelado", "2": "Licenciatura", "3": "Tecnológico"}).fillna("Não informado")
    x["area"] = x.NO_CINE_AREA_GERAL.fillna("Não informada")
    x["curso"] = x.NO_CURSO
    x["instituicao"] = x.NO_IES
    x["curso_id"] = x.CO_IES.astype(str) + ":" + x.CO_CURSO.astype(str)
    return x


def trajectory_summary(frame, dimensions):
    """Nunca agregar referências ou coortes distintas na mesma taxa."""
    if not {"ano", "coorte"}.issubset(dimensions):
        raise AnalyticsError("Agregação exige ano e coorte explícitos.")
    cols = ["denominador", "desistentes", "concluintes", "permanentes"]
    grouped = frame.groupby(dimensions, dropna=False, observed=True)
    out = grouped[cols].sum(min_count=1).reset_index()
    out["cursos"] = grouped.size().to_numpy()
    for c, name in [("desistentes", "tda"), ("concluintes", "tca"), ("permanentes", "tap")]:
        out[name] = rate(out[c], out.denominador)
    return out


def census(frame):
    key = ["NU_ANO_CENSO", "CO_IES", "CO_CURSO", "TP_DIMENSAO", "CO_MUNICIPIO"]
    require(frame, key + ["CO_UF", "TP_REDE", "TP_MODALIDADE_ENSINO", "NO_MUNICIPIO"])
    cols = ["NU_ANO_CENSO", "QT_MAT", "QT_VG_TOTAL", "QT_MAT_FIES", "QT_MAT_PROUNII", "QT_MAT_PROUNIP"]
    x = numeric(frame, cols)
    if x[key].isna().any().any() or x.duplicated(key).any():
        raise AnalyticsError("Chave municipal do Censo ausente ou duplicada.")
    if not x.CO_UF.astype(str).eq("51").all():
        raise AnalyticsError("Censo deve conter exclusivamente MT.")
    if not (x.TP_DIMENSAO.astype(str).isin(["1", "2"]) & x.TP_DIMENSAO.eq(x.TP_MODALIDADE_ENSINO)).all():
        raise AnalyticsError("Dimensões nacionais/municipais incompatíveis.")
    if (x[cols] % 1 != 0).any().any():
        raise AnalyticsError("Contagens do Censo devem ser inteiras.")
    if any(x[c].gt(x.QT_MAT).any() for c in cols[-3:]):
        raise AnalyticsError("Financiamento excede as matrículas compatíveis.")
    x["ano"] = x.NU_ANO_CENSO.astype(int)
    x["rede"] = x.TP_REDE.astype(str).map({"1": "Pública", "2": "Privada"})
    x["modalidade"] = x.TP_MODALIDADE_ENSINO.astype(str).map({"1": "Presencial", "2": "EAD"})
    if x[["rede", "modalidade"]].isna().any().any():
        raise AnalyticsError("Rede/modalidade desconhecida.")
    return x


def census_summary(frame):
    mapping = {"QT_MAT": "matriculas", "QT_MAT_FIES": "fies", "QT_MAT_PROUNII": "prouni_integral", "QT_MAT_PROUNIP": "prouni_parcial"}
    out = frame.groupby(["ano", "rede", "modalidade"], observed=True)[list(mapping)].sum(min_count=1).rename(columns=mapping).reset_index()
    for c in ["fies", "prouni_integral", "prouni_parcial"]:
        out[c + "_pct"] = rate(out[c], out.matriculas)
    out = out.sort_values(["rede", "modalidade", "ano"])
    groups = out.groupby(["rede", "modalidade"])
    previous = groups.matriculas.shift()
    out["variacao_pct"] = rate(out.matriculas - previous, previous)
    out.loc[groups.ano.diff().ne(1), "variacao_pct"] = np.nan
    return out.reset_index(drop=True)


def join_quality(courses, quality, edition):
    """Uma única edição e uma observação por IES/curso, sem multiplicar alunos."""
    q = quality.loc[quality.ano_cpc.eq(edition)].copy()
    key = ["CO_IES", "CO_CURSO"]
    if q[key].isna().any().any() or q.duplicated(key).any():
        raise AnalyticsError("CPC com chave ausente ou duplicada na edição.")
    if edition > int(courses.ano.min()):
        raise AnalyticsError("CPC posterior à referência não permitido.")
    result = courses.merge(q, on=key, how="left", validate="many_to_one")
    if len(result) != len(courses) or result.denominador.sum() != courses.denominador.sum():
        raise AnalyticsError("Junção CPC alterou a população.")
    result["faixa_cpc"] = result.faixa_cpc.fillna("Sem CPC")
    return result


def correlation(frame):
    complete = frame[["cpc", "tda"]].dropna()
    if len(complete) < 10 or complete.cpc.nunique() < 2 or complete.tda.nunique() < 2:
        return None
    return float(complete.cpc.corr(complete.tda))
