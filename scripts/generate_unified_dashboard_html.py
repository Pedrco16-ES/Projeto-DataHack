"""Gera o dashboard HTML em página única com todos os KPIs (P1 a P5, B1 e B2),
o banner de pergunta, o simulador do funil e o gráfico de barras dos cursos onde a rota se perde.
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
  <!-- Tailwind CSS via allowlisted CDN -->
  <script src="https://www.gstatic.com/antigravity/web/dev/tailwindcss.min.js"></script>
  <!-- Chart.js para renderização de gráficos de alta fidelidade -->
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
      box-shadow: 0 1px 3px rgba(0, 0, 0, 0.03), 0 1px 2px rgba(0, 0, 0, 0.02);
      transition: all 0.2s ease;
    }}
    .card-base:hover {{
      box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05), 0 2px 4px -1px rgba(0, 0, 0, 0.03);
    }}
    .kpi-badge {{
      display: inline-block;
      font-size: 10px;
      font-weight: 800;
      text-transform: uppercase;
      letter-spacing: 0.5px;
      padding: 2px 8px;
      border-radius: 9999px;
    }}
    .filter-btn {{
      font-size: 11px;
      font-weight: 700;
      padding: 6px 14px;
      border-radius: 8px;
      border: 1px solid #E2E8F0;
      background: #FFFFFF;
      color: #64748B;
      transition: all 0.15s ease;
    }}
    .filter-btn.active {{
      background: #2563EB;
      color: #FFFFFF;
      border-color: #2563EB;
      box-shadow: 0 2px 4px rgba(37, 99, 235, 0.2);
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
<body class="p-3 sm:p-5 md:p-8 min-h-screen flex flex-col">

  <!-- ================= TOPBAR BRANDING ================= -->
  <header class="max-w-7xl mx-auto w-full mb-6">
    <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-4 border-b border-slate-200">
      <div>
        <div class="flex items-center gap-2">
          <span class="bg-blue-100 text-blue-800 text-xs font-black px-2.5 py-0.5 rounded-full">DataHack Univag 2026</span>
          <span class="text-xs font-semibold text-slate-500">Mato Grosso · Ensino Superior</span>
        </div>
        <h1 class="text-2xl sm:text-3xl font-black text-slate-900 tracking-tight mt-1">Rota do Diploma — Dashboard Executivo</h1>
        <p class="text-xs text-slate-500 mt-0.5">Análise integrada das 5 perguntas obrigatórias e 2 bônus em visualização única</p>
      </div>

      <div class="flex items-center gap-2.5 self-start sm:self-auto">
        <span class="inline-flex items-center gap-1.5 text-xs font-bold text-emerald-700 bg-emerald-50 border border-emerald-200 px-3 py-1.5 rounded-xl shadow-2xs">
          <span class="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></span>
          Bases Oficiais INEP & IBGE
        </span>
        <button onclick="downloadMasterCSV()" class="inline-flex items-center gap-1.5 text-xs font-extrabold text-white bg-blue-600 hover:bg-blue-700 px-3.5 py-2 rounded-xl shadow transition">
          <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4"></path></svg>
          Exportar CSV
        </button>
      </div>
    </div>
  </header>

  <main class="max-w-7xl mx-auto w-full space-y-6 flex-1">

    <!-- ================= 1. BANNER COM A PERGUNTA CENTRAL ================= -->
    <div class="bg-[#EFF6FF] border border-[#BFDBFE] text-[#1E3A8A] rounded-2xl px-5 py-3.5 text-sm md:text-base font-bold shadow-sm flex items-center justify-between flex-wrap gap-2">
      <span>De cada 100 que entram numa graduação em MT, quantos chegam ao diploma, e em quais cursos a rota se perde?</span>
      <span class="text-xs bg-white text-blue-700 font-extrabold px-3 py-1 rounded-full border border-blue-200">Coorte 2015 Presencial MT</span>
    </div>

    <!-- ================= 2. OS 4 KPIS DA PERGUNTA P1 (IDÊNTICOS AO MOCKUP) ================= -->
    <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">

      <div class="card-base p-5">
        <div class="text-xs font-medium text-slate-500">Taxa de conclusão</div>
        <div id="kpi-conclusao" class="text-3xl font-black text-[#2563EB] tracking-tight mt-1.5">38,8</div>
        <div id="kpi-conclusao-sub" class="text-xs text-slate-400 mt-1">a cada 100 alunos · 2024</div>
      </div>

      <div class="card-base p-5">
        <div class="text-xs font-medium text-slate-500">Taxa de desistência</div>
        <div id="kpi-desistencia" class="text-3xl font-black text-[#EF4444] tracking-tight mt-1.5">60,2</div>
        <div id="kpi-desistencia-sub" class="text-xs text-slate-400 mt-1">a cada 100 alunos · 2024</div>
      </div>

      <div class="card-base p-5">
        <div class="text-xs font-medium text-slate-500">Retidos / cursando</div>
        <div id="kpi-retidos" class="text-3xl font-black text-[#0D9488] tracking-tight mt-1.5">1,0</div>
        <div id="kpi-retidos-sub" class="text-xs text-slate-400 mt-1">a cada 100 alunos · 2024</div>
      </div>

      <div class="card-base p-5">
        <div class="text-xs font-medium text-slate-500">Ano crítico de perda</div>
        <div class="text-3xl font-black text-[#EA580C] tracking-tight mt-1.5">2016</div>
        <div class="text-xs text-slate-400 mt-1">maior salto de desistentes na coorte 2015 (+16,96 p.p.)</div>
      </div>

    </div>

    <!-- ================= 3. CONTROLE DESLIZANTE DE ANO (SLIDER COM PLAY/PAUSE) ================= -->
    <div class="card-base p-4 bg-white flex flex-col sm:flex-row sm:items-center justify-between gap-4">
      <div class="flex items-center gap-3">
        <button id="btn-play-pause" onclick="togglePlayTimeline()" class="bg-blue-600 hover:bg-blue-700 text-white p-2.5 rounded-xl shadow transition">
          <svg id="icon-play" class="w-4 h-4" fill="currentColor" viewBox="0 0 24 24"><path d="M8 5v14l11-7z"/></svg>
          <svg id="icon-pause" class="w-4 h-4 hidden" fill="currentColor" viewBox="0 0 24 24"><path d="M6 19h4V5H6v14zm8-14v14h4V5h-4z"/></svg>
        </button>
        <div>
          <div class="text-xs font-extrabold text-slate-800">Simulador Dinâmico da Turma (2015 a 2024)</div>
          <div class="text-xs text-slate-400">Arraste o slider para acompanhar a evasão e conclusão a cada ano</div>
        </div>
      </div>

      <div class="flex items-center gap-3 flex-1 max-w-md">
        <span class="text-xs font-bold text-slate-500">2015</span>
        <input type="range" id="year-slider" min="2015" max="2024" value="2024" step="1" oninput="updateYear(this.value)" class="w-full cursor-pointer h-2 bg-slate-200 rounded-lg">
        <span class="text-xs font-bold text-slate-500">2024</span>
        <span id="label-selected-year" class="bg-blue-50 border border-blue-200 text-blue-700 text-xs font-black px-3 py-1 rounded-lg">2024</span>
      </div>
    </div>

    <!-- ================= 4. FUNIL DO DIPLOMA (DONUT) + EVOLUÇÃO (LINHAS) ================= -->
    <div class="grid grid-cols-1 lg:grid-cols-12 gap-6">

      <!-- Donut: Funil do Diploma -->
      <div class="card-base p-6 lg:col-span-5 flex flex-col justify-between">
        <div>
          <h3 class="text-base font-bold text-slate-900">Funil do diploma</h3>
          <p id="donut-subtitle" class="text-xs text-slate-400 mt-0.5">Os 100 ingressantes, em 2024</p>
        </div>

        <div class="relative flex items-center justify-center my-4" style="height: 250px;">
          <canvas id="chart-funil-donut"></canvas>
          <div class="absolute inset-0 flex flex-col items-center justify-center pointer-events-none">
            <span id="donut-center-num" class="text-2xl font-black text-slate-800">2024</span>
            <span class="text-[10px] uppercase font-bold text-slate-400">Ano Ref.</span>
          </div>
        </div>

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

      <!-- Linhas: Evolução da Coorte -->
      <div class="card-base p-6 lg:col-span-7 flex flex-col justify-between">
        <div>
          <h3 class="text-base font-bold text-slate-900">Evolução da coorte 2015</h3>
          <p class="text-xs text-slate-400 mt-0.5">Por 100 ingressantes, ano a ano</p>
        </div>

        <div class="my-4" style="height: 250px;">
          <canvas id="chart-evolucao-linhas"></canvas>
        </div>

        <div class="flex items-center justify-center gap-6 text-xs font-semibold pt-2 border-t border-slate-100">
          <div class="flex items-center gap-1.5">
            <span class="w-4 h-1 bg-[#2563EB] rounded"></span>
            <span class="text-slate-700">Concluiu</span>
          </div>
          <div class="flex items-center gap-1.5">
            <span class="w-4 h-1 bg-[#EF4444] rounded"></span>
            <span class="text-slate-700">Desistiu</span>
          </div>
          <div class="flex items-center gap-1.5">
            <span class="w-4 h-1 bg-[#94A3B8] rounded"></span>
            <span class="text-slate-700">Retido</span>
          </div>
        </div>
      </div>

    </div>

    <!-- ================= 5. GRÁFICO DE BARRAS: EM QUAIS CURSOS A ROTA SE PERDE? ================= -->
    <div class="card-base p-6">
      <div class="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-5">
        <div>
          <h3 class="text-lg font-black text-slate-900 flex items-center gap-2">
            <span>📊</span> Em quais cursos a rota mais se perde? (Desistência Acumulada em MT)
          </h3>
          <p class="text-xs text-slate-500 mt-0.5">Taxa de desistência acumulada (%) nos cursos de graduação de Mato Grosso (Coorte 2015 acompanhada até 2024)</p>
        </div>

        <!-- Filtros Rápidos do Gráfico de Barras -->
        <div class="flex items-center gap-1.5 flex-wrap">
          <button onclick="setCourseFilter('criticos')" id="btn-filter-criticos" class="filter-btn active">🔴 Cursos Críticos (> 70% perda)</button>
          <button onclick="setCourseFilter('menor')" id="btn-filter-menor" class="filter-btn">🟢 Maior Retenção (Menor perda)</button>
          <button onclick="setCourseFilter('areas')" id="btn-filter-areas" class="filter-btn">🏛️ Por Grande Área CINE</button>
          <button onclick="setCourseFilter('todos')" id="btn-filter-todos" class="filter-btn">📋 Ver Todos</button>
        </div>
      </div>

      <!-- Canvas do Gráfico de Barras dos Cursos -->
      <div class="relative" style="min-height: 380px;">
        <canvas id="chart-cursos-barras"></canvas>
      </div>

      <div class="grid grid-cols-1 md:grid-cols-3 gap-3 mt-4 pt-4 border-t border-slate-100 text-xs">
        <div class="p-3 bg-red-50 text-red-900 rounded-xl border border-red-200">
          <b>Maior Evasão:</b> <b>Engenharia Ambiental (87,4%)</b>, <b>Matemática (84,3%)</b> e <b>Química (82,5%)</b>.
        </div>
        <div class="p-3 bg-emerald-50 text-emerald-900 rounded-xl border border-emerald-200">
          <b>Maior Conclusão:</b> <b>Medicina (14,8% perda / 85,2% conclusão)</b> e <b>Odontologia (33,7% perda)</b>.
        </div>
        <div class="p-3 bg-blue-50 text-blue-900 rounded-xl border border-blue-200">
          <b>Área com Maior Perda:</b> <b>Computação e TIC (71,9%)</b> e <b>Engenharias (68,5%)</b>.
        </div>
      </div>
    </div>

    <!-- ================= 6. GRADE DOS KPIS DE TODAS AS DEMAIS PERGUNTAS (P2 A P5, B1 E B2) ================= -->
    <div>
      <div class="flex items-center justify-between mb-3">
        <h3 class="text-base font-black text-slate-900 flex items-center gap-2">
          <span>🎯</span> Indicadores Chave das Perguntas P1 a P5 e Bônus
        </h3>
        <span class="text-xs text-slate-500 font-semibold">Respostas oficiais do desafio</span>
      </div>

      <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">

        <!-- KPI P1 -->
        <div class="card-base p-4 border-l-4 border-blue-600">
          <div class="flex justify-between items-center mb-1">
            <span class="kpi-badge bg-blue-100 text-blue-800">P1 · Obrigatória</span>
            <span class="text-[11px] text-slate-400 font-bold">2015–2024</span>
          </div>
          <div class="text-xs font-semibold text-slate-600">Quanto da turma desiste?</div>
          <div class="text-2xl font-black text-red-600 mt-1">60,2% Desistiram</div>
          <div class="text-xs text-emerald-600 font-bold mt-0.5">38,8% Concluíram · 1% Retidos</div>
          <div class="text-[11px] text-slate-500 mt-2 pt-2 border-t border-slate-100">
            Maior salto no <b>2º ano (2016)</b> com <b>+16,96 p.p.</b>
          </div>
        </div>

        <!-- KPI P2 -->
        <div class="card-base p-4 border-l-4 border-red-500">
          <div class="flex justify-between items-center mb-1">
            <span class="kpi-badge bg-red-100 text-red-800">P2 · Obrigatória</span>
            <span class="text-[11px] text-slate-400 font-bold">Trajetória MT</span>
          </div>
          <div class="text-xs font-semibold text-slate-600">Onde a rota mais se perde?</div>
          <div class="text-2xl font-black text-red-600 mt-1">TI & Eng. > 70%</div>
          <div class="text-xs text-slate-600 font-bold mt-0.5">Eng. Ambiental 87,4% · Mat. 84,3%</div>
          <div class="text-[11px] text-slate-500 mt-2 pt-2 border-t border-slate-100">
            <b>Medicina</b> retém <b>85,2%</b> dos ingressantes.
          </div>
        </div>

        <!-- KPI P3 -->
        <div class="card-base p-4 border-l-4 border-indigo-600">
          <div class="flex justify-between items-center mb-1">
            <span class="kpi-badge bg-indigo-100 text-indigo-800">P3 · Obrigatória</span>
            <span class="text-[11px] text-slate-400 font-bold">Censo 2021–24</span>
          </div>
          <div class="text-xs font-semibold text-slate-600">Pública x Privada, Pres. x EAD</div>
          <div class="text-2xl font-black text-indigo-700 mt-1">+57,1% EAD Priv.</div>
          <div class="text-xs text-amber-700 font-bold mt-0.5">2022: Ano Atípico (> 44k desv.)</div>
          <div class="text-[11px] text-slate-500 mt-2 pt-2 border-t border-slate-100">
            Presencial privado recuou <b>-5,0%</b> no mesmo período.
          </div>
        </div>

        <!-- KPI P4 -->
        <div class="card-base p-4 border-l-4 border-emerald-600">
          <div class="flex justify-between items-center mb-1">
            <span class="kpi-badge bg-emerald-100 text-emerald-800">P4 · Obrigatória</span>
            <span class="text-[11px] text-slate-400 font-bold">CPC 2021–23</span>
          </div>
          <div class="text-xs font-semibold text-slate-600">Qualidade retém? (CPC)</div>
          <div class="text-2xl font-black text-emerald-700 mt-1">R = -0,42</div>
          <div class="text-xs text-emerald-700 font-bold mt-0.5">CPC 4 e 5: 38% menor perda</div>
          <div class="text-[11px] text-slate-500 mt-2 pt-2 border-t border-slate-100">
            Associação moderada; forte efeito de seleção vestibular.
          </div>
        </div>

        <!-- KPI P5 -->
        <div class="card-base p-4 border-l-4 border-amber-500">
          <div class="flex justify-between items-center mb-1">
            <span class="kpi-badge bg-amber-100 text-amber-800">P5 · Obrigatória</span>
            <span class="text-[11px] text-slate-400 font-bold">Enade 2025</span>
          </div>
          <div class="text-xs font-semibold text-slate-600">O funil das licenciaturas</div>
          <div class="text-2xl font-black text-amber-700 mt-1">57,5% Desistem</div>
          <div class="text-xs text-red-600 font-bold mt-0.5">&lt; 25% Proficientes em Exatas</div>
          <div class="text-[11px] text-slate-500 mt-2 pt-2 border-t border-slate-100">
            Duplo funil crítico na formação docente em MT.
          </div>
        </div>

        <!-- KPI B1 -->
        <div class="card-base p-4 border-l-4 border-purple-600">
          <div class="flex justify-between items-center mb-1">
            <span class="kpi-badge bg-purple-100 text-purple-800">B1 · Bônus</span>
            <span class="text-[11px] text-slate-400 font-bold">Censo x IBGE</span>
          </div>
          <div class="text-xs font-semibold text-slate-600">Desertos de Ensino Superior</div>
          <div class="text-2xl font-black text-purple-700 mt-1">60,3% Deserto</div>
          <div class="text-xs text-purple-700 font-bold mt-0.5">~80 municípios sem vaga pres.</div>
          <div class="text-[11px] text-slate-500 mt-2 pt-2 border-t border-slate-100">
            Média MT: 15,2 vagas / 100 jovens (Cuiabá lidera: 27,7).
          </div>
        </div>

        <!-- KPI B2 -->
        <div class="card-base p-4 border-l-4 border-teal-600 sm:col-span-2 lg:col-span-2">
          <div class="flex justify-between items-center mb-1">
            <span class="kpi-badge bg-teal-100 text-teal-800">B2 · Bônus</span>
            <span class="text-[11px] text-slate-400 font-bold">Rede Privada 2021–24</span>
          </div>
          <div class="text-xs font-semibold text-slate-600">Financiamento (FIES & ProUni)</div>
          <div class="text-2xl font-black text-teal-700 mt-1">-15,3 p.p. Desvinculação</div>
          <div class="text-xs text-teal-700 font-bold mt-0.5">8,8% em financiados vs 24,1% não financiados</div>
          <div class="text-[11px] text-slate-500 mt-2 pt-2 border-t border-slate-100">
            Apoio financeiro atua como fortíssimo escudo de retenção estudantil.
          </div>
        </div>

      </div>
    </div>

    <!-- ================= 7. TABELA ANALÍTICA DE CURSOS E MUNICÍPIOS ================= -->
    <div class="card-base p-6">
      <div class="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-3 mb-4">
        <div>
          <h3 class="text-base font-black text-slate-900">Detalhamento dos Cursos Ofertados em Mato Grosso</h3>
          <p class="text-xs text-slate-500">Consulte taxas de evasão e conclusão por curso (Células &lt; 10 suprimidas)</p>
        </div>
        <input type="text" id="master-search-input" oninput="renderMasterTable()" placeholder="Buscar curso ou área..." class="px-3 py-1.5 border border-slate-300 rounded-lg text-xs w-full sm:w-64">
      </div>

      <div class="overflow-x-auto custom-scroll max-h-80">
        <table class="w-full text-left text-xs border-collapse">
          <thead class="sticky top-0 bg-slate-100 text-slate-700">
            <tr>
              <th class="p-2.5">Curso (Rótulo CINE)</th>
              <th class="p-2.5">Grande Área</th>
              <th class="p-2.5">Grau Acadêmico</th>
              <th class="p-2.5 text-right">Ingressantes 2015</th>
              <th class="p-2.5 text-right text-red-600 font-bold">Desistência (TDA)</th>
              <th class="p-2.5 text-right text-blue-600 font-bold">Conclusão (TCA)</th>
              <th class="p-2.5 text-right text-slate-600">Retidos (TAP)</th>
            </tr>
          </thead>
          <tbody id="master-table-body" class="divide-y divide-slate-100"></tbody>
        </table>
      </div>
    </div>

  </main>

  <footer class="max-w-7xl mx-auto w-full mt-8 pt-4 border-t border-slate-200 text-center text-xs text-slate-400">
    Rota do Diploma · DataHack Univag 2026 · Fontes Oficiais: INEP (Trajetória, Censo Superior, CPC, Enade) e IBGE (Censo 2022).
  </footer>

  <!-- ================= SCRIPTS JS & CHART.JS ================= -->
  <script>
    const DATA = {data_json};
    let donutChart = null;
    let lineChart = null;
    let coursesBarChart = null;
    let playTimer = null;
    let currentCourseFilter = 'criticos';

    // Atualiza o simulador do ano
    function updateYear(yVal) {{
      const year = parseInt(yVal);
      document.getElementById('label-selected-year').innerText = year;
      document.getElementById('year-slider').value = year;

      const row = DATA.p1.find(r => r.nu_ano_referencia === year) || DATA.p1[DATA.p1.length - 1];

      document.getElementById('kpi-conclusao').innerText = row.tca.toFixed(1).replace('.', ',');
      document.getElementById('kpi-conclusao-sub').innerText = `a cada 100 alunos · ${{year}}`;

      document.getElementById('kpi-desistencia').innerText = row.tda.toFixed(1).replace('.', ',');
      document.getElementById('kpi-desistencia-sub').innerText = `a cada 100 alunos · ${{year}}`;

      document.getElementById('kpi-retidos').innerText = row.tap.toFixed(1).replace('.', ',');
      document.getElementById('kpi-retidos-sub').innerText = `a cada 100 alunos · ${{year}}`;

      document.getElementById('donut-subtitle').innerText = `Os 100 ingressantes, em ${{year}}`;
      document.getElementById('donut-center-num').innerText = year;

      if (donutChart) {{
        donutChart.data.datasets[0].data = [row.tca, row.tda, row.tap];
        donutChart.update();
      }}
    }}

    function togglePlayTimeline() {{
      const pIcon = document.getElementById('icon-play');
      const pauseIcon = document.getElementById('icon-pause');

      if (playTimer) {{
        clearInterval(playTimer);
        playTimer = null;
        pIcon.classList.remove('hidden');
        pauseIcon.classList.add('hidden');
      }} else {{
        pIcon.classList.add('hidden');
        pauseIcon.classList.remove('hidden');
        playTimer = setInterval(() => {{
          const sl = document.getElementById('year-slider');
          let cur = parseInt(sl.value);
          cur = cur >= 2024 ? 2015 : cur + 1;
          updateYear(cur);
        }}, 900);
      }}
    }}

    // Filtros rápidos do gráfico de barras dos cursos
    function setCourseFilter(mode) {{
      currentCourseFilter = mode;
      document.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
      const activeBtn = document.getElementById('btn-filter-' + mode);
      if (activeBtn) activeBtn.classList.add('active');
      renderCoursesBarChart();
    }}

    function renderCoursesBarChart() {{
      const sig = DATA.p2.filter(r => r.qt_ingressante >= 40);
      let items = [];

      if (currentCourseFilter === 'criticos') {{
        items = [...sig].sort((a,b) => b.tda - a.tda).slice(0, 10);
      }} else if (currentCourseFilter === 'menor') {{
        items = [...sig].sort((a,b) => a.tda - b.tda).slice(0, 10);
      }} else if (currentCourseFilter === 'areas') {{
        // Agrupa por grande área CINE
        const areaMap = {{}};
        DATA.p2.forEach(r => {{
          if (!areaMap[r.NO_CINE_AREA_GERAL]) areaMap[r.NO_CINE_AREA_GERAL] = {{ ing: 0, sumTda: 0 }};
          areaMap[r.NO_CINE_AREA_GERAL].ing += r.qt_ingressante;
          areaMap[r.NO_CINE_AREA_GERAL].sumTda += (r.tda * r.qt_ingressante);
        }});
        items = Object.keys(areaMap).map(k => ({{
          NO_CINE_ROTULO: k,
          tda: areaMap[k].sumTda / areaMap[k].ing
        }})).sort((a,b) => b.tda - a.tda);
      }} else {{
        items = [...sig].sort((a,b) => b.tda - a.tda).slice(0, 20);
      }}

      const labels = items.map(r => r.NO_CINE_ROTULO);
      const dataVals = items.map(r => parseFloat(r.tda.toFixed(1)));
      const colors = dataVals.map(v => v >= 70 ? '#EF4444' : (v <= 45 ? '#10B981' : '#F59E0B'));

      if (coursesBarChart) {{
        coursesBarChart.data.labels = labels;
        coursesBarChart.data.datasets[0].data = dataVals;
        coursesBarChart.data.datasets[0].backgroundColor = colors;
        coursesBarChart.update();
      }} else {{
        const ctx = document.getElementById('chart-cursos-barras').getContext('2d');
        coursesBarChart = new Chart(ctx, {{
          type: 'bar',
          data: {{
            labels: labels,
            datasets: [{{
              label: 'Desistência Acumulada (%)',
              data: dataVals,
              backgroundColor: colors,
              borderRadius: 6
            }}]
          }},
          options: {{
            indexAxis: 'y',
            responsive: true,
            maintainAspectRatio: false,
            scales: {{
              x: {{ max: 100, ticks: {{ callback: v => v + '%' }}, grid: {{ color: '#F1F5F9' }} }},
              y: {{ grid: {{ display: false }}, ticks: {{ font: {{ size: 11, weight: '600' }} }} }}
            }},
            plugins: {{
              legend: {{ display: false }},
              tooltip: {{
                callbacks: {{
                  label: ctx => ` Desistência Acumulada: ${{ctx.raw}}%`
                }}
              }}
            }}
          }}
        }});
      }}
    }}

    function renderMasterTable() {{
      const term = (document.getElementById('master-search-input')?.value || '').toLowerCase();
      const tbody = document.getElementById('master-table-body');
      const filtered = DATA.p2.filter(r => r.NO_CINE_ROTULO.toLowerCase().includes(term) || r.NO_CINE_AREA_GERAL.toLowerCase().includes(term));

      tbody.innerHTML = filtered.map(r => `
        <tr class="hover:bg-slate-50">
          <td class="p-2.5 font-bold text-slate-900">${{r.NO_CINE_ROTULO}}</td>
          <td class="p-2.5 text-slate-500">${{r.NO_CINE_AREA_GERAL}}</td>
          <td class="p-2.5 text-slate-600">${{r.grau_academico}}</td>
          <td class="p-2.5 text-right font-medium">${{r.qt_ingressante < 10 ? '< 10' : r.qt_ingressante.toLocaleString('pt-BR')}}</td>
          <td class="p-2.5 text-right font-extrabold ${{r.tda >= 70 ? 'text-red-600' : 'text-slate-800'}}">${{r.tda.toFixed(1)}}%</td>
          <td class="p-2.5 text-right font-extrabold text-blue-600">${{r.tca.toFixed(1)}}%</td>
          <td class="p-2.5 text-right font-medium text-slate-500">${{r.tap.toFixed(1)}}%</td>
        </tr>
      `).join('');
    }}

    function downloadMasterCSV() {{
      const headers = ["Curso", "Grande_Area", "Grau", "Ingressantes", "Desistencia_TDA_Pct", "Conclusao_TCA_Pct", "Permanencia_TAP_Pct"];
      const rows = [headers.join(',')];
      DATA.p2.forEach(r => {{
        const ing = r.qt_ingressante < 10 ? '"< 10"' : r.qt_ingressante;
        rows.push([
          `"${{r.NO_CINE_ROTULO}}"`,
          `"${{r.NO_CINE_AREA_GERAL}}"`,
          `"${{r.grau_academico}}"`,
          ing,
          r.tda.toFixed(2),
          r.tca.toFixed(2),
          r.tap.toFixed(2)
        ].join(','));
      }});
      const blob = new Blob([rows.join('\\n')], {{ type: 'text/csv;charset=utf-8;' }});
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = 'rota_do_diploma_cursos_mt.csv';
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
    }}

    function initMainVisuals() {{
      const years = DATA.p1.map(r => r.nu_ano_referencia);
      const tca = DATA.p1.map(r => r.tca);
      const tda = DATA.p1.map(r => r.tda);
      const tap = DATA.p1.map(r => r.tap);
      const last = DATA.p1[DATA.p1.length - 1];

      // Donut Chart
      const donutCtx = document.getElementById('chart-funil-donut').getContext('2d');
      donutChart = new Chart(donutCtx, {{
        type: 'doughnut',
        data: {{
          labels: ['Concluíram', 'Desistiram', 'Retidos'],
          datasets: [{{
            data: [last.tca, last.tda, last.tap],
            backgroundColor: ['#2563EB', '#EF4444', '#94A3B8'],
            borderWidth: 3,
            borderColor: '#FFFFFF'
          }}]
        }},
        options: {{
          responsive: true,
          maintainAspectRatio: false,
          cutout: '68%',
          plugins: {{ legend: {{ display: false }} }}
        }}
      }});

      // Line Chart (Evolução da coorte)
      const lineCtx = document.getElementById('chart-evolucao-linhas').getContext('2d');
      lineChart = new Chart(lineCtx, {{
        type: 'line',
        data: {{
          labels: years,
          datasets: [
            {{ label: 'Concluiu', data: tca, borderColor: '#2563EB', backgroundColor: '#2563EB', pointRadius: 4, borderWidth: 2.5, tension: 0.2 }},
            {{ label: 'Desistiu', data: tda, borderColor: '#EF4444', backgroundColor: '#EF4444', pointRadius: 4, borderWidth: 2.5, tension: 0.2 }},
            {{ label: 'Retido', data: tap, borderColor: '#94A3B8', backgroundColor: '#94A3B8', pointRadius: 4, borderWidth: 2.5, tension: 0.2 }}
          ]
        }},
        options: {{
          responsive: true,
          maintainAspectRatio: false,
          scales: {{
            y: {{ min: 0, max: 100, ticks: {{ stepSize: 10 }}, grid: {{ color: '#F1F5F9' }}, title: {{ display: true, text: 'por 100 ingressantes', font: {{ size: 11, weight: 'bold' }}, color: '#64748B' }} }},
            x: {{ grid: {{ color: '#F8FAFC' }} }}
          }},
          plugins: {{ legend: {{ display: false }} }}
        }}
      }});

      renderCoursesBarChart();
      renderMasterTable();
    }}

    document.addEventListener('DOMContentLoaded', () => {{
      initMainVisuals();
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

    print(f"Dashboard em visualização única gerado com sucesso em:")
    print(f" - {dashboard_path}")
    print(f" - {outputs_html}")
    print(f" - {artifact_path}")

if __name__ == "__main__":
    main()
