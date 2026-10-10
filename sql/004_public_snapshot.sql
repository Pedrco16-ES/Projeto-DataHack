-- OPCIONAL. Não aplicada automaticamente pelo dashboard ou pelo construtor.
-- Revisar e autorizar antes de executar no Supabase. Não altera staging/meta.
-- Se a tabela já existir, este script falha: não adota objetos desconhecidos.
BEGIN;
CREATE TABLE marts.public_snapshots (
    sha256 text PRIMARY KEY CHECK (sha256 ~ '^[0-9a-f]{64}$'),
    document jsonb NOT NULL CHECK (document->>'status' = 'approved_local_mvp'),
    active boolean NOT NULL DEFAULT false,
    created_at timestamptz NOT NULL DEFAULT now()
);
CREATE UNIQUE INDEX public_snapshots_one_active ON marts.public_snapshots(active) WHERE active;
ALTER TABLE marts.public_snapshots ENABLE ROW LEVEL SECURITY;
REVOKE ALL ON marts.public_snapshots FROM PUBLIC;
CREATE POLICY public_snapshot_read ON marts.public_snapshots FOR SELECT USING (active);
-- A política não concede privilégios: uma conta de leitura dedicada ainda
-- precisa de USAGE em marts e SELECT nesta tabela. Não conceder staging/meta.
-- Não habilitar anon/authenticated sem decisão explícita de publicação externa.
COMMIT;
