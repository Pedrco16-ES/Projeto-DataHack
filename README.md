# Rota do Diploma — DataHack Univag 2026

Projeto realizado no dia 10/10/26. Análise da trajetória dos estudantes do ensino superior em Mato Grosso.

## Estado atual

Etapa 4 concluída: configuração, conexão PostgreSQL com TLS, ingestão local, tratamento do recorte MT, interface administrativa, migration e persistência transacional privada. Após autorização, cinco lotes com 67.824 registros foram carregados e reconciliados no Supabase. A repetição reutilizou os lotes sem duplicação. Ainda não há dashboard público, tabelas de indicadores ou resultados analíticos aprovados.

## Instalação no Windows

Python 3.11 ou superior; ambiente validado com Python 3.13. Execute dentro de `Projeto-DataHack`:

```powershell
python -m venv venv
.\venv\Scripts\python.exe -m pip install -r requirements.txt
```

Se `venv` já existe, use somente o segundo comando. O caminho explícito evita usar acidentalmente pacotes do Python global. As dependências têm intervalos de versões; não há lockfile completo nesta etapa.

## Configuração

Se não existir `.env.local`, copie `.env.example` para esse nome. Preserve seu arquivo existente. Preencha `DATABASE_URL` com a connection string PostgreSQL do provedor, nunca a URL HTTPS do painel. Credenciais com caracteres especiais devem estar codificadas para uso em URL. Não compartilhe a string nem registre seu conteúdo em logs.

- `DATABASE_URL`: conexão local administrativa; os testes usam somente leitura.
- `PUBLIC_DATABASE_URL`: futura conexão com usuário restrito a resultados públicos; pode permanecer vazia nesta etapa. Não reutilizar automaticamente a conta administrativa.
- `DATA_DIR`: padrão `../Dados`; os arquivos originais permanecem fora do repositório.
- `OUTPUTS_DIR`: padrão `outputs`; reservado a snapshots públicos aprovados.
- `DB_CONNECT_TIMEOUT`: segundos, padrão 10.
- `DB_STATEMENT_TIMEOUT_MS`: milissegundos, padrão 15000.

Os caminhos relativos são resolvidos a partir da raiz do projeto. Variáveis do processo prevalecem sobre `.env.local`. TLS é obrigatório; `require` é o padrão, com suporte a `verify-full` e certificado adequado. Consulte [arquitetura](docs/arquitetura.md).

## Verificação

```powershell
.\venv\Scripts\python.exe test_connection.py
.\venv\Scripts\python.exe -m pytest -q
.\venv\Scripts\python.exe -m pip check
```

O teste de conexão executa `SELECT 1`, verifica TLS e encerra a transação sem gravações. Os testes unitários não precisam de banco ou credenciais reais. Não publique tracebacks brutos de drivers ou objetos de configuração serializados.

## Estrutura

`src/ingestion` e `src/processing`: leitura e tratamento locais; `src/database`: conexão; `src/analytics`: métricas futuras; `src/export`: downloads administrativos CSV/XLSX. `components` e `pages` serão usados no dashboard. `sql`, `tests`, `docs` e `prompts` guardam respectivamente scripts, testes, documentação e registros de IA.

`data/raw` e `data/processed` são ignorados, exceto os marcadores de diretório. `outputs` não recebe arquivos no Git automaticamente: cada resultado precisará de aprovação e proteção de células menores que 10. Dados brutos e rejeitados nunca devem aparecer na interface pública.

## Ingestão e administração local

```powershell
.\venv\Scripts\python.exe -m src.ingestion --help
.\venv\Scripts\python.exe -m streamlit run admin.py --server.address=127.0.0.1
```

A interface permite escolher arquivos do disco ou fazer upload, visualizar a amostra e confirmar o processamento. Para arquivos grandes, use a CLI descrita em [ingestão](docs/ingestao.md). Suporte validado: Censo de cursos 2021–2024 e Trajetória edição 2024. Cadastro de IES, outros anos e outras fontes aguardam contratos próprios.

Os lotes ficam em `data/processed/<batch_id>/`: `accepted.csv`, `rejected.csv`, `excluded.csv` e `report.json`. São dados administrativos, ainda não aprovados e sem supressão. Não exponha `admin.py` na rede ou em hospedagem pública. Os arquivos originais não são modificados. A carga no banco usa um plano revisado e confirmação explícita de hash.

## Persistência privada

Consulte [persistência](docs/persistencia.md) para objetos SQL, plano de carga, riscos, autorização e reversão. O SQL está em `sql/001_staging.sql`; as consultas de reconciliação, em `sql/002_reconciliation.sql`.

```powershell
.\venv\Scripts\python.exe -m src.database --help
.\venv\Scripts\python.exe scripts/test_postgres.py --real-plan data/processed/stage4_plan.json
```

O segundo comando requer os binários PostgreSQL locais e executa testes em uma instância exclusiva de loopback, encerrada ao final. Não conecta ao Supabase. O plano desta sessão está em `data/processed/stage4_plan.json`; ele contém cinco lotes com 67.824 registros, não alunos únicos. A documentação fornece os comandos de aplicação e retirada lógica para execução autorizada.

## Próximas etapas

Etapa 5: métricas obrigatórias com contratos e validações estatísticas. Etapas posteriores: oito telas, bônus, exportação pública protegida e snapshots offline. Lacunas de fontes e de cobertura seguem documentadas; estar carregado na staging não significa aprovação para publicação.

O comando `streamlit run app.py` será disponibilizado quando o dashboard público existir. A aplicação de migrations e cargas PostgreSQL não é automática; não há deploy configurado.

Leia [fontes](docs/fontes.md), [contratos pendentes](docs/metricas.md), [dashboard previsto](docs/dashboard.md) e [validação](docs/validacao.md).
