# Apresentação e contingência

1. Execute `iniciar_mvp.cmd` e abra `http://localhost:8501`. Use tela cheia e zoom 90–100%.
2. Panorama/P1: explique a coorte 2015, 59,9% desistência, 38,8% conclusão, 1,3% permanência e denominador ajustado. Maior incremento em 2016.
3. P2/P4: demonstre filtro por área e cobertura publicável. CPC indica associação, não causa.
4. P3/B2: compare redes/modalidades e benefícios separadamente, com matrículas do mesmo ano como denominador.
5. P5/B1: explicite fontes ausentes; pendências não são zero.

## Sem servidor ou internet

Gere `outputs/apresentacao.html` com `venv/Scripts/python.exe scripts/export_presentation.py`. Abra diretamente no navegador: não depende de servidor, CDN ou banco e contém somente resultados protegidos.

PDF: Ctrl+P → Salvar como PDF → paisagem → gráficos de fundo habilitados. As seções têm quebras de página; revise paginação. Vídeo: grave a navegação com a ferramenta de captura já instalada; não mostre ambiente, credenciais ou administração. PDF/vídeo não foram produzidos automaticamente.

Baixe gráficos PNG pela barra Plotly e tabelas CSV/XLSX no app. Snapshot/apresentação são ignorados no Git; copie apenas artefatos protegidos aprovados para a máquina da apresentação.
