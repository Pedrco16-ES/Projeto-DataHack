# Respostas às cinco perguntas e aos dois bônus

O Streamlit e `dashboard.html` usam o snapshot público validado em
`outputs/public_snapshot.json`. Os textos de resposta são calculados por
`src/analytics/answers.py`; não há números editoriais fixos no gerador HTML.

- P1: respondida para coorte 2015 presencial de MT, até 2024.
- P2: rankings de cursos/áreas publicáveis; seis coortes em horizonte estadual comum. Não há comparação por curso entre coortes.
- P3: parcial. Matrículas por rede/modalidade; evasão apenas estadual. Maior variação observada não prova ano estatisticamente atípico.
- P4: parcial. Associação descritiva CPC/desistência; outras explicações não foram estimadas.
- P5: respondida nos recortes publicáveis. Trajetória e Enade não são a mesma população; 11 de 84 cursos presenciais no Enade.
- B1: 141 municípios em 2022; distinguir ausência de registro de oferta de registro com zero vagas. Ambos aparecem na listagem de zero vagas.
- B2: parcial. Peso dos benefícios disponível; associação com evasão por curso indisponível.

Para regenerar o HTML offline, sem banco ou alteração das bases:

```powershell
.\venv\Scripts\python.exe -B scripts/generate_unified_dashboard_html.py
```

O arquivo contém a biblioteca de gráficos, sem carregamento por CDN. A apresentação
`outputs/apresentacao.html` é um artefato separado; a entrega revisada é `dashboard.html`.
O Streamlit mantém seus filtros; a síntese inicial é explicitamente identificada
como referente ao recorte completo e não muda com eles.

Reversão das alterações de interface desta revisão: restaurar os três arquivos
correspondentes em `.audit-backup-fidelidade/` para `components/dashboard.py`,
`dashboard.html` e `scripts/generate_unified_dashboard_html.py`. A cópia preserva
as alterações locais que já existiam antes desta revisão. As bases não foram alteradas.
