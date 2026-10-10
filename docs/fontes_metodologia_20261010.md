# Passos 1 e 2 — fontes e metodologia concluídas no limite das publicações

**Atualização posterior:** a integração local ao dashboard e ao snapshot foi concluída no [passo 3](integracao_passo3.md). Os parágrafos abaixo preservam o registro dos passos 1 e 2; a referência a dados ainda não integrados descreve aquele momento. O Supabase não foi alterado no passo 3.

Data: 10/10/2026. Escopo: adquirir/preparar fontes oficiais e fechar contratos técnicos. Os novos dados são administrativos e ainda não foram integrados ao dashboard nem enviados ao Supabase. O snapshot anterior permanece inalterado. Não houve instalação de pacotes ou uso de agentes adicionais.

## 1. Fontes obtidas e verificadas

| Fonte | Preparação e evidência |
| --- | --- |
| Trajetória 2016–2020, edição até 2024 | Cinco ZIP oficiais baixados; cabeçalhos e SHA-256 dos dicionários iguais ao contrato existente; séries MT completas, chaves e taxas oficiais verificadas |
| IBGE, tabela SIDRA 9514, variável 93 | Sete idades simples, 18–24 anos, sexo Total e declaração Total; 987 observações, 141 municípios, população somada de 397.671 |
| Malha municipal IBGE 2022 | GeoJSON com 141 códigos, exatamente iguais aos da população; anéis fechados e coordenadas conferidos |
| Cadastro municipal | Cadastro de 2022 derivado da consulta exaustiva SIDRA e reconciliado com a malha. Cadastro atual consultado tem 142 municípios; Boa Esperança do Norte não é incluída no recorte 2022 |
| Enade Licenciaturas 2025 | Planilha oficial atualizada em 25/05/2026: 4.948 cursos nacionais e três linhas de rodapé excluídas; 97 cursos MT, sendo 84 presenciais e 13 EAD; seis registros sem resultado calculável preservados |
| Fluxo do sistema por UF 2010–2024 | Planilha oficial, aba TX_EVASAO: 14 transições anuais de MT; sem rede/modalidade/curso e sem numeradores/denominadores absolutos publicados |
| Documentação | Metodologia de trajetória 2017, apresentação Censo 2024 e apresentação Enade/PND 2025 preservadas em PDF |

Originais: `data/raw/complementares_20261010/`. Preparados: `data/processed/complementares_20261010/`. URL, horário UTC de aquisição, tamanho, headers e SHA-256 de cada arquivo estão em [manifesto versionado](fontes_complementares_manifest.json). O diretório de dados permanece ignorado pelo Git.

Referências oficiais: [Trajetória INEP](https://www.gov.br/inep/pt-br/acesso-a-informacao/dados-abertos/indicadores-educacionais/indicadores-de-trajetoria-da-educacao-superior), [Enade por curso 2025](https://www.gov.br/inep/pt-br/acesso-a-informacao/dados-abertos/indicadores-educacionais/indicadores-de-qualidade-da-educacao-superior/2025), [SIDRA 9514](https://sidra.ibge.gov.br/tabela/9514), [malha IBGE 2022](https://servicodados.ibge.gov.br/api/v3/malhas/estados/51?formato=application/vnd.geo%2Bjson&qualidade=minima&intrarregiao=municipio&periodo=2022), [fluxo por UF](https://www.gov.br/inep/pt-br/acesso-a-informacao/dados-abertos/indicadores-educacionais/indicadores-de-fluxo-da-educacao-superior/2010-2024).

## 2. Decisões metodológicas

**P1:** manter coorte 2015 presencial até 2024. Contagens anuais acumuladas antes dos filtros; denominador = ingressantes menos falecimentos acumulados. Nenhuma mudança dos resultados atuais.

**P2:** comparar 2015–2020 no horizonte comum **h=4**, em que h=referência−ingresso. São cinco observações, h=0 a h=4, com referências 2019–2024. Não comparar todas as turmas na referência 2024, pois teriam exposição diferente. Mesmo horizonte não remove diferenças de composição ou de calendário/pandemia; não tratar diferenças como efeito causal. Diagnóstico privado em `diagnostico_coortes_h4_privado.csv`; publicar exige proteção para a nova família de recortes.

**P3:** adotar como série complementar a **taxa oficial de evasão do sistema de educação superior, total de MT**, reproduzida da tabela do INEP. A unidade é o estudante acompanhado entre dois anos consecutivos, com situação ativa no ano-base; não é uma razão entre contagens anuais de cursos. Usar rótulos completos de transição: 2020→2021, 2021→2022, 2022→2023 e 2023→2024. A tabela publica, respectivamente, 13,7%, 16,7%, 17,9% e 18,5%.

Não reconstruir numeradores/denominadores absolutos a partir dessas taxas arredondadas, nem ponderar por QT_MAT. Os recortes **MT × rede × modalidade** não estão no arquivo obtido; essa parte de P3 permanece sem fonte suficiente. Matrículas por rede/modalidade continuam calculáveis em painel separado. Com quatro pontos, variações e maior mudança são descritivas; não afirmar outlier estatístico. [Definição de fluxo INEP](https://www.gov.br/inep/pt-br/acesso-a-informacao/dados-abertos/indicadores-educacionais/indicadores-de-fluxo-da-educacao-superior/sobre).

**P4:** manter edição única **CPC 2023** para associação exploratória com desfecho da coorte 2015 em 2024. A edição é anterior ao desfecho final, mas posterior ao ingresso e parte das desistências: não é exposição causal de entrada. O ciclo cobre áreas específicas. Não preencher Sem CPC usando automaticamente outras edições. Comparações por rede, área e grau são descritivas; correlação não ponderada entre cursos não comprova causalidade. Uma análise causal exigiria outro desenho e controles.

**P5:** numerador = concluintes iguais ou acima do Padrão 1 de Proficiência; denominador = concluintes participantes com resultado disponível. Não usar inscritos nem concluintes da trajetória. A planilha armazena **fração 0–1**, apesar do título Percentual: calcular taxa pelas contagens e multiplicar por 100. Valores publicados estão arredondados a três casas; reconciliação aceita erro de até 0,00051 na fração. SC/ausências permanecem ausentes, não zero.

Recorte principal de P5: presencial de MT; EAD fica separado, porque a localização do curso não demonstra residência do participante. Entre 99 cursos de licenciatura da trajetória 2015/2024, 68 encontram correspondência nos 84 cursos presenciais Enade 2025, e 64 têm resultado calculável. Chave IES + curso em edição única, sem multiplicação de linhas. A união é por curso; os estudantes e denominadores são diferentes. O cruzamento está conferido administrativamente, ainda sem publicação de pequenas células.

**B1:** usar vagas presenciais **Censo Superior 2022** e população **Censo Demográfico 2022**, com cadastro/malha 2022. Fórmula: vagas/população de 18–24 ×100. Há 42 municípios com registros presenciais na base tratada e nenhuma chave fora do cadastro. Fazer LEFT JOIN partindo dos 141 municípios. Ausência de registro de oferta pode ser rotulada como "sem oferta presencial registrada" após reconciliação da fonte; não confundir com impossibilidade de acesso. População ausente/zero deve produzir indicador indisponível, não zero. Não usar o denominador 2022 como se fosse população de 2024.

**B2:** manter FIES, ProUni integral e parcial separados, cada um sobre matrículas privadas compatíveis. A sobreposição não foi demonstrada; não criar soma de beneficiários. A taxa oficial de evasão estadual não pode ser atribuída a cursos para correlacionar com financiamento. Essa associação continua bloqueada por ausência de desfecho compatível no mesmo grão/tempo. Não substituir por desvinculados/matrículas ou usar a trajetória da coorte 2015 como evasão anual de 2021–2024.

## Validação e reprodução

Três testes essenciais passaram em 1,92 s: população/idades/geometria e duplicatas; fração/contagens/ausências Enade; escala e transições da evasão oficial. Além disso, a preparação executou as validações reais de todas as novas coortes. Não repetida a bateria do dashboard, pois a interface e o snapshot não mudaram.

```powershell
.\venv\Scripts\python.exe -B scripts/acquire_official_sources.py
.\venv\Scripts\python.exe -B -m src.ingestion.supplements
.\venv\Scripts\python.exe -B -m src.ingestion.flow
.\venv\Scripts\python.exe -B scripts/validate_supplement_scope.py
.\venv\Scripts\python.exe -B -m pytest tests/test_supplements.py -q -p no:cacheprovider
```

Downloads existentes são reutilizados somente com manifesto/hash compatíveis. INEP exigiu cadeia de certificados resolvida pelo Windows; o coletor usa HTTPS nativo com validação ativa, sem desabilitar TLS. Não foram necessários microdados individuais do Enade: a planilha oficial por curso já fornece os numeradores/denominadores requeridos.

Próximo passo: integrar esses recortes e contratos às análises/telas, revisar a proteção conjunta antes de atualizar o snapshot. Validação técnica documentada não representa homologação pelo INEP nem aprovação editorial da equipe do desafio.
