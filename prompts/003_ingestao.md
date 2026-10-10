# Sessão de IA — Etapa 3 — 10/10/2026

Solicitação: “quando chegar a etapa que precisa das tabelas tratadas me avise, mas pode continuar com o passo 3”.

Escopo: leitura e tratamento locais de Trajetória e Censo, interface administrativa, CLI, contratos, relatórios e testes. Preservar originais e credenciais. Não criar tabelas PostgreSQL, fazer commits, push ou deploy.

Decisões baseadas nos arquivos: chave municipal do Censo inclui TP_DIMENSAO e CO_MUNICIPIO; fontes nacionais e exteriores não devem ser somadas ao recorte MT. O Censo 2022 utiliza UF 0 em observações sem alocação estadual; a dimensão geográfica determina a exclusão, sem atribuir município fictício. Trajetória usa cabeçalho técnico na nona linha e coluna TADA. Campos numéricos de códigos no Excel são convertidos para texto preservando inteiros mesmo na presença de nulos.

A Etapa 4 exigirá revisão das tabelas tratadas e dos relatórios antes da carga no banco. Os lotes desta etapa não estão aprovados para publicação. Dados didáticos ficam restritos aos testes.
