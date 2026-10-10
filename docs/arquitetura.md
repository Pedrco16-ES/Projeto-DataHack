# Arquitetura

Fluxo previsto: fontes em DATA_DIR → ingestão → validação e recorte MT → staging → indicadores em marts → aprovação e supressão → snapshots em outputs → Streamlit.

A Etapa 2 implementou configuração e conexão. A Etapa 3 acrescentou contratos versionados, leitura CSV/XLSX/JSON/ZIP, validação do recorte MT, relatórios e downloads administrativos. Analytics e dashboard público continuam como pontos de extensão. Não foram criados esquemas ou tabelas no banco.

`admin.py` é uma aplicação Streamlit exclusivamente local, vinculada a 127.0.0.1 no comando documentado. A CLI e a interface chamam o mesmo pipeline. Lotes são publicados atomicamente em data/processed, com hashes e status treated_not_approved; nenhuma importação chama a camada de banco. Consumo de memória: blocos para origem nacional e recorte MT materializado para checagens globais.

A configuração resolve caminhos relativos a partir da raiz do projeto, independentemente do diretório de execução. Variáveis do processo têm precedência sobre .env.local. Interpolação de valores dotenv está desativada para preservar credenciais literais.

SQLAlchemy usa psycopg 3, TLS obrigatório, timeout de conexão, timeout de consultas e leitura por padrão. sslmode=require criptografa a conexão, mas não valida a identidade do servidor como verify-full; este último pode ser configurado com sslrootcert apropriado. URLs com opções não suportadas são rejeitadas sem exibir seu conteúdo.

DATABASE_URL é reservada às operações locais. PUBLIC_DATABASE_URL deverá pertencer a uma função PostgreSQL com SELECT apenas nos resultados aprovados. Leitura por padrão no cliente não substitui permissões do banco. Não existe fallback da conexão pública para a administrativa. O modo offline será implementado posteriormente.

Na Etapa 4, migration e cargas transacionais foram autorizadas, aplicadas e reconciliadas no Supabase. O plano liga hashes do SQL, relatório e dados às contagens revisadas. COPY usa tabelas temporárias; todos os lotes do plano são efetivados em uma transação. Durante a importação, o timeout por comando é ampliado para 180s apenas nessa transação. Locks, chaves e índice único de fonte/edição ativa evitam duplicação e substituição automática. Lotes retirados permanecem no histórico e deixam de aparecer nas views atuais. Consulte persistencia.md.
