-- Consultas ADMINISTRATIVAS, somente leitura. Não alimentar a UI diretamente:
-- os resultados detalhados precisam da proteção de src/analytics/disclosure.py.
-- Executar cada consulta separadamente. As chaves já são validadas na staging.

-- P1: acumular ANTES de selecionar a referência; mesmo painel de cursos.
WITH series AS (
  SELECT t.*,
    sum(qt_desistencia) OVER w AS desistentes,
    sum(qt_concluinte) OVER w AS concluintes,
    qt_ingressante - sum(qt_falecido) OVER w AS denominador
  FROM staging.trajetoria_atual t
  WHERE nu_ano_ingresso = 2015 AND tp_modalidade_ensino = '1'
  WINDOW w AS (PARTITION BY co_ies, co_curso, nu_ano_ingresso
               ORDER BY nu_ano_referencia ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW)
)
SELECT nu_ano_referencia, sum(denominador) AS denominador,
       sum(desistentes) AS desistentes, sum(concluintes) AS concluintes,
       sum(qt_permanencia) AS permanentes,
       100.0 * sum(desistentes) / nullif(sum(denominador), 0) AS tda,
       100.0 * sum(concluintes) / nullif(sum(denominador), 0) AS tca,
       100.0 * sum(qt_permanencia) / nullif(sum(denominador), 0) AS tap
FROM series GROUP BY nu_ano_referencia ORDER BY nu_ano_referencia;

-- P2: taxas oficiais POR CURSO, mesma coorte e mesmo horizonte.
-- Agregados por área devem usar contagens acumuladas da consulta anterior.
SELECT co_ies, co_curso, no_curso, no_cine_area_geral,
       nu_ano_ingresso, nu_ano_referencia,
       nu_ano_referencia - nu_ano_ingresso AS horizonte, tda, tca, tap
FROM staging.trajetoria_atual
WHERE nu_ano_ingresso = 2015 AND nu_ano_referencia = 2024
  AND tp_modalidade_ensino = '1'
ORDER BY tda DESC;

-- P3 e B2: matrículas e financiamento em grão municipal compatível.
-- FIES e ProUni são separados; não há taxa de evasão anual aprovada.
SELECT nu_ano_censo, tp_rede, tp_modalidade_ensino,
       sum(qt_mat) AS matriculas,
       sum(qt_mat_fies) AS fies,
       sum(qt_mat_prounii) AS prouni_integral,
       sum(qt_mat_prounip) AS prouni_parcial,
       100.0 * sum(qt_mat_fies) / nullif(sum(qt_mat), 0) AS fies_pct,
       100.0 * sum(qt_mat_prounii) / nullif(sum(qt_mat), 0) AS prouni_integral_pct,
       100.0 * sum(qt_mat_prounip) / nullif(sum(qt_mat), 0) AS prouni_parcial_pct
FROM staging.censo_curso_atual
WHERE co_uf = '51' AND tp_dimensao IN ('1','2')
  AND tp_dimensao = tp_modalidade_ensino AND nu_ano_censo BETWEEN 2021 AND 2024
GROUP BY nu_ano_censo, tp_rede, tp_modalidade_ensino
ORDER BY nu_ano_censo, tp_rede, tp_modalidade_ensino;

-- P4: CPC é validado localmente em src/analytics/build.py, edição única 2023.
-- Não há tabela de CPC carregada no banco: nenhum JOIN fictício é criado.
-- P5: a seleção abaixo é administrativa; Enade 2025 ainda não disponível.
SELECT co_ies, co_curso, no_curso, nu_ano_ingresso, nu_ano_referencia, tda, tca, tap
FROM staging.trajetoria_atual
WHERE tp_grau_academico = '2' AND tp_modalidade_ensino = '1'
  AND nu_ano_ingresso = 2015 AND nu_ano_referencia = 2024;

-- B1: somente vagas registradas; população IBGE ausente, sem fabricar zeros.
SELECT nu_ano_censo, co_municipio, no_municipio, sum(qt_vg_total) AS vagas
FROM staging.censo_curso_atual
WHERE tp_dimensao = '1' AND tp_modalidade_ensino = '1' AND co_uf = '51'
GROUP BY nu_ano_censo, co_municipio, no_municipio;
