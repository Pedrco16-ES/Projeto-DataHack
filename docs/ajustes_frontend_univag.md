# Ajustes de frontend UNIVAG — 10/10/2026

Referências lidas: `PROMPT-FRONTEND-DASHBOARDS.md` e
`UNIVAG_Guia_Estilos_Dashboards.md`, disponibilizados na pasta Downloads.
Escopo escolhido: adaptar visual e usabilidade ao frontend existente em
Streamlit/Plotly e à apresentação HTML, mantendo a arquitetura atual.

## Implementado

- Estilos compartilhados em `components/univag.css`: paleta institucional,
  tipografia, cartões, foco visível, ajustes para telas estreitas e redução de movimento.
- Tema inicial Streamlit alinhado às cores UNIVAG.
- Filtros múltiplos validados e serializados na URL, com resumo do recorte.
  Valores inválidos e opções dependentes incompatíveis são descartados;
  limpar filtros permanece na tela atual. Seletores de ano e controles do
  simulador continuam com seu comportamento original.
- Gráficos cartesianos e roscas com alternativa tabular dos mesmos pontos;
  o mapa mantém sua tabela detalhada existente.
- Ausência numérica representada por travessão, distinta de zero; formatação
  brasileira nos números e separadores dos gráficos.
- Estado de carregamento, mensagem de erro com nova tentativa e orientação
  para recuperar buscas vazias.
- Link para pular ao conteúdo e atualização de cores no HTML e em seu gerador.

## Validação e limites

`python -m pytest tests/test_univag_frontend.py tests/test_step3.py -q`
passou com 12 testes, cobrindo as oito telas ativas, filtros e integrações.
Houve um aviso de depreciação interno do Streamlit/NumPy.

A execução de `tests/test_mvp.py` junto de `tests/test_step3.py` teve oito
aprovações e uma falha: o teste que percorre todas as páginas inclui a versão
legada `01_p1_trajetoria.py`, que exige o CSV ausente
`outputs/p1_trajetoria_coorte2015.csv`. As páginas da navegação atual usam o
snapshot público disponível.

Não foi realizada inspeção visual em navegador ou auditoria completa WCAG.
O HTML recebeu ajustes visuais; seus fluxos JavaScript existentes não foram
reescritos. O tema entregue permanece claro. Migração React/ECharts, autenticação
e contrato OpenAPI não fazem parte do escopo escolhido. Não foram inventadas
metas, comparações ou métricas para preencher componentes.
