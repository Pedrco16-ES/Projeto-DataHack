"""Gera o dashboard HTML interativo da Rota do Diploma com fidelidade visual ao layout de referência.

Design limpo, minimalista, moderno:
- Top banner com pergunta orientadora
- 4 cartões KPIs com números em destaque colorido
- Gráfico Donut "Funil do diploma" (Concluíram / Desistiram / Retidos)
- Gráfico de Linhas "Evolução da coorte 2015" (Concluiu, Desistiu, Retido)
- Controle deslizante (slider) interativo de anos (2015 a 2024) com reprodução automática (Play/Pause)
- Navegação fluida pelas 8 telas do desafio (Panorama, P1 a P5, B1 e B2)
- Filtros dinâmicos e proteção de células < 10.
"""

from pathlib import Path
import json
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
OUTPUTS_DIR = PROJECT_ROOT / "outputs"
ARTIFACT_DIR = Path(r"C:\Users\alunoti\.gemini\antigravity\brain\2f0bc1ce-a5ad-4159-9ad4-96500dbac519")

def load_data():
    p1 = pd.read_csv(OUTPUTS_DIR / "p1_trajetoria_coorte2015.csv").to_dict(orient="records")
    p2 = pd.read_csv(OUTPUTS_DIR / "p2_cursos_areas.csv").to_dict(orient="records")
    p3 = pd.read_csv(OUTPUTS_DIR / "p3_censo_rede_modalidade.csv").to_dict(orient="records")
    p4 = pd.read_csv(OUTPUTS_DIR / "p4_qualidade_cpc.csv").to_dict(orient="records")
    p5 = pd.read_csv(OUTPUTS_DIR / "p5_licenciaturas.csv").to_dict(orient="records")
    b1 = pd.read_csv(OUTPUTS_DIR / "b1_oferta_municipal.csv").to_dict(orient="records")
    b2 = pd.read_csv(OUTPUTS_DIR / "b2_financiamento.csv").to_dict(orient="records")
    return {
        "p1": p1,
        "p2": p2,
        "p3": p3,
        "p4": p4,
        "p5": p5,
        "b1": b1,
        "b2": b2,
    }

def generate_html(data):
    data_json = json.dumps(data, ensure_ascii=False)

    html = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Rota do Diploma · DataHack Univag 2026</title>
  <!-- Tailwind CSS via endpoint oficial -->
  <script src="https://www.gstatic.com/antigravity/web/dev/tailwindcss.min.js"></script>
  <!-- Chart.js para renderização de gráficos fluidos e elegantes -->
  <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.1/dist/chart.umd.min.js"></script>
  <style>
    body {{
      background-color: #F8FAFC;
      color: #0F172A;
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    }}
    .card-base {{
      background: #FFFFFF;
      border: 1px solid #E2E8F0;
      border-radius: 16px;
      box-shadow: 0 1px 3px rgba(0, 0, 0, 0.04), 0 1px 2px rgba(0, 0, 0, 0.02);
      transition: all 0.2s ease;
    }}
    .card-base:hover {{
      box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05), 0 2px 4px -1px rgba(0, 0, 0, 0.03);
    }}
    .tab-btn {{
      transition: all 0.15s ease-in-out;
      border-radius: 10px;
      font-size: 13px;
      font-weight: 600;
      color: #64748B;
    }}
    .tab-btn.active {{
      background-color: #2563EB !important;
      color: #FFFFFF !important;
      box-shadow: 0 2px 8px rgba(37, 99, 235, 0.25);
    }}
    .tab-btn:hover:not(.active) {{
      background-color: #F1F5F9;
      color: #0F172A;
    }}
    .custom-scroll::-webkit-scrollbar {{
      width: 6px;
      height: 6px;
    }}
    .custom-scroll::-webkit-scrollbar-thumb {{
      background: #CBD5E1;
      border-radius: 4px;
    }}
    input[type=range] {{
      accent-color: #2563EB;
    }}
  </style>
</head>
<body class="p-3 md:p-6 lg:p-8 flex flex-col min-h-screen">

  <!-- Header Superior e Seletor de Telas -->
  <header class="max-w-7xl mx-auto w-full mb-6">
    <div class="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-4 border-b border-slate-200">
      <div>
        <div class="flex items-center gap-2">
          <span class="bg-blue-100 text-blue-700 text-xs font-bold px-2.5 py-0.5 rounded-full">DataHack Univag 2026</span>
          <span class="text-xs text-slate-500 font-medium">Mato Grosso · Ensino Superior</span>
        </div>
        <h1 class="text-2xl font-extrabold text-slate-900 tracking-tight mt-1">Rota do Diploma</h1>
        <p class="text-xs text-slate-500">Trajetória, evasão, oferta regional e qualidade da educação superior em MT</p>
      </div>

      <div class="flex flex-wrap items-center gap-2">
        <span class="inline-flex items-center gap-1.5 text-xs font-semibold text-emerald-700 bg-emerald-50 border border-emerald-200 px-3 py-1.5 rounded-lg">
          <span class="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></span>
          Snapshots Aprovados (INEP / IBGE)
        </span>
        <button onclick="exportCurrentData()" class="inline-flex items-center gap-1.5 text-xs font-bold text-slate-700 bg-white border border-slate-300 hover:bg-slate-50 px-3 py-1.5 rounded-lg shadow-sm transition">
          <svg class="w-3.5 h-3.5 text-slate-600" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4"></path></svg>
          Exportar CSV
        </button>
      </div>
    </div>

    <!-- Barra de Navegação Horizontal das 8 Telas -->
    <nav class="flex items-center gap-1.5 overflow-x-auto custom-scroll py-2.5 mt-2">
      <button onclick="switchScreen('p1')" id="nav-p1" class="tab-btn active px-3.5 py-2 shrink-0">1. P1: Trajetória 2015</button>
      <button onclick="switchScreen('panorama')" id="nav-panorama" class="tab-btn px-3.5 py-2 shrink-0">2. Panorama Geral</button>
      <button onclick="switchScreen('p2')" id="nav-p2" class="tab-btn px-3.5 py-2 shrink-0">3. P2: Cursos & Áreas</button>
      <button onclick="switchScreen('p3')" id="nav-p3" class="tab-btn px-3.5 py-2 shrink-0">4. P3: Rede & Modalidade</button>
      <button onclick="switchScreen('p4')" id="nav-p4" class="tab-btn px-3.5 py-2 shrink-0">5. P4: Qualidade (CPC)</button>
      <button onclick="switchScreen('p5')" id="nav-p5" class="tab-btn px-3.5 py-2 shrink-0">6. P5: Licenciaturas</button>
      <button onclick="switchScreen('b1')" id="nav-b1" class="tab-btn px-3.5 py-2 shrink-0">7. B1: Desertos de Vagas</button>
      <button onclick="switchScreen('b2')" id="nav-b2" class="tab-btn px-3.5 py-2 shrink-0">8. B2: Financiamento</button>
    </nav>
  </header>

  <!-- Container de Conteúdo -->
  <main class="max-w-7xl mx-auto w-full flex-1">

    <!-- =========================================================================
         TELA P1: TRAJETÓRIA (Layout Fiel à Imagem de Referência)
         ========================================================================= -->
    <section id="screen-p1" class="space-y-6">

      <!-- Banner de Pergunta em Formato Pill -->
      <div class="bg-[#EFF6FF] border border-[#BFDBFE] text-[#1E3A8A] rounded-2xl px-5 py-3.5 text-sm md:text-base font-semibold shadow-sm flex items-center justify-between flex-wrap gap-2">
        <span>De cada 100 que entram numa graduação em MT, quantos chegam ao diploma, e em quais cursos a rota se perde?</span>
        <span class="text-xs bg-white text-blue-700 font-bold px-2.5 py-1 rounded-full border border-blue-200 shadow-2xs">Coorte 2015 Presencial MT</span>
      </div>

      <!-- 4 Cartões KPIs Iguais à Imagem -->
      <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">

        <!-- Card 1: Conclusão -->
        <div class="card-base p-5">
          <div class="text-xs font-medium text-slate-500">Taxa de conclusão</div>
          <div id="kpi-conclusao" class="text-3xl font-extrabold text-[#2563EB] tracking-tight mt-1.5">38,8</div>
          <div id="kpi-conclusao-sub" class="text-xs text-slate-400 mt-1">a cada 100 alunos · 2024</div>
        </div>

        <!-- Card 2: Desistência -->
        <div class="card-base p-5">
          <div class="text-xs font-medium text-slate-500">Taxa de desistência</div>
          <div id="kpi-desistencia" class="text-3xl font-extrabold text-[#EF4444] tracking-tight mt-1.5">60,2</div>
          <div id="kpi-desistencia-sub" class="text-xs text-slate-400 mt-1">a cada 100 alunos · 2024</div>
        </div>

        <!-- Card 3: Retidos / Cursando -->
        <div class="card-base p-5">
          <div class="text-xs font-medium text-slate-500">Retidos / cursando</div>
          <div id="kpi-retidos" class="text-3xl font-extrabold text-[#0D9488] tracking-tight mt-1.5">1,0</div>
          <div id="kpi-retidos-sub" class="text-xs text-slate-400 mt-1">a cada 100 alunos · 2024</div>
        </div>

        <!-- Card 4: Ano Crítico de Perda -->
        <div class="card-base p-5">
          <div class="text-xs font-medium text-slate-500">Ano crítico de perda</div>
          <div class="text-3xl font-extrabold text-[#EA580C] tracking-tight mt-1.5">2016</div>
          <div class="text-xs text-slate-400 mt-1">maior salto de desistentes na coorte 2015 (+16,96 p.p.)</div>
        </div>

      </div>

      <!-- Barra de Controle Interativa de Ano / Timeline Slider -->
      <div class="card-base p-4 bg-white flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div class="flex items-center gap-3">
          <button id="btn-play-pause" onclick="togglePlayTimeline()" class="bg-blue-600 hover:bg-blue-700 text-white p-2.5 rounded-xl shadow transition">
            <svg id="icon-play" class="w-4 h-4" fill="currentColor" viewBox="0 0 24 24"><path d="M8 5v14l11-7z"/></svg>
            <svg id="icon-pause" class="w-4 h-4 hidden" fill="currentColor" viewBox="0 0 24 24"><path d="M6 19h4V5H6v14zm8-14v14h4V5h-4z"/></svg>
          </button>
          <div>
            <div class="text-xs font-bold text-slate-800">Simulador da Linha do Tempo (2015 a 2024)</div>
            <div class="text-xs text-slate-400">Arraste para visualizar a migração dos 100 alunos ano a ano</div>
          </div>
        </div>

        <div class="flex items-center gap-3 flex-1 max-w-md">
          <span class="text-xs font-bold text-slate-500">2015</span>
          <input type="range" id="year-slider" min="2015" max="2024" value="2024" step="1" oninput="updateYear(this.value)" class="w-full cursor-pointer h-2 bg-slate-200 rounded-lg">
          <span class="text-xs font-bold text-slate-500">2024</span>
          <span id="label-selected-year" class="bg-blue-50 border border-blue-200 text-blue-700 text-xs font-extrabold px-3 py-1 rounded-lg">2024</span>
        </div>
      </div>

      <!-- Dois Cartões Principais (Donut + Linhas) -->
      <div class="grid grid-cols-1 lg:grid-cols-12 gap-6">

        <!-- Card da Esquerda: Funil do Diploma (Donut Chart) -->
        <div class="card-base p-6 lg:col-span-5 flex flex-col">
          <div>
            <h3 class="text-base font-bold text-slate-900">Funil do diploma</h3>
            <p id="donut-subtitle" class="text-xs text-slate-400 mt-0.5">Os 100 ingressantes, em 2024</p>
          </div>

          <div class="relative flex-1 flex items-center justify-center my-6" style="min-height: 250px;">
            <canvas id="chart-funil-donut"></canvas>
            <!-- Centro do Donut -->
            <div class="absolute inset-0 flex flex-col items-center justify-center pointer-events-none">
              <span id="donut-center-num" class="text-2xl font-black text-slate-800">100</span>
              <span class="text-[10px] uppercase font-bold text-slate-400">Ingressantes</span>
            </div>
          </div>

          <!-- Legenda do Donut -->
          <div class="flex items-center justify-center gap-5 text-xs font-semibold pt-2 border-t border-slate-100">
            <div class="flex items-center gap-1.5">
              <span class="w-3.5 h-3.5 rounded-sm bg-[#2563EB]"></span>
              <span class="text-slate-700">Concluíram</span>
            </div>
            <div class="flex items-center gap-1.5">
              <span class="w-3.5 h-3.5 rounded-sm bg-[#EF4444]"></span>
              <span class="text-slate-700">Desistiram</span>
            </div>
            <div class="flex items-center gap-1.5">
              <span class="w-3.5 h-3.5 rounded-sm bg-[#94A3B8]"></span>
              <span class="text-slate-700">Retidos</span>
            </div>
          </div>
        </div>

        <!-- Card da Direita: Evolução da coorte 2015 (Line Chart) -->
        <div class="card-base p-6 lg:col-span-7 flex flex-col">
          <div>
            <h3 class="text-base font-bold text-slate-900">Evolução da coorte 2015</h3>
            <p class="text-xs text-slate-400 mt-0.5">Por 100 ingressantes, ano a ano</p>
          </div>

          <div class="flex-1 my-4" style="min-height: 250px;">
            <canvas id="chart-evolucao-linhas"></canvas>
          </div>

          <!-- Legenda do Line Chart -->
          <div class="flex items-center justify-center gap-6 text-xs font-semibold pt-2 border-t border-slate-100">
            <div class="flex items-center gap-1.5">
              <span class="w-5 h-1 bg-[#2563EB] rounded"></span>
              <span class="text-slate-700">Concluiu</span>
            </div>
            <div class="flex items-center gap-1.5">
              <span class="w-5 h-1 bg-[#EF4444] rounded"></span>
              <span class="text-slate-700">Desistiu</span>
            </div>
            <div class="flex items-center gap-1.5">
              <span class="w-5 h-1 bg-[#94A3B8] rounded"></span>
              <span class="text-slate-700">Retido</span>
            </div>
          </div>
        </div>

      </div>

      <!-- Tabela Anual Detalhada da Coorte -->
      <div class="card-base p-6">
        <h3 class="text-sm font-bold text-slate-800 mb-3">Tabela de Balanço da Trajetória (INEP · Mato Grosso)</h3>
        <div class="overflow-x-auto custom-scroll">
          <table class="w-full text-left text-xs border-collapse">
            <thead>
              <tr class="bg-slate-50 text-slate-600 border-b border-slate-200">
                <th class="p-2.5">Ano Ref.</th>
                <th class="p-2.5">Ano de Curso</th>
                <th class="p-2.5 text-right">Ingressantes</th>
                <th class="p-2.5 text-right text-blue-600">Concluiu (TCA)</th>
                <th class="p-2.5 text-right text-red-600">Desistiu (TDA)</th>
                <th class="p-2.5 text-right text-amber-600">Salto Anual (Δ TDA)</th>
                <th class="p-2.5 text-right text-slate-600">Retido (TAP)</th>
                <th class="p-2.5 text-center">Balanço (100%)</th>
              </tr>
            </thead>
            <tbody id="p1-full-table-body" class="divide-y divide-slate-100"></tbody>
          </table>
        </div>
      </div>

    </section>

    <!-- =========================================================================
         TELA PANORAMA: RESUMO EXECUTIVO INTEGRADO
         ========================================================================= -->
    <section id="screen-panorama" class="hidden space-y-6">
      <div class="bg-gradient-to-r from-slate-900 to-blue-900 text-white rounded-2xl p-6 shadow-sm">
        <div class="text-xs uppercase font-bold text-blue-300">Panorama Integrado</div>
        <h2 class="text-2xl font-black mt-1">Raio-X do Ensino Superior em Mato Grosso</h2>
        <p class="text-xs text-blue-100 max-w-2xl mt-1">Síntese executiva articulando as 5 perguntas obrigatórias e 2 bônus com indicadores estaduais oficiais.</p>
      </div>

      <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">

        <div onclick="switchScreen('p1')" class="card-base p-5 cursor-pointer hover:border-blue-500">
          <div class="text-xs font-bold text-blue-600 uppercase">P1 · Trajetória</div>
          <div class="font-bold text-slate-800 text-base mt-1">Quanto da turma desiste?</div>
          <div class="text-2xl font-black text-red-600 mt-2">60,2% Desistência</div>
          <p class="text-xs text-slate-500 mt-1">38,8% formados em 10 anos. Maior salto de perda no 2º ano de curso.</p>
        </div>

        <div onclick="switchScreen('p2')" class="card-base p-5 cursor-pointer hover:border-blue-500">
          <div class="text-xs font-bold text-blue-600 uppercase">P2 · Cursos & Áreas</div>
          <div class="font-bold text-slate-800 text-base mt-1">Onde a rota mais se perde?</div>
          <div class="text-2xl font-black text-orange-600 mt-2">TI & Engenharias > 70%</div>
          <p class="text-xs text-slate-500 mt-1">Eng. Ambiental (87,4%) e Matemática (84,3%) no topo. Medicina com 85,2% de formatura.</p>
        </div>

        <div onclick="switchScreen('p3')" class="card-base p-5 cursor-pointer hover:border-blue-500">
          <div class="text-xs font-bold text-blue-600 uppercase">P3 · Rede & Modalidade</div>
          <div class="font-bold text-slate-800 text-base mt-1">Evolução e Anos Atípicos</div>
          <div class="text-2xl font-black text-blue-600 mt-2">+57% EAD Privado</div>
          <p class="text-xs text-slate-500 mt-1">2022 foi o ano atípico de pico de desvinculações no pós-pandemia (> 44 mil em MT).</p>
        </div>

        <div onclick="switchScreen('p4')" class="card-base p-5 cursor-pointer hover:border-blue-500">
          <div class="text-xs font-bold text-blue-600 uppercase">P4 · Qualidade (CPC)</div>
          <div class="font-bold text-slate-800 text-base mt-1">Qualidade retém alunos?</div>
          <div class="text-2xl font-black text-emerald-600 mt-2">R = -0,42 (Moderada)</div>
          <p class="text-xs text-slate-500 mt-1">Cursos CPC 4 e 5 perdem 38% a menos. Efeito de seleção vestibular e infraestrutura.</p>
        </div>

        <div onclick="switchScreen('p5')" class="card-base p-5 cursor-pointer hover:border-blue-500">
          <div class="text-xs font-bold text-blue-600 uppercase">P5 · Licenciaturas</div>
          <div class="font-bold text-slate-800 text-base mt-1">O funil dos professores</div>
          <div class="text-2xl font-black text-red-600 mt-2">57,5% Evasão Docente</div>
          <p class="text-xs text-slate-500 mt-1">Menos de 25% dos concluintes em Exatas atingem o padrão satisfatório no Enade 2025.</p>
        </div>

        <div onclick="switchScreen('b1')" class="card-base p-5 cursor-pointer hover:border-blue-500">
          <div class="text-xs font-bold text-purple-600 uppercase">B1 & B2 · Bônus Oficiais</div>
          <div class="font-bold text-slate-800 text-base mt-1">Desertos & Financiamento</div>
          <div class="text-2xl font-black text-purple-600 mt-2">80 Municípios sem Oferta</div>
          <p class="text-xs text-slate-500 mt-1">FIES e ProUni reduzem a desvinculação anual privada em 15,3 p.p. a favor da permanência.</p>
        </div>

      </div>
    </section>

    <!-- =========================================================================
         TELA P2: ONDE A ROTA MAIS SE PERDE
         ========================================================================= -->
    <section id="screen-p2" class="hidden space-y-6">
      <div class="bg-[#EFF6FF] border border-[#BFDBFE] text-[#1E3A8A] rounded-2xl p-4 text-sm font-semibold">
        <b>P2:</b> Quais cursos e áreas possuem maior e menor desistência? Como comparar as coortes?
      </div>

      <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div class="card-base p-5">
          <h3 class="text-sm font-bold text-red-600 mb-3">Top 5 Cursos com MAIOR Desistência (TDA %)</h3>
          <div style="height: 230px;"><canvas id="chart-p2-top-maior"></canvas></div>
        </div>
        <div class="card-base p-5">
          <h3 class="text-sm font-bold text-emerald-600 mb-3">Top 5 Cursos com MENOR Desistência (TDA %)</h3>
          <div style="height: 230px;"><canvas id="chart-p2-top-menor"></canvas></div>
        </div>
      </div>

      <div class="card-base p-5">
        <div class="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-3 mb-3">
          <h3 class="text-sm font-bold text-slate-800">Cursos Ofertados em MT (Rótulo CINE)</h3>
          <input type="text" id="p2-search-input" oninput="renderP2Table()" placeholder="Buscar curso ou grande área..." class="px-3 py-1.5 border border-slate-300 rounded-lg text-xs w-full sm:w-64">
        </div>
        <div class="overflow-x-auto custom-scroll max-h-80">
          <table class="w-full text-left text-xs border-collapse">
            <thead class="sticky top-0 bg-slate-100 text-slate-700">
              <tr>
                <th class="p-2">Curso</th>
                <th class="p-2">Grande Área CINE</th>
                <th class="p-2">Grau</th>
                <th class="p-2 text-right">Ingressantes</th>
                <th class="p-2 text-right">Desistência (TDA)</th>
                <th class="p-2 text-right">Conclusão (TCA)</th>
              </tr>
            </thead>
            <tbody id="p2-table-body" class="divide-y divide-slate-100"></tbody>
          </table>
        </div>
      </div>
    </section>

    <!-- =========================================================================
         TELA P3: REDE E MODALIDADE
         ========================================================================= -->
    <section id="screen-p3" class="hidden space-y-6">
      <div class="bg-[#EFF6FF] border border-[#BFDBFE] text-[#1E3A8A] rounded-2xl p-4 text-sm font-semibold">
        <b>P3:</b> Como se comportam as matrículas e a evasão anual entre 2021 e 2024? Existe algum ano atípico?
      </div>

      <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div class="card-base p-5">
          <h3 class="text-sm font-bold text-slate-800 mb-3">Evolução das Matrículas por Segmento (2021 a 2024)</h3>
          <div style="height: 240px;"><canvas id="chart-p3-lines"></canvas></div>
        </div>
        <div class="card-base p-5">
          <h3 class="text-sm font-bold text-slate-800 mb-3">Taxa de Desvinculação Censitária (%)</h3>
          <div style="height: 240px;"><canvas id="chart-p3-bars"></canvas></div>
        </div>
      </div>

      <div class="bg-amber-50 border border-amber-200 text-amber-900 rounded-xl p-4 text-xs leading-relaxed">
        <b>Ano Atípico Identificado (2022):</b> Registrou pico histórico de desvinculações (> 44.000) com retorno presencial e renegociação pós-pandemia. Ressalva: desvinculação censitária não é evasão longitudinal.
      </div>
    </section>

    <!-- =========================================================================
         TELA P4: QUALIDADE (CPC)
         ========================================================================= -->
    <section id="screen-p4" class="hidden space-y-6">
      <div class="bg-[#EFF6FF] border border-[#BFDBFE] text-[#1E3A8A] rounded-2xl p-4 text-sm font-semibold">
        <b>P4:</b> Cursos com CPC mais alto apresentam menor desistência? O que mais pode explicar essa relação?
      </div>

      <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div class="card-base p-5">
          <h3 class="text-sm font-bold text-slate-800 mb-3">Dispersão: CPC Contínuo vs Desistência (R = -0,42)</h3>
          <div style="height: 240px;"><canvas id="chart-p4-scatter-canvas"></canvas></div>
        </div>
        <div class="card-base p-5">
          <h3 class="text-sm font-bold text-slate-800 mb-3">Desistência Média por Faixa de CPC (%)</h3>
          <div style="height: 240px;"><canvas id="chart-p4-faixas-canvas"></canvas></div>
        </div>
      </div>
    </section>

    <!-- =========================================================================
         TELA P5: LICENCIATURAS
         ========================================================================= -->
    <section id="screen-p5" class="hidden space-y-6">
      <div class="bg-[#EFF6FF] border border-[#BFDBFE] text-[#1E3A8A] rounded-2xl p-4 text-sm font-semibold">
        <b>P5:</b> Quanto desiste nas licenciaturas e quanto dos concluintes é proficiente no Enade 2025?
      </div>

      <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div class="card-base p-5">
          <h3 class="text-sm font-bold text-red-600 mb-3">1º Gargalo: Desistência na Trajetória (TDA %)</h3>
          <div style="height: 240px;"><canvas id="chart-p5-tda-canvas"></canvas></div>
        </div>
        <div class="card-base p-5">
          <h3 class="text-sm font-bold text-blue-600 mb-3">2º Gargalo: % Proficiente no Enade 2025</h3>
          <div style="height: 240px;"><canvas id="chart-p5-enade-canvas"></canvas></div>
        </div>
      </div>
    </section>

    <!-- =========================================================================
         TELA B1: DESERTOS DE ENSINO SUPERIOR
         ========================================================================= -->
    <section id="screen-b1" class="hidden space-y-6">
      <div class="bg-[#F3E8FF] border border-[#E9D5FF] text-[#581C87] rounded-2xl p-4 text-sm font-semibold">
        <b>B1:</b> Quantas vagas presenciais existem por 100 jovens de 18 a 24 anos em cada município? Onde não há oferta?
      </div>

      <div class="card-base p-5">
        <h3 class="text-sm font-bold text-slate-800 mb-3">Top Polos Regionais (Vagas presenciais por 100 jovens)</h3>
        <div style="height: 240px;"><canvas id="chart-b1-polos-canvas"></canvas></div>
      </div>

      <div class="card-base p-5">
        <div class="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-3 mb-3">
          <h3 class="text-sm font-bold text-slate-800">Situação da Oferta nos 141 Municípios de MT</h3>
          <input type="text" id="b1-search-input" oninput="renderB1Table()" placeholder="Buscar município..." class="px-3 py-1.5 border border-slate-300 rounded-lg text-xs w-full sm:w-64">
        </div>
        <div class="overflow-x-auto custom-scroll max-h-80">
          <table class="w-full text-left text-xs border-collapse">
            <thead class="sticky top-0 bg-slate-100 text-slate-700">
              <tr>
                <th class="p-2">Código IBGE</th>
                <th class="p-2">Município</th>
                <th class="p-2 text-right">População 18–24a</th>
                <th class="p-2 text-right">Vagas Presenciais</th>
                <th class="p-2 text-right">Vagas / 100 Jovens</th>
                <th class="p-2">Situação</th>
              </tr>
            </thead>
            <tbody id="b1-table-body" class="divide-y divide-slate-100"></tbody>
          </table>
        </div>
      </div>
    </section>

    <!-- =========================================================================
         TELA B2: FINANCIAMENTO E PERMANÊNCIA
         ========================================================================= -->
    <section id="screen-b2" class="hidden space-y-6">
      <div class="bg-[#F3E8FF] border border-[#E9D5FF] text-[#581C87] rounded-2xl p-4 text-sm font-semibold">
        <b>B2:</b> Qual é o peso de FIES e ProUni na rede privada entre 2021 e 2024? Cursos com mais financiados evadem menos?
      </div>

      <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div class="card-base p-5">
          <h3 class="text-sm font-bold text-slate-800 mb-3">Evolução do FIES & ProUni nos Ingressantes Privados (%)</h3>
          <div style="height: 230px;"><canvas id="chart-b2-evol-canvas"></canvas></div>
        </div>
        <div class="card-base p-5">
          <h3 class="text-sm font-bold text-slate-800 mb-3">Taxa de Desvinculação Anual: Financiados vs Não Financiados (%)</h3>
          <div style="height: 230px;"><canvas id="chart-b2-comp-canvas"></canvas></div>
        </div>
      </div>
    </section>

  </main>

  <!-- Script Lógico & Interatividade Completa -->
  <script>
    const DATA = {data_json};
    let currentScreen = 'p1';
    let donutChartInstance = null;
    let lineChartInstance = null;
    let playInterval = null;

    // Alternar entre Telas
    function switchScreen(screenId) {{
      currentScreen = screenId;
      document.querySelectorAll('main > section').forEach(sec => sec.classList.add('hidden'));
      document.querySelectorAll('.tab-btn').forEach(btn => btn.classList.remove('active'));

      const targetSec = document.getElementById('screen-' + screenId);
      const targetBtn = document.getElementById('nav-' + screenId);
      if (targetSec) targetSec.classList.remove('hidden');
      if (targetBtn) targetBtn.classList.add('active');

      window.scrollTo({{ top: 0, behavior: 'smooth' }});
    }}

    // Atualização Dinâmica do Ano no P1
    function updateYear(yearVal) {{
      const year = parseInt(yearVal);
      document.getElementById('label-selected-year').innerText = year;
      document.getElementById('year-slider').value = year;

      const row = DATA.p1.find(r => r.nu_ano_referencia === year) || DATA.p1[DATA.p1.length - 1];

      // Atualiza KPIs
      document.getElementById('kpi-conclusao').innerText = row.tca.toFixed(1).replace('.', ',');
      document.getElementById('kpi-conclusao-sub').innerText = `a cada 100 alunos · ${{year}}`;

      document.getElementById('kpi-desistencia').innerText = row.tda.toFixed(1).replace('.', ',');
      document.getElementById('kpi-desistencia-sub').innerText = `a cada 100 alunos · ${{year}}`;

      document.getElementById('kpi-retidos').innerText = row.tap.toFixed(1).replace('.', ',');
      document.getElementById('kpi-retidos-sub').innerText = `a cada 100 alunos · ${{year}}`;

      document.getElementById('donut-subtitle').innerText = `Os 100 ingressantes, em ${{year}}`;
      document.getElementById('donut-center-num').innerText = year;

      // Atualiza Donut
      if (donutChartInstance) {{
        donutChartInstance.data.datasets[0].data = [row.tca, row.tda, row.tap];
        donutChartInstance.update();
      }}
    }}

    // Play/Pause na Timeline
    function togglePlayTimeline() {{
      const playIcon = document.getElementById('icon-play');
      const pauseIcon = document.getElementById('icon-pause');

      if (playInterval) {{
        clearInterval(playInterval);
        playInterval = null;
        playIcon.classList.remove('hidden');
        pauseIcon.classList.add('hidden');
      }} else {{
        playIcon.classList.add('hidden');
        pauseIcon.classList.remove('hidden');
        playInterval = setInterval(() => {{
          const slider = document.getElementById('year-slider');
          let current = parseInt(slider.value);
          current = current >= 2024 ? 2015 : current + 1;
          updateYear(current);
        }}, 900);
      }}
    }}

    // Exportação CSV
    function exportCurrentData() {{
      let activeData = DATA.p1;
      let filename = 'p1_trajetoria_coorte2015.csv';
      if (currentScreen === 'p2') {{ activeData = DATA.p2; filename = 'p2_cursos_areas.csv'; }}
      else if (currentScreen === 'p3') {{ activeData = DATA.p3; filename = 'p3_censo_rede.csv'; }}
      else if (currentScreen === 'p4') {{ activeData = DATA.p4; filename = 'p4_qualidade_cpc.csv'; }}
      else if (currentScreen === 'p5') {{ activeData = DATA.p5; filename = 'p5_licenciaturas.csv'; }}
      else if (currentScreen === 'b1') {{ activeData = DATA.b1; filename = 'b1_desertos_mt.csv'; }}
      else if (currentScreen === 'b2') {{ activeData = DATA.b2; filename = 'b2_financiamento.csv'; }}

      const headers = Object.keys(activeData[0]);
      const csv = [headers.join(',')];
      activeData.forEach(r => {{
        const vals = headers.map(h => {{
          const v = r[h];
          if (typeof v === 'number' && v < 10 && h.toLowerCase().includes('ingressante')) return '"< 10"';
          return JSON.stringify(v ?? '');
        }});
        csv.push(vals.join(','));
      }});
      const blob = new Blob([csv.join('\\n')], {{ type: 'text/csv;charset=utf-8;' }});
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = filename;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
    }}

    // Renderiza Tabelas
    function renderTables() {{
      // Tabela P1
      const p1Body = document.getElementById('p1-full-table-body');
      p1Body.innerHTML = DATA.p1.map(r => `
        <tr class="hover:bg-slate-50">
          <td class="p-2 font-bold">${{r.nu_ano_referencia}}</td>
          <td class="p-2">${{r.ano_curso}}</td>
          <td class="p-2 text-right">${{r.qt_ingressante.toLocaleString('pt-BR')}}</td>
          <td class="p-2 text-right font-bold text-blue-600">${{r.tca.toFixed(1)}}%</td>
          <td class="p-2 text-right font-bold text-red-600">${{r.tda.toFixed(1)}}%</td>
          <td class="p-2 text-right font-bold text-orange-600">+${{r.delta_tda.toFixed(1)}} p.p.</td>
          <td class="p-2 text-right font-semibold text-slate-500">${{r.tap.toFixed(1)}}%</td>
          <td class="p-2 text-center text-emerald-700 font-bold">100%</td>
        </tr>
      `).join('');

      renderP2Table();
      renderB1Table();
    }}

    function renderP2Table() {{
      const term = (document.getElementById('p2-search-input')?.value || '').toLowerCase();
      const p2Body = document.getElementById('p2-table-body');
      const filtered = DATA.p2.filter(r => r.NO_CINE_ROTULO.toLowerCase().includes(term) || r.NO_CINE_AREA_GERAL.toLowerCase().includes(term));
      p2Body.innerHTML = filtered.map(r => `
        <tr class="hover:bg-slate-50">
          <td class="p-2 font-semibold text-slate-900">${{r.NO_CINE_ROTULO}}</td>
          <td class="p-2 text-slate-500">${{r.NO_CINE_AREA_GERAL}}</td>
          <td class="p-2">${{r.grau_academico}}</td>
          <td class="p-2 text-right">${{r.qt_ingressante < 10 ? '< 10' : r.qt_ingressante.toLocaleString('pt-BR')}}</td>
          <td class="p-2 text-right font-bold ${{r.tda >= 70 ? 'text-red-600' : 'text-slate-800'}}">${{r.tda.toFixed(1)}}%</td>
          <td class="p-2 text-right font-bold text-emerald-600">${{r.tca.toFixed(1)}}%</td>
        </tr>
      `).join('');
    }}

    function renderB1Table() {{
      const term = (document.getElementById('b1-search-input')?.value || '').toLowerCase();
      const b1Body = document.getElementById('b1-table-body');
      const filtered = DATA.b1.filter(r => r.no_municipio.toLowerCase().includes(term));
      b1Body.innerHTML = filtered.map(r => `
        <tr class="hover:bg-slate-50">
          <td class="p-2 text-slate-500">${{r.co_municipio}}</td>
          <td class="p-2 font-bold text-slate-800">${{r.no_municipio}}</td>
          <td class="p-2 text-right">${{r.pop_18_24.toLocaleString('pt-BR')}}</td>
          <td class="p-2 text-right font-bold">${{r.vagas_presenciais.toLocaleString('pt-BR')}}</td>
          <td class="p-2 text-right font-black ${{r.vagas_presenciais === 0 ? 'text-red-500' : 'text-blue-600'}}">
            ${{r.vagas_por_100_jovens.toFixed(2)}}
          </td>
          <td class="p-2">
            <span class="px-2 py-0.5 rounded text-[10px] font-bold ${{r.vagas_presenciais === 0 ? 'bg-red-100 text-red-700' : (r.vagas_por_100_jovens >= 20 ? 'bg-emerald-100 text-emerald-800' : 'bg-amber-100 text-amber-800')}}">
              ${{r.classificacao}}
            </span>
          </td>
        </tr>
      `).join('');
    }}

    // Inicialização dos Gráficos com Chart.js
    function initAllCharts() {{
      const yearsP1 = DATA.p1.map(r => r.nu_ano_referencia);
      const tcaVals = DATA.p1.map(r => r.tca);
      const tdaVals = DATA.p1.map(r => r.tda);
      const tapVals = DATA.p1.map(r => r.tap);

      // Donut Chart P1 (Fiel ao mock)
      const lastP1 = DATA.p1[DATA.p1.length - 1];
      const donutCtx = document.getElementById('chart-funil-donut').getContext('2d');
      donutChartInstance = new Chart(donutCtx, {{
        type: 'doughnut',
        data: {{
          labels: ['Concluíram', 'Desistiram', 'Retidos'],
          datasets: [{{
            data: [lastP1.tca, lastP1.tda, lastP1.tap],
            backgroundColor: ['#2563EB', '#EF4444', '#94A3B8'],
            borderWidth: 3,
            borderColor: '#FFFFFF',
            hoverOffset: 4
          }}]
        }},
        options: {{
          responsive: true,
          maintainAspectRatio: false,
          cutout: '68%',
          plugins: {{ legend: {{ display: false }} }}
        }}
      }});

      // Line Chart P1 (Fiel ao mock com marcadores redondos)
      const lineCtx = document.getElementById('chart-evolucao-linhas').getContext('2d');
      lineChartInstance = new Chart(lineCtx, {{
        type: 'line',
        data: {{
          labels: yearsP1,
          datasets: [
            {{
              label: 'Concluiu',
              data: tcaVals,
              borderColor: '#2563EB',
              backgroundColor: '#2563EB',
              pointRadius: 4,
              borderWidth: 2.5,
              tension: 0.2
            }},
            {{
              label: 'Desistiu',
              data: tdaVals,
              borderColor: '#EF4444',
              backgroundColor: '#EF4444',
              pointRadius: 4,
              borderWidth: 2.5,
              tension: 0.2
            }},
            {{
              label: 'Retido',
              data: tapVals,
              borderColor: '#94A3B8',
              backgroundColor: '#94A3B8',
              pointRadius: 4,
              borderWidth: 2.5,
              tension: 0.2
            }}
          ]
        }},
        options: {{
          responsive: true,
          maintainAspectRatio: false,
          scales: {{
            y: {{
              min: 0,
              max: 100,
              ticks: {{ stepSize: 10 }},
              grid: {{ color: '#F1F5F9' }},
              title: {{ display: true, text: 'por 100 ingressantes', font: {{ size: 11, weight: 'bold' }}, color: '#64748B' }}
            }},
            x: {{ grid: {{ color: '#F8FAFC' }} }}
          }},
          plugins: {{ legend: {{ display: false }} }}
        }}
      }});

      // P2 Rankings
      const sigP2 = DATA.p2.filter(r => r.qt_ingressante >= 50);
      const topMaior = [...sigP2].sort((a,b) => b.tda - a.tda).slice(0, 5);
      const topMenor = [...sigP2].sort((a,b) => a.tda - b.tda).slice(0, 5);

      new Chart(document.getElementById('chart-p2-top-maior'), {{
        type: 'bar',
        data: {{
          labels: topMaior.map(r => r.NO_CINE_ROTULO),
          datasets: [{{ data: topMaior.map(r => r.tda), backgroundColor: '#EF4444', borderRadius: 6 }}]
        }},
        options: {{ indexAxis: 'y', responsive: true, maintainAspectRatio: false, plugins: {{ legend: {{ display: false }} }} }}
      }});

      new Chart(document.getElementById('chart-p2-top-menor'), {{
        type: 'bar',
        data: {{
          labels: topMenor.map(r => r.NO_CINE_ROTULO),
          datasets: [{{ data: topMenor.map(r => r.tda), backgroundColor: '#10B981', borderRadius: 6 }}]
        }},
        options: {{ indexAxis: 'y', responsive: true, maintainAspectRatio: false, plugins: {{ legend: {{ display: false }} }} }}
      }});

      // P3 Linhas & Barras
      const p3Years = [2021, 2022, 2023, 2024];
      const p3Segs = [...new Set(DATA.p3.map(r => r.segmento))];
      const p3Colors = ['#1E3A8A', '#2563EB', '#F59E0B', '#EC4899'];

      new Chart(document.getElementById('chart-p3-lines'), {{
        type: 'line',
        data: {{
          labels: p3Years,
          datasets: p3Segs.map((s, i) => ({{
            label: s,
            data: p3Years.map(y => DATA.p3.find(r => r.nu_ano_censo === y && r.segmento === s)?.qt_mat || 0),
            borderColor: p3Colors[i],
            borderWidth: 2.5,
            pointRadius: 3
          }}))
        }},
        options: {{ responsive: true, maintainAspectRatio: false }}
      }});

      new Chart(document.getElementById('chart-p3-bars'), {{
        type: 'bar',
        data: {{
          labels: p3Years,
          datasets: p3Segs.map((s, i) => ({{
            label: s,
            data: p3Years.map(y => DATA.p3.find(r => r.nu_ano_censo === y && r.segmento === s)?.pct_desvinculacao || 0),
            backgroundColor: p3Colors[i]
          }}))
        }},
        options: {{ responsive: true, maintainAspectRatio: false }}
      }});

      // P4 Scatter & Faixas
      const p4Evaluated = DATA.p4.filter(r => r.cpc_continuo !== null && !isNaN(r.cpc_continuo));
      new Chart(document.getElementById('chart-p4-scatter-canvas'), {{
        type: 'scatter',
        data: {{
          datasets: [{{
            label: 'Cursos',
            data: p4Evaluated.map(r => ({{ x: r.cpc_continuo, y: r.tda }})),
            backgroundColor: '#2563EB'
          }}]
        }},
        options: {{ responsive: true, maintainAspectRatio: false }}
      }});

      const faixas = ['1', '2', '3', '4', '5', 'Sem CPC'];
      const faixasTDA = faixas.map(f => {{
        const sub = DATA.p4.filter(r => String(r.faixa_cpc) === f);
        if (!sub.length) return 0;
        return (sub.reduce((acc, r) => acc + (r.tda * r.qt_ingressante), 0) / sub.reduce((acc, r) => acc + r.qt_ingressante, 0)).toFixed(1);
      }});
      new Chart(document.getElementById('chart-p4-faixas-canvas'), {{
        type: 'bar',
        data: {{
          labels: faixas,
          datasets: [{{ data: faixasTDA, backgroundColor: ['#EF4444', '#F59E0B', '#3B82F6', '#10B981', '#8B5CF6', '#94A3B8'], borderRadius: 6 }}]
        }},
        options: {{ responsive: true, maintainAspectRatio: false, plugins: {{ legend: {{ display: false }} }} }}
      }});

      // P5 Licenciaturas
      new Chart(document.getElementById('chart-p5-tda-canvas'), {{
        type: 'bar',
        data: {{
          labels: DATA.p5.map(r => r.NO_CINE_ROTULO),
          datasets: [{{ data: DATA.p5.map(r => r.tda), backgroundColor: '#EF4444', borderRadius: 6 }}]
        }},
        options: {{ indexAxis: 'y', responsive: true, maintainAspectRatio: false, plugins: {{ legend: {{ display: false }} }} }}
      }});

      new Chart(document.getElementById('chart-p5-enade-canvas'), {{
        type: 'bar',
        data: {{
          labels: DATA.p5.map(r => r.NO_CINE_ROTULO),
          datasets: [{{ data: DATA.p5.map(r => r.enade_proficiente_pct), backgroundColor: '#2563EB', borderRadius: 6 }}]
        }},
        options: {{ indexAxis: 'y', responsive: true, maintainAspectRatio: false, plugins: {{ legend: {{ display: false }} }} }}
      }});

      // B1 Polos
      const topB1 = [...DATA.b1].filter(r => r.vagas_presenciais > 0).sort((a,b) => b.vagas_por_100_jovens - a.vagas_por_100_jovens).slice(0, 10);
      new Chart(document.getElementById('chart-b1-polos-canvas'), {{
        type: 'bar',
        data: {{
          labels: topB1.map(r => r.no_municipio),
          datasets: [{{ data: topB1.map(r => r.vagas_por_100_jovens), backgroundColor: '#2563EB', borderRadius: 6 }}]
        }},
        options: {{ indexAxis: 'y', responsive: true, maintainAspectRatio: false, plugins: {{ legend: {{ display: false }} }} }}
      }});

      // B2 Financiamento
      new Chart(document.getElementById('chart-b2-evol-canvas'), {{
        type: 'line',
        data: {{
          labels: DATA.b2.map(r => r.nu_ano_censo),
          datasets: [
            {{ label: '% FIES', data: DATA.b2.map(r => r.pct_fies), borderColor: '#2563EB', borderWidth: 2.5 }},
            {{ label: '% ProUni', data: DATA.b2.map(r => r.pct_prouni), borderColor: '#8B5CF6', borderWidth: 2.5 }},
            {{ label: '% Total', data: DATA.b2.map(r => r.pct_apoio_total), borderColor: '#10B981', borderDash: [4, 4], borderWidth: 2.5 }}
          ]
        }},
        options: {{ responsive: true, maintainAspectRatio: false }}
      }});

      new Chart(document.getElementById('chart-b2-comp-canvas'), {{
        type: 'bar',
        data: {{
          labels: DATA.b2.map(r => r.nu_ano_censo),
          datasets: [
            {{ label: 'Financiados (Desvinculação %)', data: DATA.b2.map(r => r.taxa_desvinculacao_financiados), backgroundColor: '#10B981', borderRadius: 6 }},
            {{ label: 'Não Financiados (Desvinculação %)', data: DATA.b2.map(r => r.taxa_desvinculacao_nao_financiados), backgroundColor: '#EF4444', borderRadius: 6 }}
          ]
        }},
        options: {{ responsive: true, maintainAspectRatio: false }}
      }});
    }}

    document.addEventListener('DOMContentLoaded', () => {{
      renderTables();
      initAllCharts();
    }});
  </script>
</body>
</html>
"""
    return html

def main():
    data = load_data()
    html_content = generate_html(data)

    dashboard_path = PROJECT_ROOT / "dashboard.html"
    outputs_html = OUTPUTS_DIR / "dashboard.html"
    artifact_path = ARTIFACT_DIR / "dashboard.html"

    dashboard_path.write_text(html_content, encoding="utf-8")
    outputs_html.write_text(html_content, encoding="utf-8")
    artifact_path.write_text(html_content, encoding="utf-8")

    print(f"Novo HTML Dashboard V2 gerado com sucesso em:")
    print(f" - {dashboard_path}")
    print(f" - {outputs_html}")
    print(f" - {artifact_path}")

if __name__ == "__main__":
    main()
