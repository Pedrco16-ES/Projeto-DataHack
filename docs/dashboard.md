# Dashboard MVP — oito telas

**Atualização do passo 3:** P2 inclui seis coortes em horizonte comum; P3 inclui evasão estadual oficial independente dos filtros; P5 inclui Enade protegido com filtros próprios; B1 inclui mapa e vagas por 100 jovens de 2022 nos 141 municípios. Snapshot schema 2. Consulte [integração e limites atuais](integracao_passo3.md). A tabela abaixo registra a entrega inicial, anterior a essa ampliação.

Execute `venv/Scripts/python.exe -m streamlit run app.py`. Navegação lateral, fundo claro, gráficos Plotly com zoom/seleção e download PNG, filtros e Limpar filtros. Tabelas com busca literal, ordenação, paginação, CSV/XLSX.

| Tela | Entrega | Limitação |
| --- | --- | --- |
| Panorama | Indicadores, sete cartões, trajetória/matrículas | Populações distintas identificadas |
| P1 | Barra 100%, evolução, maior aumento, cursos | Filtros no detalhamento publicável |
| P2 | Rankings, áreas, filtros, denominadores | Apenas coorte 2015, horizonte 9 |
| P3 | Matrículas, redes/modalidades, variação | Evasão anual e outliers pendentes |
| P4 | CPC, dispersão, correlação, faixas/cobertura | Edição 2023; associação descritiva |
| P5 | Trajetória de licenciaturas | Enade 2025 ausente |
| B1 | Oferta municipal/ano, ranking | IBGE/cadastro/geometria pendentes |
| B2 | FIES e ProUni separados | Associação com evasão pendente |

Snapshot em `outputs/public_snapshot.json`. Atualizar dados validados limpa cache de 5 minutos e recarrega, sem ingestão. Administração local separada em `admin.py`; sem dados brutos na interface pública.

Leitor remoto opcional usa `marts.public_snapshots` exclusivamente com PUBLIC_DATABASE_URL. Falha/ausência de banco usa snapshot local. Esquema e conta públicos não configurados: demonstração entregue em modo offline. Oito telas verificadas por Streamlit AppTest; sem inspeção visual automatizada em navegador.
