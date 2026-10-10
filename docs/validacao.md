# Validação — Etapas 2, 3 e 4 — 10/10/2026

## Etapa 4 — concluída e validada no Supabase

Após autorização explícita do usuário, a migration 001 e os cinco lotes foram aplicados no Supabase PostgreSQL 17.11 em 10/10/2026. Reconciliação registrada às 18:09 UTC (15:09 em America/Sao_Paulo).

- Total persistido: **67.824 registros**, sendo 5.150 de Trajetória e 62.674 dos Censos.
- Mesmas chaves dos CSVs, mesmas contagens de linhas e mesmas somas de QT_INGRESSANTE/QT_PERMANENCIA/QT_CONCLUINTE/QT_DESISTENCIA/QT_FALECIDO na Trajetória e QT_MAT/QT_ING/QT_CONC no Censo.
- Hashes do plano, migration, relatórios e artefatos conferidos contra os metadados persistidos.
- Repetição remota retornou reused para todos os cinco lotes, sem novas linhas ou eventos de carga; permanecem cinco eventos.
- TLS ativo; verificação em transação somente leitura; timeout normal preservado em 15s.
- RLS habilitada nas seis tabelas; schemas sem USAGE para anon/authenticated; public_approved=false em todos os lotes.

Evidências locais ignoradas pelo Git: `data/processed/stage4_supabase_load.json`, `stage4_supabase_repeat.json` e `stage4_supabase_verification.json`. A verificação pode ser repetida com scripts/verify_persistence.py.

### Ajuste identificado durante a execução remota

A migration foi concluída, mas a primeira carga não foi efetivada. Foi confirmado rollback com zero lotes e zero linhas nas duas tabelas. A investigação identificou cancelamento de consulta SQLSTATE 57014 durante o Censo, sob limite de 15s. A carga passou a usar SET LOCAL statement_timeout='180s', exclusivo da transação de importação. Uma falha transitória de conexão também exigiu nova tentativa com connect_timeout=30, sem modificar a configuração permanente nem a .env.local.

Após o ajuste, **53 testes passaram em 13,39 s**, incluindo verificação de que o timeout maior é restaurado ao fim da transação. Evidência local: `data/processed/pg-test-a0b8e4f9f61b/pytest.xml`. A carga remota foi então concluída, repetida e reconciliada com sucesso. A retirada lógica não foi executada no Supabase: os cinco lotes permanecem ativos. Nenhum commit, push ou deploy foi realizado.

### Histórico dos testes antes da autorização

Resultado final: **53 testes aprovados em 13,68 s**, incluindo nove testes de integração em PostgreSQL 18.4 local isolado. Nenhum teste de integração foi executado no Supabase. O diagnóstico remoto foi somente leitura: PostgreSQL 17.11, schemas meta/staging/marts ausentes, permissão de criação disponível.

### Verificações aprovadas

- Migration transacional, checksum, repetição sem alteração e recusa de adoção de schemas desconhecidos.
- Revalidação de artefatos, contratos, chaves, tipos, recorte territorial e contagens antes da carga.
- COPY para tabela temporária e reconciliação antes/depois da inserção.
- Preservação de códigos textuais e constraints de contagens não negativas.
- Segunda carga sem duplicação de registros ou eventos de sucesso.
- Duas cargas concorrentes do mesmo plano resultaram em um carregamento e uma reutilização.
- Falha induzida depois da cópia do segundo lote reverteu todos os lotes, metadados e eventos da transação.
- Falha induzida na migration reverteu os schemas criados nessa transação.
- Lote conflitante de mesma fonte/edição foi bloqueado; retirada lógica preservou o histórico e permitiu nova versão explícita.
- Retirada com um lote inexistente reverteu integralmente a operação.
- PUBLIC sem acesso aos schemas; privilégios herdados de anon/authenticated foram revogados dos objetos criados em simulação local; RLS habilitada.
- pip check sem conflitos; git diff --check sem erros de whitespace (aviso LF/CRLF do Windows).

### Ensaio integral com os lotes tratados

Em cluster local exclusivo, os cinco lotes do plano foram carregados e repetidos: 5.150 registros de Trajetória e 62.674 de Censo, total 67.824. Todos os lotes retornaram loaded na primeira carga e reused na segunda. A retirada dos cinco lotes zerou as views atuais sem excluir os registros históricos.

Resultados administrativos preservados em `data/processed/pg-test-09515575a370/real_plan_results.json`. Execução final dos 53 testes em `data/processed/pg-test-cf9dbd58c0d2/pytest.xml` e `pytest.log`. As instâncias temporárias foram encerradas; esses diretórios são ignorados pelo Git.

O primeiro ensaio de inicialização encontrou uma limitação de token restrito no Windows. A tentativa seguinte evidenciou bloqueio na captura de pipes do controlador. O helper foi ajustado para logs em arquivo e stdin fechado; somente seus processos/cluster temporários foram encerrados. Nenhum serviço existente foi reiniciado.

### Plano autorizado

SQL revisável: `sql/001_staging.sql`. Plano local: `data/processed/stage4_plan.json`, SHA-256 `12f7b3bb76c116c20e2afd6cc132b4df385ff241f346f8941a2b3ff0588ded95`.

A execução autorizada e a reconciliação no PostgreSQL 17.11 foram concluídas conforme os resultados acima. Os testes locais também passaram no PostgreSQL 18.4. O plano criou schemas privados e carregou somente registros aceitos; não publicou indicadores. Impacto e reversão estão em persistencia.md.

## Etapa 3 — resultado final

39 testes aprovados em 5,21 s na execução final; pip check sem conflitos. Inclui testes da interface com Streamlit AppTest (abertura, prévia, manutenção da amostra após rerun e invalidação da confirmação ao trocar edição). Não foi realizado teste visual em navegador.

Cobertura: CSV, XLSX com cabeçalho na nona linha, JSON, ZIP e rejeição de caminhos inseguros; preservação de códigos textuais/zeros à esquerda; códigos numéricos do Excel com nulos; valores ausentes; contagens negativas e fracionárias; taxas fora de faixa; períodos/chaves inválidos; duplicatas entre blocos; granularidade municipal; confirmação de mapeamento; reuso e detecção de artefatos alterados; reconciliação; exportação CSV/XLSX e neutralização de fórmulas.

### Processamento integral das fontes locais

Contagens de **registros**, não de estudantes ou indicadores do desafio. As rejeições abaixo incluem registros nacionais sem UF identificável, não apenas dados de MT.

| Fonte | Recebidos | Aceitos MT | Rejeitados | Excluídos do recorte |
| --- | ---: | ---: | ---: | ---: |
| Trajetória edição 2024 | 281.431 | 5.150 | 11.181 | 265.100 |
| Censo cursos 2021 | 444.786 | 12.278 | 0 | 432.508 |
| Censo cursos 2022 | 573.019 | 15.059 | 1 | 557.959 |
| Censo cursos 2023 | 671.610 | 17.022 | 4 | 654.584 |
| Censo cursos 2024 | 720.349 | 18.315 | 9 | 702.025 |

Todos os lotes finais reconciliam recebidos = aceitos + rejeitados + excluídos. Nenhuma duplicata nas chaves testadas do recorte MT. Todos os aceitos têm CO_UF=51. O recorte da Trajetória contém somente coorte 2015, com referências de 2015 a 2024.

Cada arquivo foi submetido novamente com tamanho de bloco diferente: o pipeline reutilizou o lote após validar SHA-256 dos artefatos, sem acrescentar linhas. Este teste verifica idempotência local; não comprova idempotência de uma carga PostgreSQL ainda não implementada.

### Lotes finais

Os diretórios abaixo estão em data/processed e não estão versionados:

- Trajetória: `b4dc6e7e54837534c70f82a1`.
- Censo 2021: `87f5c5bcda628b47b3026875`.
- Censo 2022: `6097b78b393c4e0dec66f5b3`.
- Censo 2023: `f047c5b5c5511a84294561c5`.
- Censo 2024: `ad16c6d9aa985e79a73c3347`.

`data/processed/latest_stage3.json` registra o inventário desta execução de validação. Lotes anteriores da investigação foram preservados; não utilizá-los como lotes finais. Cada diretório contém report.json, accepted.csv, rejected.csv e excluded.csv. Todos possuem status treated_not_approved e zero linhas importadas no banco.

### Problemas encontrados e corrigidos

- A construção inicial de DataFrames de Excel com códigos numéricos e nulos convertia 51 para texto 51.0, alterando o recorte. Corrigida pela preservação do tipo objeto antes da conversão para string; teste de regressão verifica independência do tamanho de bloco. A base real foi integralmente reprocessada.
- Censo 2022 apresenta UF 0 em dimensões geográficas 3 e 4. A classificação usa a dimensão definida pelo dicionário para separar registros nacionais/exteriores; não fabrica localização estadual.
- Cadastro IES 2021 possui campos não encontrados no dicionário consultado. Sua ingestão ficou explicitamente pendente de contrato/granularidade próprios.

### Pendências para a Etapa 4

As 11.181 rejeições de Trajetória têm UF ausente/inválida: 11.180 indicam modalidade EAD e uma não tem modalidade. Não atribuir esses registros a MT pela sede da instituição sem justificativa metodológica. Os Censos 2022–2024 também têm registros sem localização identificável, preservados em rejeição.

Revisar relatórios, ausências e outliers; confirmar chaves definitivas; distinguir lacuna geográfica de dado inválido; aprovar schemas e migrations antes da carga. Os candidatos aprovados estruturalmente não são indicadores validados. Falecimentos, contagens anuais/acumuladas, denominadores, cobertura de junções e supressão continuam pendentes.

Nenhum dado do banco foi alterado, nenhum resultado foi publicado e nenhum commit/push/deploy foi feito. A interface administrativa deve continuar local. O processamento nacional é em blocos, mas a análise global de duplicidades e qualidade materializa o recorte MT em memória.

## Histórico — Etapa 2

Ambiente: Windows, Python 3.13.7, venv do projeto. Dependências instaladas com requirements.txt. Nenhuma tabela ou dado do banco foi alterado; nenhum commit, push ou deploy foi realizado.

## Verificações executadas

- `venv/Scripts/python.exe -m pytest -q`: 14 testes aprovados (0,54 s na execução final).
- `venv/Scripts/python.exe -m pip check`: sem dependências incompatíveis reportadas.
- `venv/Scripts/python.exe test_connection.py`: SELECT 1 retornou 1 e TLS foi confirmado com psycopg 3.
- `SHOW transaction_read_only`: on na conexão criada pela aplicação.
- `SHOW statement_timeout`: 15s.
- `git diff --check`: sem erros de whitespace; aviso de conversão LF/CRLF no Windows.
- `git check-ignore`: confirmou exclusão de .env.local, .env, exemplos de dados brutos, rejeições e outputs não aprovados.

Testes cobrem precedência de ambiente, ausência de credenciais no repr, caminhos, URLs inválidas, rejeição de TLS desativado e opções não autorizadas, separação da conexão pública, limites de timeout, configuração sem banco, sanitização de falhas e liberação do pool.

## Problemas resolvidos

A instalação precisou de acesso de rede fora da restrição inicial. A validação real encontrou uma diferença em relação ao psycopg2: no psycopg 3 o estado TLS é consultado por pgconn.ssl_in_use. O código foi corrigido e os testes unitários e a conexão real foram executados novamente com sucesso.

## Limites registrados ao final da Etapa 2

Não existem indicadores aprovados, schemas da aplicação criados por esta etapa, ingestão, dashboard ou snapshots. Os módulos de ingestão, processamento, análise e exportação são apenas estrutura. Idempotência, chaves, cobertura das junções, proteção de células pequenas e fallback offline serão testados quando implementados.

A conexão pública com permissões restritas ainda precisa ser configurada; leitura por padrão no cliente não substitui privilégios PostgreSQL. O requirements.txt define intervalos, sem lockfile transitivo. O suporte a XLS antigo depende de decisão futura. Fontes ausentes e limitações estão em fontes.md e metricas.md.
