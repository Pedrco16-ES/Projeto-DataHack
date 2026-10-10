# Passo 3 — integração local concluída

Atualização em 10/10/2026. Este documento substitui as pendências de integração registradas nos relatos anteriores dos passos 1 e 2 e do MVP inicial.

- **P2:** seis coortes, 2015–2020, comparadas no horizonte de quatro anos desde o ingresso (cinco observações). Totais estaduais presenciais em taxas arredondadas, sem contagens intermediárias. O ranking continua na coorte 2015 até 2024, com 283 cursos publicáveis, e seus filtros não alteram a comparação estadual.
- **P3:** evasão do sistema publicada pelo INEP para MT: 13,7%, 16,7%, 17,9% e 18,5% nas transições 2020–2021 até 2023–2024. Painel independente dos filtros de matrículas. A fonte não fornece rede/modalidade/curso nem denominadores numéricos.
- **P5:** 11 de 84 cursos presenciais de licenciatura publicáveis no Enade 2025. São 339 participantes e 180 no padrão 1 ou acima: 53,1%, ponderados por participantes. Cursos com dados incompletos ou células positivas menores que 10, inclusive o complemento, foram omitidos antes dos filtros. Inscritos e totais de participantes omitidos não são divulgados. Trajetória e Enade têm filtros e populações separados; não formam um funil individual.
- **B1:** 141 municípios na malha IBGE 2022, 397.671 residentes de 18–24 anos e 84.508 vagas presenciais registradas em 2022. Há 99 municípios sem registro de oferta presencial no recorte validado. Zero é oferta registrada nula; não demonstra inexistência de acesso. Denominador ausente/zero produz indicador indisponível. O mapa usa geometria no snapshot e fundo sem serviço externo de mapas.
- **B2:** mantidos FIES e ProUni separadamente. A taxa estadual não pode ser atribuída a cursos para criar uma correlação com financiamento; esse resultado continua indisponível.

P1 permanece em 41.889 ingressantes ajustados: 59,9% desistência, 38,8% conclusão e 1,3% permanência. Os 283 cursos publicáveis da trajetória são os mesmos do MVP anterior.

## Artefatos e rastreabilidade

`src/analytics/extensions.py` verifica as fontes pelo manifesto e os recortes das coortes pelos hashes dos relatórios, reconcilia taxas e populações e monta as novas séries. `outputs/public_snapshot.json` usa schema 2, inclui geometria e proveniência e é consumido pela interface. CSV/XLSX usam somente dados públicos já protegidos. `outputs/apresentacao.html` inclui as novas análises e funciona offline.

O snapshot anterior é preservado em `outputs/public_snapshot.previous.json`; reversão exige código compatível com a versão do snapshot. Nenhuma migration, conta, credencial ou carga remota foi alterada. A entrega local não depende de Supabase nem de rede.

## Verificações essenciais

Cinco testes aprovados em 7,67 s: consistência dos novos resultados e recusa de célula pequena mesmo com hash recalculado; independência dos filtros do Enade; execução das oito telas e limpeza dos filtros; integridade/fallback offline; exportações seguras. A primeira execução concluiu três testes, mas a limpeza de temporários externos falhou por permissão do Windows; a execução final usou diretório temporário exclusivo dentro do projeto e terminou com código zero.

Sem agentes adicionais, instalações ou repetição da bateria de banco. A verificação das telas usou Streamlit AppTest; não equivale a inspeção visual do mapa em navegador.

```powershell
$step3TestDir = Join-Path (Get-Location) ('data/processed/step3-tests-' + [guid]::NewGuid().ToString('N'))
.\venv\Scripts\python.exe -B -m pytest tests/test_step3.py tests/test_mvp.py::test_dashboard_eight_pages_and_filter_reset tests/test_mvp.py::test_real_snapshot_integrity_and_offline_fallback tests/test_mvp.py::test_public_exports_neutralize_formulas_and_preserve_metadata -q -p no:cacheprovider --basetemp $step3TestDir
```

Para visualizar, abra `iniciar_mvp.cmd`; se o aplicativo já estiver aberto, clique em **Atualizar dados validados**. Próximos passos do plano: integração pública no Supabase, refinamento visual e validação final.
