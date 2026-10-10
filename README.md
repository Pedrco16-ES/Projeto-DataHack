# Rota do Diploma — DataHack Univag 2026

Projeto realizado no dia 10/10/26. Análise da trajetória dos estudantes do ensino superior em Mato Grosso.

## Estado atual

**Passo 3 concluído:** novas fontes integradas ao snapshot e às telas: comparação das coortes 2015–2020 no horizonte comum de quatro anos, Enade Licenciaturas 2025 protegido, evasão oficial estadual e mapa dos 141 municípios com vagas por 100 jovens em 2022. Consulte [integração e validação](docs/integracao_passo3.md) e [fontes e metodologia](docs/fontes_metodologia_20261010.md).

MVP local das etapas 5–8 implementado: oito telas Streamlit, métricas verificadas com dados reais, CPC 2023, financiamento, oferta municipal, filtros, CSV/XLSX e snapshot offline protegido. A etapa 4 permanece com cinco lotes e 67.824 registros reconciliados no Supabase.

Limites: evasão anual sem desagregação por rede/modalidade/curso; associação com financiamento indisponível. Enade tem 11 de 84 cursos presenciais publicáveis após proteção e não representa todo MT. A publicação remota do snapshot continua pendente. O MVP não equivale à conclusão científica de todas as perguntas.

## Abrir o MVP agora

Na pasta `Projeto-DataHack`, com o ambiente existente:

```powershell
.\venv\Scripts\python.exe -m streamlit run app.py --server.address=127.0.0.1
```

Abra `http://localhost:8501`. Alternativa: execute `iniciar_mvp.cmd`. O snapshot em `outputs/public_snapshot.json` permite abrir as oito telas sem rede ou banco. P1, coorte 2015 presencial, até 2024: **59,9% desistência, 38,8% conclusão e 1,3% permanência** sobre 41.889 ingressantes ajustados em 515 cursos. O detalhamento usa 283 cursos publicáveis e não representa a população completa.

## Reconstruir resultados e apresentação

```powershell
.\venv\Scripts\python.exe -m src.analytics
.\venv\Scripts\python.exe -m src.analytics --approve-local "Revisão técnica do MVP local"
.\venv\Scripts\python.exe scripts/export_presentation.py
```

O primeiro comando gera candidato administrativo sem mudar o snapshot. O segundo valida hashes, fórmulas, chaves e proteção e grava atomicamente o snapshot local, preservando `public_snapshot.previous.json`. Não publica na internet nem grava no Supabase. Para reverter, restaure a cópia anterior junto da versão de código compatível: o passo 3 exige snapshot schema 2. A apresentação `outputs/apresentacao.html` funciona offline e pode ser impressa em PDF. Consulte [apresentação](docs/apresentacao.md).

Em outra máquina, copie o snapshot protegido para `outputs/` para usar o dashboard. Para reconstruir, copie os lotes finais, `stage4_plan.json`, os arquivos oficiais CPC e os diretórios `data/raw/complementares_20261010` e `data/processed/complementares_20261010`, incluindo manifestos e relatórios. Esses dados são ignorados pelo Git. Não copie credenciais administrativas para hospedar a interface.

## Verificação rápida do MVP

```powershell
$mvpTestDir = Join-Path (Get-Location) ('data/processed/mvp-tests-' + [guid]::NewGuid().ToString('N'))
.\venv\Scripts\python.exe -B -m pytest tests/test_mvp.py -q -p no:cacheprovider --basetemp $mvpTestDir
```

Sete testes essenciais: oito telas, matemática, proteção, junções, exportações e fallback. Não iniciam banco, instalam pacotes ou alteram Supabase. Os testes anteriores continuam disponíveis.

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

`src/ingestion` e `src/processing`: tratamento; `src/database`: conexão e persistência; `src/analytics`: cálculos, proteção e snapshots; `src/export`: downloads administrativos e públicos separados. `components/dashboard.py`, `app.py` e `pages/` implementam as oito telas. `sql`, `tests`, `docs` e `prompts` guardam scripts, testes, documentação e registros de IA.

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

## Execução do Dashboard Público (8 Telas)

Completar fontes pendentes e rever a metodologia antes da publicação externa. Consultas administrativas: `sql/003_analytics_readonly.sql`. O backend público opcional lê `marts.public_snapshots` exclusivamente com `PUBLIC_DATABASE_URL`, sem fallback para a conta administrativa. Estrutura em `sql/004_public_snapshot.sql`, ainda não aplicada; faltam conta com SELECT restrito e carga do snapshot. O MVP entregue utiliza snapshot local.

O botão de atualização recarrega dados aprovados e invalida o cache de 5 minutos. Importações continuam na administração local. Migrations, cargas remotas e deploy não são automáticos.

Consulte [documentação do dashboard](docs/dashboard.md), [fontes](docs/fontes.md) e [validação](docs/validacao.md).
