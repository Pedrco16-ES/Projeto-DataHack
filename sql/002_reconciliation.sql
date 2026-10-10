-- Consultas somente leitura, após a carga autorizada.
SELECT i.batch_id, i.source, i.edition, i.status, i.accepted,
       CASE i.source
         WHEN 'trajetoria' THEN (SELECT count(*) FROM staging.trajetoria t WHERE t.batch_id=i.batch_id)
         WHEN 'censo_curso' THEN (SELECT count(*) FROM staging.censo_curso c WHERE c.batch_id=i.batch_id)
       END AS stored_rows,
       i.public_approved
FROM meta.importacoes i
ORDER BY i.source, i.edition, i.loaded_at;

SELECT source_edition, count(*) AS records
FROM staging.trajetoria_atual GROUP BY source_edition;
SELECT source_edition, count(*) AS records
FROM staging.censo_curso_atual GROUP BY source_edition;

-- Cada view contém somente lotes carregados e ainda não retirados.
-- Linhas antigas permanecem na staging para auditoria, sem aprovação pública.
SELECT batch_id, action, created_at FROM meta.eventos ORDER BY event_id;
