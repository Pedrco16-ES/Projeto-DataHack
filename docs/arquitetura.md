# Arquitetura

Fluxo MVP: fontes → ingestão/recorte MT → lotes reconciliados com staging → motor analítico local → proteção/aprovação técnica local → snapshot atômico em outputs → Streamlit/apresentação offline.

A etapa 2 implementou conexão; a 3, ingestão/tratamento; a 4, staging/meta/marts e cargas no Supabase. Etapas 5–8: src/analytics, snapshot protegido, oito telas e exportação. Cálculos pesados ocorrem na CLI; interface agrega apenas cursos publicáveis já validados.

`admin.py` é uma aplicação Streamlit exclusivamente local, vinculada a 127.0.0.1 no comando documentado. A CLI e a interface chamam o mesmo pipeline. Lotes são publicados atomicamente em data/processed, com hashes e status treated_not_approved; nenhuma importação chama a camada de banco. Consumo de memória: blocos para origem nacional e recorte MT materializado para checagens globais.

A configuração resolve caminhos relativos a partir da raiz do projeto, independentemente do diretório de execução. Variáveis do processo têm precedência sobre .env.local. Interpolação de valores dotenv está desativada para preservar credenciais literais.

SQLAlchemy usa psycopg 3, TLS obrigatório, timeout de conexão, timeout de consultas e leitura por padrão. sslmode=require criptografa a conexão, mas não valida a identidade do servidor como verify-full; este último pode ser configurado com sslrootcert apropriado. URLs com opções não suportadas são rejeitadas sem exibir seu conteúdo.

DATABASE_URL é administrativa. PUBLIC_DATABASE_URL deve ter SELECT apenas nos resultados aprovados; leitura por padrão não substitui privilégios. Sem fallback público para conta administrativa. Offline valida estado, versão e SHA-256 do JSON. Hash detecta alterações acidentais; não é assinatura contra quem controla o filesystem.

Snapshot: validar → gravar temporário → substituir atomicamente, preservando cópia anterior. SQL 004 oferece estrutura remota opcional ainda não aplicada. UI lê somente snapshot ativo e usa fallback offline com mensagem de origem. Nenhum banco, credencial ou serviço foi alterado nesta sessão.

Na Etapa 4, migration e cargas transacionais foram autorizadas, aplicadas e reconciliadas no Supabase. O plano liga hashes do SQL, relatório e dados às contagens revisadas. COPY usa tabelas temporárias; todos os lotes do plano são efetivados em uma transação. Durante a importação, o timeout por comando é ampliado para 180s apenas nessa transação. Locks, chaves e índice único de fonte/edição ativa evitam duplicação e substituição automática. Lotes retirados permanecem no histórico e deixam de aparecer nas views atuais. Consulte persistencia.md.
