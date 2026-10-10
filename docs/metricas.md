# Contratos de métricas — MVP local, 10/10/2026

**Revisão posterior:** [contratos dos passos 1 e 2](fontes_metodologia_20261010.md) definem comparação de seis coortes em h=4, B1 com anos alinhados em 2022, proficiência Enade por contagens e evasão oficial total de MT. Esses contratos foram implementados no [passo 3](integracao_passo3.md). O restante deste documento registra os contratos do MVP inicial; pendências de fontes foram superadas conforme o relatório de integração.

## Trajetória: P1, P2 e P5

Fonte: dicionário DOCX local e planilha INEP 2015–2024. QT_CONCLUINTE, QT_DESISTENCIA e QT_FALECIDO são contagens anuais. Identidade confrontada com todas as 5.150 linhas aceitas.

- Grão: IES + curso + coorte + referência; UF 51, presencial.
- Numeradores: desistências e conclusões acumuladas desde o ingresso; permanência é a contagem do ano.
- Denominador: ingressantes menos falecimentos acumulados.
- TDA/TCA/TAP = numerador compatível / denominador × 100. Estados devem somar o denominador.
- Taxas confrontadas com as oficiais, tolerância 0,02 p.p.; erro real observado inferior a 0,00000001 p.p.
- Bloquear séries incompletas, chaves repetidas, contagens negativas, denominador não positivo e ingressantes variáveis. Acumular antes de filtrar referência.
- Agregar por soma de numeradores/denominadores na mesma coorte/referência, nunca média simples ou soma de ingressantes através dos anos.
- Horizonte = referência − ingresso. Zero é o ano do ingresso; coorte 2015 em 2024 tem horizonte 9 e dez observações.

P1: 515 cursos, 41.889 ingressantes ajustados, 25.092 desistentes, 16.253 concluintes e 544 permanentes. Taxas 59,9012%, 38,8002% e 1,2987%. Maior aumento entre anos consecutivos: 2016, 16,7 p.p. O primeiro ano não tem comparação anterior. Diferença acumulada não é risco anual.

P2: rankings/áreas entre 283 cursos publicáveis, coorte 2015 e horizonte 9. Outras coortes ausentes. Atributos e localização são os do último ano da fonte, não necessariamente do ingresso.

P5: grau 2 = licenciatura, no mesmo subconjunto publicável. Enade 2025 ausente; proficiência não calculada. Populações de trajetória e Enade não formam funil individual.

## P3 e B2

Contratos locais Censo 2021–2024. Grão original: ano + IES + curso + dimensão + município. Somente dimensões 1 (presencial) e 2 (EAD municipal), UF 51; excluir Brasil/exterior. Grão público fixo: ano + rede + modalidade. Ausências nas contagens necessárias bloqueiam cálculo.

P3: soma QT_MAT; variação = (matrículas atuais / anteriores − 1) × 100, apenas anos consecutivos com base positiva. Matrículas de anos diferentes não são alunos únicos. Quatro anos não sustentam classificação robusta de outliers; variações descritivas. Evasão anual não calculada sem definição/denominador aprovado.

B2, privada: QT_MAT_FIES, QT_MAT_PROUNII e QT_MAT_PROUNIP, cada um dividido por QT_MAT do mesmo ano/recorte. Não somar benefícios nem presumir exclusividade. Participação não é efeito causal ou resultado individual. Associação com evasão pendente. Benefícios não podem exceder matrículas.

## P4

CPC 2023, edição única mais recente local anterior à referência 2024. Sem preencher lacunas com outros ciclos. Junção IES + curso, chave única na edição, mantendo contagem de cursos e denominador. 90 de 283 cursos publicáveis com conceito. Sem CPC não significa zero; inclui cursos fora do ciclo e sem conceito.

A edição cobre apenas as áreas avaliadas naquele ciclo. CPC é posterior ao ingresso e a parte dos desfechos, portanto não é exposição causal na entrada. Pearson descritivo não ponderado exige >=10 cursos completos e variância nas duas medidas. Sem p-valor ou ajuste multivariado; r observado ≈0,0452 antes de filtros. Segmentação não controla confundimento. Taxas por faixa usam numeradores/denominadores; coberturas por cursos e ingressantes são exibidas.

## B1

Oferta = soma QT_VG_TOTAL em presencial/dimensão 1 por ano/município. Vagas não são estudantes. Indicador futuro = vagas / população de 18–24 anos × 100. IBGE, cadastro completo e geometria ausentes: sem mapa, desertos ou zeros imputados. Compatibilidade temporal ainda precisa de validação.

## Proteção e filtros

Trajetória: ocultar toda a linha de curso quando qualquer estado positivo ou denominador for menor que 10. Omitir ingressantes originais/óbitos no curso. Proteção complementar exige resíduo zero ou >=10 entre total P1 e cursos divulgados em cada estado. P2/P4/P5 usam exclusivamente o MESMO subconjunto; não divulgar totais completos extras por rede, área, grau ou CPC.

Evolução P1: taxas a 0,1 p.p., sem contagens, denominadores intermediários ou óbitos anuais. Contrato restrito ao painel estadual de 515 cursos; não aplicar a filtros de curso. Novas margens ou cruzamentos com tabelas externas exigem revisão.

Censo: ocultar numerador de benefício positivo <10 e sua taxa, inclusive quando o complemento positivo for <10. Manter matrículas seguras; sem total de benefícios ou categoria sem benefícios. Matrículas pequenas bloqueiam dependentes e variações. Totais com parcela oculta ficam indisponíveis, sem somas parciais.

Filtros, gráficos, tabelas e downloads consomem somente snapshot protegido. Filtros de cursos em P1 não alteram o total/evolução estadual. CSV neutraliza fórmulas; XLSX inclui metadados. Proteção técnica não substitui revisão editorial para publicação externa.
