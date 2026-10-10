# Persistência — Etapa 4

Implementação de migrations e carga transacional privada. O plano desta sessão foi explicitamente autorizado pelo usuário e executado no Supabase em 10/10/2026. A interface administrativa da Etapa 3 não cria tabelas nem grava no banco automaticamente. Novas cargas ou retiradas continuam sujeitas à revisão e autorização correspondentes.

## Estado e escopo

O diagnóstico somente leitura encontrou PostgreSQL 17.11, sem schemas meta/staging/marts e com permissão de criação de schemas. O plano atual contém cinco lotes e 67.824 registros aceitos: 5.150 de Trajetória e 62.674 dos Censos 2021–2024. São contagens de registros, não de alunos únicos. Rejeições e exclusões permanecem localmente; apenas seus relatórios são armazenados no banco.

A migration 001 e os cinco lotes foram efetivados. A reconciliação remota confirmou chaves, hashes registrados, contagens de linhas e somas dos principais campos de contagem contra os CSVs tratados. A repetição retornou reused em todos os lotes; permanecem cinco eventos de carga. Há TLS ativo, RLS nas seis tabelas e nenhum acesso aos schemas para anon/authenticated. Todos os lotes continuam sem aprovação pública.

Não serão criadas tabelas de IES, CPC ou IBGE sem contratos validados. Marts ficará reservado, sem indicadores ou acesso público. A revisão das fórmulas, cobertura e supressão pertence às próximas etapas.

## Objetos criados

- `meta.schema_versions`: versão e SHA-256 da migration aplicada.
- `meta.importacoes`: lote, origem, edição, hashes, contagens, status e datas.
- `meta.validacoes`: relatório administrativo de cada lote em JSONB.
- `meta.eventos`: eventos de carga e retirada com justificativa.
- `staging.trajetoria`: todas as colunas do contrato, com códigos em texto, contagens/anos inteiros e taxas numéricas.
- `staging.censo_curso`: união dos campos documentados nas edições 2021–2024; ausências de uma edição permanecem NULL.
- `staging.trajetoria_atual` e `staging.censo_curso_atual`: views somente com lotes de status loaded, incluindo a edição de origem.

Granularidade por lote: Trajetória `(CO_IES, CO_CURSO, NU_ANO_INGRESSO, NU_ANO_REFERENCIA)`; Censo `(NU_ANO_CENSO, CO_IES, CO_CURSO, TP_DIMENSAO, CO_MUNICIPIO)`. Cada linha tem o número do registro original. Chaves primárias e unicidade por lote impedem duplicações. Campos opcionais não são inventados. A diferença derivada ANOS_DESDE_INGRESSO pode ser calculada a partir dos anos originais; não é persistida como variável oficial.

Há no máximo um lote ativo por fonte/edição. Versões de edições diferentes podem conter trajetórias sobrepostas: toda consulta analítica precisa selecionar explicitamente uma edição e um horizonte, sem somar edições do mesmo acompanhamento. As tabelas históricas não devem ser consumidas diretamente por indicadores; utilize as views atuais com recorte temporal explícito.

## Plano e autorização

```powershell
.\venv\Scripts\python.exe -m src.database plan --inventory data/processed/latest_stage3.json --output data/processed/stage4_plan.json
```

O comando revalida tipos, chaves, UF, contagens, relatórios, hashes e a versão do pipeline. Não acessa o banco e não sobrescreve um plano existente. Para uma revisão futura, escolha outro nome de arquivo. O plano é ignorado pelo Git por conter caminhos administrativos locais.

Plano preparado nesta sessão: `data/processed/stage4_plan.json`.

SHA-256: `12f7b3bb76c116c20e2afd6cc132b4df385ff241f346f8941a2b3ff0588ded95`.

**Comando para executar somente após autorização:**

```powershell
.\venv\Scripts\python.exe -m src.database apply --plan data/processed/stage4_plan.json --approve-plan 12f7b3bb76c116c20e2afd6cc132b4df385ff241f346f8941a2b3ff0588ded95
```

O hash é uma confirmação operacional do artefato revisado, não substitui autenticação ou controle de acesso ao computador. O arquivo SQL revisável é `sql/001_staging.sql`, gerado por `src/database/ddl.py`; um teste garante correspondência entre gerador e migration.

## Efeito, riscos e limites

A aplicação cria três schemas novos e suas tabelas/views/índices, registra metadados e carrega os cinco lotes na conexão DATABASE_URL. Consome armazenamento e recursos de CPU/rede do projeto Supabase. Pode falhar por limites de espaço, timeout ou privilégios; erros do driver são ocultados para proteger dados de conexão.

Os schemas meta e staging não são públicos. A migration revoga privilégios de PUBLIC e, quando existem, das funções anon/authenticated nos objetos criados. RLS é habilitada sem políticas públicas. As views usam security_invoker. O carregador deve ser executado pela conta administrativa proprietária dos objetos; a futura conexão pública terá permissões específicas somente nos resultados aprovados. A proteção por schema continua necessária para futuros objetos, inclusive em bancos com privilégios padrão globais personalizados.

A migration recusa adotar schemas preexistentes sem o registro de versão/checksum esperado. Não exclui tabelas ou dados existentes. Também não substitui automaticamente lotes ativos. Aprovação estrutural de staging não é aprovação estatística ou pública; public_approved permanece false e não pode ser alterado para true nesta versão do schema.

## Transações e idempotência

1. Revalidar integralmente os lotes antes da operação.
2. Adquirir lock transacional específico do projeto, com espera limitada.
3. Aplicar DDL e registrar seu checksum em uma transação própria.
4. Iniciar uma transação para todos os lotes do plano.
5. Conferir identidade e conflitos de fonte/edição.
6. Copiar os dados via psycopg COPY para tabela temporária.
7. Reconciliar contagens e inserir na staging com restrições de integridade.
8. Registrar validações e auditoria, efetivando somente após todos os lotes passarem.

Qualquer falha na carga reverte todos os lotes dessa execução, inclusive metadados e auditorias de sucesso. Se a migration já tiver sido efetivada, os schemas permanecem disponíveis e vazios para correção/repetição; não há limpeza destrutiva automática. Falhas de DDL revertem a própria migration. Reexecutar o plano com mesmos hashes e contagens reutiliza os lotes, sem duplicar linhas ou eventos. Alteração de conteúdo, checksum ou lote ativo conflitante interrompe a operação.

Durante a carga, `SET LOCAL statement_timeout = '180s'` permite COPY dos lotes maiores pela conexão remota. O ajuste dura somente a transação; não altera a configuração permanente do servidor nem o limite de 15 segundos das consultas normais. O teste de integração verifica tanto o limite aplicado quanto sua restauração. Para conexões remotas mais lentas, `DB_CONNECT_TIMEOUT=30` pode ser configurado pelo operador, dentro dos limites validados da aplicação.

As falhas não são registradas como lotes publicados: o comando retorna falha sanitizada e a transação é revertida. Os relatórios locais continuam disponíveis. Não se promete detecção de toda alteração manual feita por um proprietário do banco; a reconciliação valida hashes registrados e contagens, e os privilégios devem limitar edições fora do pipeline.

## Reversão após sucesso

Retire somente os lotes do plano das views atuais, preservando dados e auditoria:

```powershell
.\venv\Scripts\python.exe -m src.database withdraw --plan data/processed/stage4_plan.json --approve-plan 12f7b3bb76c116c20e2afd6cc132b4df385ff241f346f8941a2b3ff0588ded95 --reason "Reversão autorizada da carga da Etapa 4"
```

Essa operação também exige autorização. Define status withdrawn e registra o motivo em uma única transação. A repetição é inócua. Um lote retirado não é reativado automaticamente. Os schemas e registros históricos permanecem; remoção física ou alteração da política de reativação requer revisão separada.

## Testes sem Supabase

```powershell
.\venv\Scripts\python.exe -m pytest -q
.\venv\Scripts\python.exe scripts/test_postgres.py --real-plan data/processed/stage4_plan.json
```

O primeiro comando executa os testes unitários e ignora integração quando não há instância de teste explicitamente configurada. O segundo usa os binários PostgreSQL locais (padrão Windows PostgreSQL 18; alterável com --pg-bin), cria um cluster exclusivo em data/processed, limita a escuta a 127.0.0.1, executa os testes e opcionalmente ensaia o plano real. Nunca lê DATABASE_URL para conectar esse cluster. A configuração trust/sem TLS é exclusiva do servidor descartável de testes, sem credenciais reais, e não modifica a configuração TLS da aplicação.

O helper encerra apenas a instância criada por ele ao final; os arquivos locais de diagnóstico são preservados e ignorados pelo Git. Para consultar os resultados no banco autorizado, utilize `sql/002_reconciliation.sql`.

Reconciliação automatizada somente leitura, sem imprimir dados de estudantes:

```powershell
.\venv\Scripts\python.exe scripts/verify_persistence.py --plan data/processed/stage4_plan.json
```

O resultado fica em `data/processed/stage4_supabase_verification.json`. O script usa até 30 segundos para conectar, exige TLS e leitura, compara chaves e contagens com os arquivos locais e confere a proteção dos schemas. Não retira ou altera lotes.
