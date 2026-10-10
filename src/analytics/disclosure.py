"""Recortes públicos fixos: proteção antes de filtros, gráficos e downloads."""

import pandas as pd

STATES = ["denominador", "desistentes", "concluintes", "permanentes"]


def small(frame, columns):
    values = frame[columns]
    return ((values > 0) & (values < 10)).any(axis=1) | values.isna().any(axis=1)


def public_courses(final):
    """Oculta toda a linha e evita residuais pequenos contra o único total estadual.

    Não liberar outros totais completos por área, CPC, rede ou grau: os demais
    painéis usam exclusivamente este mesmo universo de cursos publicáveis.
    Ingressantes originais e óbitos não são exportados em nível de curso.
    """
    eligible = ~small(final, STATES) & final.denominador.ge(10)
    # Complementar: a diferença entre o total estadual e o detalhamento também
    # precisa conter zero ou >=10 em cada estado, para cada coorte/referência.
    for _, partition in final.groupby(["ano", "coorte"]):
        while True:
            visible = partition.loc[eligible.loc[partition.index]]
            residual = partition[STATES].sum() - visible[STATES].sum()
            if not residual.between(1, 9).any() or visible.empty:
                break
            eligible.loc[visible.sort_values("denominador").index[0]] = False
    cols = ["CO_IES", "CO_CURSO", "curso_id", "curso", "instituicao", "area", "rede",
            "modalidade", "grau", "ano", "coorte", "horizonte"] + STATES
    out = final.loc[eligible, cols].copy()
    for source, target in [("desistentes", "tda"), ("concluintes", "tca"), ("permanentes", "tap")]:
        out[target] = out[source] / out.denominador * 100
    return out


def public_census(summary):
    out = summary.copy()
    counts = ["matriculas", "fies", "prouni_integral", "prouni_parcial"]
    suppress_total = small(out, ["matriculas"])
    out["protegido"] = suppress_total
    # Não divulgar total dos benefícios nem categoria "sem benefício": como as
    # categorias se sobrepõem, outros programas não determinam o numerador oculto.
    for c in counts[1:]:
        suppress = suppress_total | small(out, [c]) | (out.matriculas - out[c]).between(1, 9)
        out.loc[suppress, [c, c + "_pct"]] = float("nan")
        out["protegido"] |= suppress
    prev = suppress_total.groupby([out.rede, out.modalidade]).shift(fill_value=False)
    out.loc[suppress_total | prev, "variacao_pct"] = float("nan")
    out.loc[suppress_total, "matriculas"] = float("nan")
    return out
