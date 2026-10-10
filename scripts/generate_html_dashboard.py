"""Gera o dashboard completo e autossuficiente em HTML da Rota do Diploma.

Incorpora todas as 8 telas, dados reais consolidados, gráficos interativos SVG/Canvas,
filtros dinâmicos, navegação instantânea e conformidade com os tokens da Univag.
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

    html_content = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Rota do Diploma · DataHack Univag 2026</title>
  <!-- Tailwind CSS via allowlisted endpoint -->
  <script src="https://www.gstatic.com/antigravity/web/dev/tailwindcss.min.js"></script>
  <!-- Chart.js para gráficos profissionais e fluidos -->
  <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.1/dist/chart.umd.min.js"></script>
  <style>
    :root {{
      --brand-navy: #1A2B5E;
      --brand-blue: #0066CC;
      --brand-light: #00AEF0;
      --brand-purple: #6F42C1;
      --brand-pink: #E83E8C;
      --page: #F8F9FA;
      --surface: #FFFFFF;
      --border: #DEE2E6;
      --ink: #1A2B5E;
      --ink-muted: #6C757D;
      --status-good: #28A745;
      --status-warning: #FFC107;
      --status-critical: #DC3545;
    }}
    body {{
      background-color: var(--page);
      color: var(--ink);
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    }}
    .bg-navy {{ background-color: var(--brand-navy); }}
    .text-navy {{ color: var(--brand-navy); }}
    .border-navy {{ border-color: var(--brand-navy); }}
    .bg-action {{ background-color: var(--brand-blue); }}
    .text-action {{ color: var(--brand-blue); }}
    .nav-btn.active {{
      background-color: #0066CC !important;
      color: #FFFFFF !important;
      font-weight: 700;
    }}
    .nav-btn:hover:not(.active) {{
      background-color: #E9ECEF;
    }}
    .custom-scroll::-webkit-scrollbar {{
      width: 6px;
      height: 6px;
    }}
    .custom-scroll::-webkit-scrollbar-thumb {{
      background: #CBD5E1;
      border-radius: 4px;
    }}
  </style>
</head>
<body class="min-h-screen flex flex-col antialiased">

  <!-- Topbar Header com Identidade Univag -->
  <header class="bg-gradient-to-r from-[#1A2B5E] via-[#0D3B82] to-[#0066CC] text-white px-6 py-4 shadow-md sticky top-0 z-50">
    <div class="max-w-7xl mx-auto flex flex-col md:flex-row md:items-center justify-between gap-4">
      <div>
        <div class="flex items-center gap-2">
          <span class="bg-[#00AEF0] text-[#1A2B5E] text-xs font-black uppercase px-2 py-0.5 rounded tracking-wide">DataHack Univag 2026</span>
          <span class="text-xs text-blue-200 font-medium">· Mato Grosso (MT)</span>
        </div>
        <h1 class="text-2xl font-black tracking-tight mt-1">Rota do Diploma — Panorama do Ensino Superior</h1>
        <p class="text-xs text-blue-100 mt-0.5">Diagnóstico longitudinal, oferta regional, qualidade e permanência estudantil (2015–2024)</p>
      </div>
      <div class="flex items-center gap-2">
        <div class="bg-white/10 backdrop-blur border border-white/20 px-3 py-1.5 rounded-lg text-right">
          <div class="text-[11px] text-blue-200 font-bold uppercase tracking-wider">Status dos Dados</div>
          <div class="text-sm font-extrabold text-white flex items-center gap-1.5 justify-end">
            <span class="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span>
            Snapshots Oficiais Aprovados
          </div>
        </div>
        <button onclick="downloadActiveCSV()" class="bg-[#00AEF0] hover:bg-sky-400 text-[#1A2B5E] text-xs font-bold px-3 py-2 rounded-lg flex items-center gap-1.5 shadow transition">
          <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4"></path></svg>
          Exportar CSV
        </button>
      </div>
    </div>
  </header>

  <!-- Container Principal: Sidebar + Telas -->
  <div class="max-w-7xl mx-auto w-full flex-1 flex flex-col md:flex-row px-4 py-6 gap-6">

    <!-- Navegação Lateral (8 Telas) -->
    <aside class="w-full md:w-64 shrink-0 bg-white border border-[#DEE2E6] rounded-xl p-3 shadow-sm h-fit sticky top-24">
      <div class="text-xs font-bold uppercase text-[#6C757D] px-3 py-2 tracking-wider">Painéis do Desafio</div>
      <nav class="space-y-1">
        <button onclick="switchTab('t1')" id="btn-t1" class="nav-btn active w-full text-left px-3 py-2.5 rounded-lg text-sm font-semibold flex items-center gap-2.5 transition">
          <span>🏠</span> <span>1. Panorama Geral</span>
        </button>
        <button onclick="switchTab('t2')" id="btn-t2" class="nav-btn w-full text-left px-3 py-2.5 rounded-lg text-sm font-semibold flex items-center gap-2.5 transition text-[#1A2B5E]">
          <span>📉</span> <span>2. P1: Trajetória 2015</span>
        </button>
        <button onclick="switchTab('t3')" id="btn-t3" class="nav-btn w-full text-left px-3 py-2.5 rounded-lg text-sm font-semibold flex items-center gap-2.5 transition text-[#1A2B5E]">
          <span>🧭</span> <span>3. P2: Cursos e Áreas</span>
        </button>
        <button onclick="switchTab('t4')" id="btn-t4" class="nav-btn w-full text-left px-3 py-2.5 rounded-lg text-sm font-semibold flex items-center gap-2.5 transition text-[#1A2B5E]">
          <span>🏛️</span> <span>4. P3: Rede e Modalidade</span>
        </button>
        <button onclick="switchTab('t5')" id="btn-t5" class="nav-btn w-full text-left px-3 py-2.5 rounded-lg text-sm font-semibold flex items-center gap-2.5 transition text-[#1A2B5E]">
          <span>⭐</span> <span>5. P4: Qualidade (CPC)</span>
        </button>
        <button onclick="switchTab('t6')" id="btn-t6" class="nav-btn w-full text-left px-3 py-2.5 rounded-lg text-sm font-semibold flex items-center gap-2.5 transition text-[#1A2B5E]">
          <span>📚</span> <span>6. P5: Licenciaturas</span>
        </button>
        <button onclick="switchTab('t7')" id="btn-t7" class="nav-btn w-full text-left px-3 py-2.5 rounded-lg text-sm font-semibold flex items-center gap-2.5 transition text-[#1A2B5E]">
          <span>🏜️</span> <span>7. B1: Desertos de Vagas</span>
        </button>
        <button onclick="switchTab('t8')" id="btn-t8" class="nav-btn w-full text-left px-3 py-2.5 rounded-lg text-sm font-semibold flex items-center gap-2.5 transition text-[#1A2B5E]">
          <span>💰</span> <span>8. B2: Financiamento</span>
        </button>
      </nav>

      <div class="mt-4 pt-3 border-t border-[#DEE2E6] text-[11px] text-[#6C757D] px-2 leading-relaxed">
        <b>Regra do Desafio:</b> Células com &lt; 10 alunos são protegidas por supressão para evitar reidentificação.
      </div>
    </aside>

    <!-- Conteúdo Dinâmico das 8 Telas -->
    <main class="flex-1 min-w-0">

      <!-- ================= TELA 1: PANORAMA GERAL ================= -->
      <section id="tab-t1" class="space-y-6">
        <!-- 4 KPIs Macro -->
        <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          <div class="bg-white border border-[#DEE2E6] rounded-xl p-5 shadow-sm">
            <div class="text-xs font-bold text-[#6C757D] uppercase tracking-wider">Ingressantes Coorte 2015</div>
            <div class="text-3xl font-black text-[#1A2B5E] mt-1">40.896</div>
            <div class="text-xs text-[#0066CC] font-semibold mt-1">Presencial · Mato Grosso</div>
          </div>
          <div class="bg-white border border-[#DEE2E6] rounded-xl p-5 shadow-sm">
            <div class="text-xs font-bold text-[#6C757D] uppercase tracking-wider">Desistência em 10 Anos (TDA)</div>
            <div class="text-3xl font-black text-[#DC3545] mt-1">60,2%</div>
            <div class="text-xs text-[#DC3545] font-semibold mt-1">60 a cada 100 abandonaram</div>
          </div>
          <div class="bg-white border border-[#DEE2E6] rounded-xl p-5 shadow-sm">
            <div class="text-xs font-bold text-[#6C757D] uppercase tracking-wider">Conclusão em 10 Anos (TCA)</div>
            <div class="text-3xl font-black text-[#28A745] mt-1">38,8%</div>
            <div class="text-xs text-[#28A745] font-semibold mt-1">39 a cada 100 diplomados</div>
          </div>
          <div class="bg-white border border-[#DEE2E6] rounded-xl p-5 shadow-sm">
            <div class="text-xs font-bold text-[#6C757D] uppercase tracking-wider">Permanência Atual (TAP)</div>
            <div class="text-3xl font-black text-[#0066CC] mt-1">1,0%</div>
            <div class="text-xs text-[#0066CC] font-semibold mt-1">1 a cada 100 ainda cursando</div>
          </div>
        </div>

        <!-- Grade dos 7 Cartões das Perguntas -->
        <div class="bg-white border border-[#DEE2E6] rounded-xl p-6 shadow-sm">
          <h2 class="text-lg font-bold text-[#1A2B5E] mb-4 flex items-center gap-2">
            <span>📋</span> Resumo Executivo das 7 Perguntas do Desafio
          </h2>
          <div class="grid grid-cols-1 md:grid-cols-2 gap-4">

            <div onclick="switchTab('t2')" class="cursor-pointer border border-[#DEE2E6] hover:border-[#0066CC] rounded-xl p-4 transition hover:shadow-md bg-[#F8F9FA]">
              <div class="flex justify-between items-center text-xs font-bold">
                <span class="bg-[#0066CC] text-white px-2 py-0.5 rounded">P1 · Obrigatória</span>
                <span class="text-[#6C757D]">2015–2024</span>
              </div>
              <div class="font-bold text-[#1A2B5E] text-base mt-2">Quanto da turma fica pelo caminho?</div>
              <div class="text-2xl font-black text-[#0066CC] mt-1">60,2% desistência</div>
              <p class="text-xs text-[#495057] mt-1 leading-relaxed">Maior salto no 2º ano de curso (+16,96 p.p. em 2016), com segundo pico de perda no 5º ano.</p>
            </div>

            <div onclick="switchTab('t3')" class="cursor-pointer border border-[#DEE2E6] hover:border-[#0066CC] rounded-xl p-4 transition hover:shadow-md bg-[#F8F9FA]">
              <div class="flex justify-between items-center text-xs font-bold">
                <span class="bg-[#0066CC] text-white px-2 py-0.5 rounded">P2 · Obrigatória</span>
                <span class="text-[#6C757D]">Trajetória 2024</span>
              </div>
              <div class="font-bold text-[#1A2B5E] text-base mt-2">Onde a rota mais se perde?</div>
              <div class="text-2xl font-black text-[#DC3545] mt-1">TI & Engenharias > 70%</div>
              <p class="text-xs text-[#495057] mt-1 leading-relaxed">Eng. Ambiental (87,4%) e Matemática (84,3%) no topo do abandono; Medicina tem retenção de 85,2%.</p>
            </div>

            <div onclick="switchTab('t4')" class="cursor-pointer border border-[#DEE2E6] hover:border-[#0066CC] rounded-xl p-4 transition hover:shadow-md bg-[#F8F9FA]">
              <div class="flex justify-between items-center text-xs font-bold">
                <span class="bg-[#0066CC] text-white px-2 py-0.5 rounded">P3 · Obrigatória</span>
                <span class="text-[#6C757D]">Censo 2021–2024</span>
              </div>
              <div class="font-bold text-[#1A2B5E] text-base mt-2">Pública × Privada, Presencial × EAD</div>
              <div class="text-2xl font-black text-[#0066CC] mt-1">+57% no EAD Privado</div>
              <p class="text-xs text-[#495057] mt-1 leading-relaxed">2022 é o ano atípico com pico de desvinculações pós-pandemia (> 44 mil desvinculados em MT).</p>
            </div>

            <div onclick="switchTab('t5')" class="cursor-pointer border border-[#DEE2E6] hover:border-[#0066CC] rounded-xl p-4 transition hover:shadow-md bg-[#F8F9FA]">
              <div class="flex justify-between items-center text-xs font-bold">
                <span class="bg-[#0066CC] text-white px-2 py-0.5 rounded">P4 · Obrigatória</span>
                <span class="text-[#6C757D]">CPC 2021–2023</span>
              </div>
              <div class="font-bold text-[#1A2B5E] text-base mt-2">Qualidade retém? (CPC)</div>
              <div class="text-2xl font-black text-[#28A745] mt-1">CPC 4 e 5: 38% evasão</div>
              <p class="text-xs text-[#495057] mt-1 leading-relaxed">Associação moderada (R = -0,42). Fatores de autosseleção e perfil da área explicam grande parte da relação.</p>
            </div>

            <div onclick="switchTab('t6')" class="cursor-pointer border border-[#DEE2E6] hover:border-[#0066CC] rounded-xl p-4 transition hover:shadow-md bg-[#F8F9FA]">
              <div class="flex justify-between items-center text-xs font-bold">
                <span class="bg-[#0066CC] text-white px-2 py-0.5 rounded">P5 · Obrigatória</span>
                <span class="text-[#6C757D]">Enade 2025</span>
              </div>
              <div class="font-bold text-[#1A2B5E] text-base mt-2">O funil das licenciaturas</div>
              <div class="text-2xl font-black text-[#DC3545] mt-1">57,5% desistem · Exatas &lt; 25% profic.</div>
              <p class="text-xs text-[#495057] mt-1 leading-relaxed">Duplo funil: alta evasão nos cursos e menos de um quarto dos concluintes em Matemática/Física atinge proficiência.</p>
            </div>

            <div onclick="switchTab('t7')" class="cursor-pointer border border-[#DEE2E6] hover:border-[#6F42C1] rounded-xl p-4 transition hover:shadow-md bg-[#F8F9FA]">
              <div class="flex justify-between items-center text-xs font-bold">
                <span class="bg-[#6F42C1] text-white px-2 py-0.5 rounded">B1 · Bônus</span>
                <span class="text-[#6C757D]">Censo 2024 × IBGE 2022</span>
              </div>
              <div class="font-bold text-[#1A2B5E] text-base mt-2">Desertos de ensino superior</div>
              <div class="text-2xl font-black text-[#6F42C1] mt-1">> 60% municípios sem oferta</div>
              <p class="text-xs text-[#495057] mt-1 leading-relaxed">Forte polarização em Cuiabá, VG, Rondonópolis e Sinop. Cerca de 80 municípios com zero vagas presenciais.</p>
            </div>

            <div onclick="switchTab('t8')" class="cursor-pointer border border-[#DEE2E6] hover:border-[#6F42C1] rounded-xl p-4 transition hover:shadow-md bg-[#F8F9FA] md:col-span-2">
              <div class="flex justify-between items-center text-xs font-bold">
                <span class="bg-[#6F42C1] text-white px-2 py-0.5 rounded">B2 · Bônus</span>
                <span class="text-[#6C757D]">Rede Privada 2021–2024</span>
              </div>
              <div class="font-bold text-[#1A2B5E] text-base mt-2">Financiamento e permanência (FIES & ProUni)</div>
              <div class="text-2xl font-black text-[#28A745] mt-1">Desvinculação 16 p.p. menor em financiados</div>
              <p class="text-xs text-[#495057] mt-1 leading-relaxed">Alunos apoiados por FIES/ProUni apresentam taxa de desvinculação anual de 8,8% contra 24,1% nos não financiados.</p>
            </div>

          </div>
        </div>

        <!-- Gráfico Geral de Trajetória da Turma -->
        <div class="bg-white border border-[#DEE2E6] rounded-xl p-6 shadow-sm">
          <h2 class="text-lg font-bold text-[#1A2B5E] mb-2">Trajetória Acumulada dos Ingressantes (Coorte 2015 MT · 10 Anos)</h2>
          <p class="text-xs text-[#6C757D] mb-4">Evolução de 100% da turma acompanhada ano a ano entre 2015 e 2024.</p>
          <div class="h-80">
            <canvas id="chart-t1-trajetoria"></canvas>
          </div>
        </div>
      </section>

      <!-- ================= TELA 2: P1 TRAJETÓRIA ================= -->
      <section id="tab-t2" class="hidden space-y-6">
        <div class="bg-gradient-to-r from-blue-50 to-indigo-50 border-l-4 border-[#0066CC] rounded-xl p-5">
          <div class="text-xs font-bold text-[#0066CC] uppercase">P1 · Pergunta Oficial</div>
          <h2 class="text-xl font-black text-[#1A2B5E] mt-1">Coorte 2015, presencial: quanto desistiu, concluiu e seguia em 2024? Em que ano a perda é maior?</h2>
          <div class="text-sm text-[#495057] mt-2 space-y-1">
            <p>• <b>Situação em 2024:</b> <b>60,2% desistiram</b>, <b>38,8% concluíram</b> e <b>1,0% continuava matriculado</b>.</p>
            <p>• <b>A cada 100 ingressantes:</b> 60 abandonaram, 39 se formaram e 1 segue cursando.</p>
            <p>• <b>Ano de maior perda:</b> O salto mais expressivo ocorre no <b>2º ano (2016)</b> com <b>+16,96 p.p. de desistência acumulada</b> (de 7,0% para 24,0%), com segundo pico no 5º ano (2019) com +10,87 p.p. ao término do prazo regular de integralização.</p>
          </div>
        </div>

        <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div class="bg-white border border-[#DEE2E6] rounded-xl p-5 shadow-sm">
            <h3 class="text-base font-bold text-[#1A2B5E] mb-3">Distribuição 100% Acumulada por Ano de Curso</h3>
            <div class="h-72">
              <canvas id="chart-p1-stacked"></canvas>
            </div>
          </div>
          <div class="bg-white border border-[#DEE2E6] rounded-xl p-5 shadow-sm">
            <h3 class="text-base font-bold text-[#1A2B5E] mb-3">Incremento Anual da Desistência (Δ TDA em p.p.)</h3>
            <div class="h-72">
              <canvas id="chart-p1-delta"></canvas>
            </div>
          </div>
        </div>

        <!-- Tabela Detalhada P1 -->
        <div class="bg-white border border-[#DEE2E6] rounded-xl p-5 shadow-sm">
          <div class="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-3 mb-4">
            <h3 class="text-base font-bold text-[#1A2B5E]">Evolução Anual da Coorte 2015 em Mato Grosso</h3>
            <span class="text-xs text-[#6C757D]">Base: 40.896 Ingressantes</span>
          </div>
          <div class="overflow-x-auto custom-scroll">
            <table class="w-full text-left text-xs border-collapse">
              <thead>
                <tr class="bg-[#1A2B5E] text-white">
                  <th class="p-2.5">Ano Ref.</th>
                  <th class="p-2.5">Ano de Curso</th>
                  <th class="p-2.5 text-right">Ingressantes</th>
                  <th class="p-2.5 text-right">Desistência Acum. (TDA)</th>
                  <th class="p-2.5 text-right">Salto Anual (Δ)</th>
                  <th class="p-2.5 text-right">Conclusão Acum. (TCA)</th>
                  <th class="p-2.5 text-right">Permanência (TAP)</th>
                </tr>
              </thead>
              <tbody id="table-p1-body" class="divide-y divide-[#DEE2E6]"></tbody>
            </table>
          </div>
        </div>
      </section>

      <!-- ================= TELA 3: P2 CURSOS E ÁREAS ================= -->
      <section id="tab-t3" class="hidden space-y-6">
        <div class="bg-gradient-to-r from-blue-50 to-indigo-50 border-l-4 border-[#0066CC] rounded-xl p-5">
          <div class="text-xs font-bold text-[#0066CC] uppercase">P2 · Pergunta Oficial</div>
          <h2 class="text-xl font-black text-[#1A2B5E] mt-1">Quais cursos e áreas possuem maior e menor desistência? Como comparar as coortes?</h2>
          <p class="text-sm text-[#495057] mt-2">
            Áreas de <b>TI e Engenharias superam 70% de perda</b> em MT. <b>Medicina</b> é o curso mais resiliente (14,8% desistência e 85,2% conclusão). Coortes só devem ser comparadas em horizontes equivalentes de acompanhamento.
          </p>
        </div>

        <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div class="bg-white border border-[#DEE2E6] rounded-xl p-5 shadow-sm">
            <h3 class="text-base font-bold text-[#DC3545] mb-3">Top 5 Cursos com MAIOR Desistência (TDA %)</h3>
            <div class="h-64">
              <canvas id="chart-p2-maior"></canvas>
            </div>
          </div>
          <div class="bg-white border border-[#DEE2E6] rounded-xl p-5 shadow-sm">
            <h3 class="text-base font-bold text-[#28A745] mb-3">Top 5 Cursos com MENOR Desistência (TDA %)</h3>
            <div class="h-64">
              <canvas id="chart-p2-menor"></canvas>
            </div>
          </div>
        </div>

        <!-- Tabela Filtrável P2 -->
        <div class="bg-white border border-[#DEE2E6] rounded-xl p-5 shadow-sm">
          <div class="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-3 mb-4">
            <h3 class="text-base font-bold text-[#1A2B5E]">Cursos Ofertados em Mato Grosso (Rótulo CINE)</h3>
            <input type="text" id="search-p2" oninput="filterP2Table()" placeholder="Buscar curso ou área..." class="px-3 py-1.5 border border-[#DEE2E6] rounded-lg text-xs w-full sm:w-64">
          </div>
          <div class="overflow-x-auto custom-scroll max-h-96">
            <table class="w-full text-left text-xs border-collapse">
              <thead class="sticky top-0 bg-[#1A2B5E] text-white">
                <tr>
                  <th class="p-2.5">Curso (Rótulo CINE)</th>
                  <th class="p-2.5">Grande Área</th>
                  <th class="p-2.5">Grau</th>
                  <th class="p-2.5 text-right">Ingressantes</th>
                  <th class="p-2.5 text-right">Desistência (TDA)</th>
                  <th class="p-2.5 text-right">Conclusão (TCA)</th>
                </tr>
              </thead>
              <tbody id="table-p2-body" class="divide-y divide-[#DEE2E6]"></tbody>
            </table>
          </div>
        </div>
      </section>

      <!-- ================= TELA 4: P3 REDE E MODALIDADE ================= -->
      <section id="tab-t4" class="hidden space-y-6">
        <div class="bg-gradient-to-r from-blue-50 to-indigo-50 border-l-4 border-[#0066CC] rounded-xl p-5">
          <div class="text-xs font-bold text-[#0066CC] uppercase">P3 · Pergunta Oficial</div>
          <h2 class="text-xl font-black text-[#1A2B5E] mt-1">Como se comportam as matrículas e a evasão anual entre 2021 e 2024? Existe algum ano atípico?</h2>
          <p class="text-sm text-[#495057] mt-2">
            <b>Ano Atípico: 2022</b> registrou o maior pico de desvinculações pós-pandemia (> 44.000 desvinculações na rede privada em MT). Paralelamente, houve explosão de <b>+57,1% no EAD Privado</b>, enquanto o presencial privado encolheu -5,0%.
          </p>
        </div>

        <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div class="bg-white border border-[#DEE2E6] rounded-xl p-5 shadow-sm">
            <h3 class="text-base font-bold text-[#1A2B5E] mb-3">Evolução das Matrículas por Segmento (2021–2024)</h3>
            <div class="h-64">
              <canvas id="chart-p3-mat"></canvas>
            </div>
          </div>
          <div class="bg-white border border-[#DEE2E6] rounded-xl p-5 shadow-sm">
            <h3 class="text-base font-bold text-[#1A2B5E] mb-3">Desvinculações Censitárias por Segmento (%)</h3>
            <div class="h-64">
              <canvas id="chart-p3-desv"></canvas>
            </div>
          </div>
        </div>

        <div class="bg-white border border-[#DEE2E6] rounded-xl p-5 shadow-sm">
          <h3 class="text-base font-bold text-[#1A2B5E] mb-3">Tabela Consolidada do Censo Superior MT</h3>
          <div class="overflow-x-auto custom-scroll">
            <table class="w-full text-left text-xs border-collapse">
              <thead>
                <tr class="bg-[#1A2B5E] text-white">
                  <th class="p-2.5">Ano</th>
                  <th class="p-2.5">Segmento</th>
                  <th class="p-2.5 text-right">Matrículas</th>
                  <th class="p-2.5 text-right">Ingressantes</th>
                  <th class="p-2.5 text-right">Desvinculados</th>
                  <th class="p-2.5 text-right">% Desvinculados/Matr.</th>
                </tr>
              </thead>
              <tbody id="table-p3-body" class="divide-y divide-[#DEE2E6]"></tbody>
            </table>
          </div>
        </div>
      </section>

      <!-- ================= TELA 5: P4 QUALIDADE (CPC) ================= -->
      <section id="tab-t5" class="hidden space-y-6">
        <div class="bg-gradient-to-r from-blue-50 to-indigo-50 border-l-4 border-[#0066CC] rounded-xl p-5">
          <div class="text-xs font-bold text-[#0066CC] uppercase">P4 · Pergunta Oficial</div>
          <h2 class="text-xl font-black text-[#1A2B5E] mt-1">Cursos com CPC mais alto apresentam menor desistência? O que mais pode explicar essa relação?</h2>
          <p class="text-sm text-[#495057] mt-2">
            Existe <b>associação negativa moderada (R = -0,42)</b>. Cursos faixas 4 e 5 abandonam menos (35% a 48%) que faixas 1 e 2 (> 70%). Efeitos de autosseleção vestibular, prestígio da carreira e programas de apoio ao estudante nas universidades públicas explicam grande parte dessa retenção.
          </p>
        </div>

        <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div class="bg-white border border-[#DEE2E6] rounded-xl p-5 shadow-sm">
            <h3 class="text-base font-bold text-[#1A2B5E] mb-3">Dispersão: CPC Contínuo vs Taxa de Desistência</h3>
            <div class="h-64">
              <canvas id="chart-p4-scatter"></canvas>
            </div>
          </div>
          <div class="bg-white border border-[#DEE2E6] rounded-xl p-5 shadow-sm">
            <h3 class="text-base font-bold text-[#1A2B5E] mb-3">Desistência Média por Faixa de CPC</h3>
            <div class="h-64">
              <canvas id="chart-p4-faixas"></canvas>
            </div>
          </div>
        </div>
      </section>

      <!-- ================= TELA 6: P5 LICENCIATURAS ================= -->
      <section id="tab-t6" class="hidden space-y-6">
        <div class="bg-gradient-to-r from-blue-50 to-indigo-50 border-l-4 border-[#0066CC] rounded-xl p-5">
          <div class="text-xs font-bold text-[#0066CC] uppercase">P5 · Pergunta Oficial</div>
          <h2 class="text-xl font-black text-[#1A2B5E] mt-1">Quanto desiste nas licenciaturas e quanto dos concluintes é proficiente no Enade 2025?</h2>
          <p class="text-sm text-[#495057] mt-2">
            <b>Duplo Gargalo:</b> 57,5% abandonam a licenciatura (ultrapassando 80% em Matemática e Química). Entre os raros concluintes, <b>menos de 25% atingem o padrão de proficiência Enade em Exatas</b>.
          </p>
        </div>

        <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div class="bg-white border border-[#DEE2E6] rounded-xl p-5 shadow-sm">
            <h3 class="text-base font-bold text-[#DC3545] mb-3">Painel A: Desistência na Trajetória (TDA %)</h3>
            <div class="h-64">
              <canvas id="chart-p5-tda"></canvas>
            </div>
          </div>
          <div class="bg-white border border-[#DEE2E6] rounded-xl p-5 shadow-sm">
            <h3 class="text-base font-bold text-[#0066CC] mb-3">Painel B: Proficiência no Enade 2025 (%)</h3>
            <div class="h-64">
              <canvas id="chart-p5-enade"></canvas>
            </div>
          </div>
        </div>
      </section>

      <!-- ================= TELA 7: B1 DESERTOS ================= -->
      <section id="tab-t7" class="hidden space-y-6">
        <div class="bg-gradient-to-r from-blue-50 to-indigo-50 border-l-4 border-[#6F42C1] rounded-xl p-5">
          <div class="text-xs font-bold text-[#6F42C1] uppercase">B1 · Pergunta Bônus</div>
          <h2 class="text-xl font-black text-[#1A2B5E] mt-1">Quantas vagas presenciais existem por 100 jovens de 18 a 24 anos em cada município? Onde não há oferta?</h2>
          <p class="text-sm text-[#495057] mt-2">
            Média estadual de ~15,2 vagas por 100 jovens, polarizada em Cuiabá (27,7), VG (22,3), Sinop (23,8) e Rondonópolis (21,4). <b>Mais de 60% dos municípios de MT (~80 municípios) não têm nenhuma vaga presencial registrada</b>.
          </p>
        </div>

        <div class="bg-white border border-[#DEE2E6] rounded-xl p-5 shadow-sm">
          <h3 class="text-base font-bold text-[#1A2B5E] mb-3">Top Polos Regionais (Vagas por 100 Jovens)</h3>
          <div class="h-64">
            <canvas id="chart-b1-polos"></canvas>
          </div>
        </div>

        <div class="bg-white border border-[#DEE2E6] rounded-xl p-5 shadow-sm">
          <div class="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-3 mb-4">
            <h3 class="text-base font-bold text-[#1A2B5E]">Tabela Municipal de Vagas Presenciais</h3>
            <input type="text" id="search-b1" oninput="filterB1Table()" placeholder="Buscar município..." class="px-3 py-1.5 border border-[#DEE2E6] rounded-lg text-xs w-full sm:w-64">
          </div>
          <div class="overflow-x-auto custom-scroll max-h-96">
            <table class="w-full text-left text-xs border-collapse">
              <thead class="sticky top-0 bg-[#1A2B5E] text-white">
                <tr>
                  <th class="p-2.5">Código IBGE</th>
                  <th class="p-2.5">Município</th>
                  <th class="p-2.5 text-right">População 18-24a (IBGE 2022)</th>
                  <th class="p-2.5 text-right">Vagas Presenciais 2024</th>
                  <th class="p-2.5 text-right">Vagas / 100 Jovens</th>
                  <th class="p-2.5">Classificação</th>
                </tr>
              </thead>
              <tbody id="table-b1-body" class="divide-y divide-[#DEE2E6]"></tbody>
            </table>
          </div>
        </div>
      </section>

      <!-- ================= TELA 8: B2 FINANCIAMENTO ================= -->
      <section id="tab-t8" class="hidden space-y-6">
        <div class="bg-gradient-to-r from-blue-50 to-indigo-50 border-l-4 border-[#6F42C1] rounded-xl p-5">
          <div class="text-xs font-bold text-[#6F42C1] uppercase">B2 · Pergunta Bônus</div>
          <h2 class="text-xl font-black text-[#1A2B5E] mt-1">Qual é o peso de FIES e ProUni na rede privada entre 2021 e 2024? Cursos com mais financiados evadem menos?</h2>
          <p class="text-sm text-[#495057] mt-2">
            Sim. Cursos com mais financiados têm <b>desvinculação anual média de 8,8% contra 24,1% nos não financiados</b> (uma vantagem protetiva de ~15 a 16 p.p. a favor da permanência).
          </p>
        </div>

        <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div class="bg-white border border-[#DEE2E6] rounded-xl p-5 shadow-sm">
            <h3 class="text-base font-bold text-[#1A2B5E] mb-3">Evolução do Apoio Financeiro na Rede Privada (%)</h3>
            <div class="h-64">
              <canvas id="chart-b2-evol"></canvas>
            </div>
          </div>
          <div class="bg-white border border-[#DEE2E6] rounded-xl p-5 shadow-sm">
            <h3 class="text-base font-bold text-[#1A2B5E] mb-3">Desvinculação: Financiados vs Não Financiados (%)</h3>
            <div class="h-64">
              <canvas id="chart-b2-comp"></canvas>
            </div>
          </div>
        </div>
      </section>

    </main>
  </div>

  <!-- Scripts JavaScript & Chart.js -->
  <script>
    const DATA = {data_json};
    let currentTab = 't1';

    function switchTab(tabId) {{
      currentTab = tabId;
      document.querySelectorAll('main > section').forEach(sec => sec.classList.add('hidden'));
      document.querySelectorAll('.nav-btn').forEach(btn => btn.classList.remove('active'));

      const targetSec = document.getElementById('tab-' + tabId);
      const targetBtn = document.getElementById('btn-' + tabId);
      if (targetSec) targetSec.classList.remove('hidden');
      if (targetBtn) targetBtn.classList.add('active');

      window.scrollTo({{ top: 0, behavior: 'smooth' }});
    }}

    // Renderiza Tabelas
    function renderTables() {{
      // P1
      const p1Body = document.getElementById('table-p1-body');
      p1Body.innerHTML = DATA.p1.map(r => `
        <tr class="hover:bg-slate-50">
          <td class="p-2.5 font-bold">${{r.nu_ano_referencia}}</td>
          <td class="p-2.5">${{r.ano_curso}}</td>
          <td class="p-2.5 text-right">${{r.qt_ingressante.toLocaleString('pt-BR')}}</td>
          <td class="p-2.5 text-right font-bold text-red-600">${{r.tda.toFixed(2)}}%</td>
          <td class="p-2.5 text-right text-red-500 font-semibold">+${{r.delta_tda.toFixed(2)}} p.p.</td>
          <td class="p-2.5 text-right font-bold text-emerald-600">${{r.tca.toFixed(2)}}%</td>
          <td class="p-2.5 text-right text-blue-600">${{r.tap.toFixed(2)}}%</td>
        </tr>
      `).join('');

      // P2
      filterP2Table();

      // P3
      const p3Body = document.getElementById('table-p3-body');
      p3Body.innerHTML = DATA.p3.map(r => `
        <tr class="hover:bg-slate-50">
          <td class="p-2.5 font-bold">${{r.nu_ano_censo}}</td>
          <td class="p-2.5 font-semibold text-[#1A2B5E]">${{r.segmento}}</td>
          <td class="p-2.5 text-right font-bold">${{r.qt_mat.toLocaleString('pt-BR')}}</td>
          <td class="p-2.5 text-right">${{r.qt_ing.toLocaleString('pt-BR')}}</td>
          <td class="p-2.5 text-right text-amber-700">${{r.qt_sit_desvinculado.toLocaleString('pt-BR')}}</td>
          <td class="p-2.5 text-right font-bold text-red-600">${{r.pct_desvinculacao.toFixed(2)}}%</td>
        </tr>
      `).join('');

      // B1
      filterB1Table();
    }}

    function filterP2Table() {{
      const term = (document.getElementById('search-p2')?.value || '').toLowerCase();
      const p2Body = document.getElementById('table-p2-body');
      const filtered = DATA.p2.filter(r =>
        r.NO_CINE_ROTULO.toLowerCase().includes(term) ||
        r.NO_CINE_AREA_GERAL.toLowerCase().includes(term)
      );
      p2Body.innerHTML = filtered.map(r => `
        <tr class="hover:bg-slate-50">
          <td class="p-2.5 font-semibold text-[#1A2B5E]">${{r.NO_CINE_ROTULO}}</td>
          <td class="p-2.5 text-[#6C757D]">${{r.NO_CINE_AREA_GERAL}}</td>
          <td class="p-2.5">${{r.grau_academico}}</td>
          <td class="p-2.5 text-right">${{r.qt_ingressante < 10 ? '< 10 (suprimido)' : r.qt_ingressante.toLocaleString('pt-BR')}}</td>
          <td class="p-2.5 text-right font-bold ${{r.tda > 70 ? 'text-red-600' : 'text-slate-700'}}">${{r.tda.toFixed(1)}}%</td>
          <td class="p-2.5 text-right font-bold text-emerald-600">${{r.tca.toFixed(1)}}%</td>
        </tr>
      `).join('');
    }}

    function filterB1Table() {{
      const term = (document.getElementById('search-b1')?.value || '').toLowerCase();
      const b1Body = document.getElementById('table-b1-body');
      const filtered = DATA.b1.filter(r => r.no_municipio.toLowerCase().includes(term));
      b1Body.innerHTML = filtered.map(r => `
        <tr class="hover:bg-slate-50">
          <td class="p-2.5 text-[#6C757D]">${{r.co_municipio}}</td>
          <td class="p-2.5 font-bold text-[#1A2B5E]">${{r.no_municipio}}</td>
          <td class="p-2.5 text-right">${{r.pop_18_24.toLocaleString('pt-BR')}}</td>
          <td class="p-2.5 text-right font-bold">${{r.vagas_presenciais.toLocaleString('pt-BR')}}</td>
          <td class="p-2.5 text-right font-black ${{r.vagas_por_100_jovens === 0 ? 'text-red-500' : 'text-blue-700'}}">
            ${{r.vagas_por_100_jovens.toFixed(2)}}
          </td>
          <td class="p-2.5">
            <span class="px-2 py-0.5 rounded text-[10px] font-bold ${{r.vagas_presenciais === 0 ? 'bg-red-100 text-red-700' : (r.vagas_por_100_jovens >= 20 ? 'bg-emerald-100 text-emerald-800' : 'bg-amber-100 text-amber-800')}}">
              ${{r.classificacao}}
            </span>
          </td>
        </tr>
      `).join('');
    }}

    // Exportação CSV do conjunto de dados ativo
    function downloadActiveCSV() {{
      let activeData = DATA.p1;
      let filename = 'p1_trajetoria_coorte2015.csv';
      if (currentTab === 't3') {{ activeData = DATA.p2; filename = 'p2_cursos_areas.csv'; }}
      else if (currentTab === 't4') {{ activeData = DATA.p3; filename = 'p3_censo_rede_modalidade.csv'; }}
      else if (currentTab === 't5') {{ activeData = DATA.p4; filename = 'p4_qualidade_cpc.csv'; }}
      else if (currentTab === 't6') {{ activeData = DATA.p5; filename = 'p5_licenciaturas.csv'; }}
      else if (currentTab === 't7') {{ activeData = DATA.b1; filename = 'b1_oferta_municipal.csv'; }}
      else if (currentTab === 't8') {{ activeData = DATA.b2; filename = 'b2_financiamento.csv'; }}

      if (!activeData || !activeData.length) return;
      const headers = Object.keys(activeData[0]);
      const csvRows = [headers.join(',')];
      for (const row of activeData) {{
        const values = headers.map(h => {{
          const val = row[h];
          if (typeof val === 'number' && val < 10 && h.toLowerCase().includes('ingressante')) return '"< 10"';
          return JSON.stringify(val ?? '');
        }});
        csvRows.push(values.join(','));
      }}
      const blob = new Blob([csvRows.join('\\n')], {{ type: 'text/csv;charset=utf-8;' }});
      const url = URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.setAttribute('href', url);
      link.setAttribute('download', filename);
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
    }}

    // Inicialização dos Gráficos com Chart.js
    function initCharts() {{
      const yearsP1 = DATA.p1.map(r => r.ano_curso);
      const tdaP1 = DATA.p1.map(r => r.tda);
      const tcaP1 = DATA.p1.map(r => r.tca);
      const tapP1 = DATA.p1.map(r => r.tap);
      const deltaP1 = DATA.p1.map(r => r.delta_tda);

      // Tela 1: Gráfico Mestre Trajetória
      new Chart(document.getElementById('chart-t1-trajetoria'), {{
        type: 'bar',
        data: {{
          labels: yearsP1,
          datasets: [
            {{ label: 'Desistência Acum. (TDA %)', data: tdaP1, backgroundColor: '#DC3545' }},
            {{ label: 'Conclusão Acum. (TCA %)', data: tcaP1, backgroundColor: '#28A745' }},
            {{ label: 'Permanência no Curso (TAP %)', data: tapP1, backgroundColor: '#0066CC' }}
          ]
        }},
        options: {{
          responsive: true,
          maintainAspectRatio: false,
          scales: {{ x: {{ stacked: true }}, y: {{ stacked: true, max: 100 }} }}
        }}
      }});

      // Tela 2: Gráficos P1
      new Chart(document.getElementById('chart-p1-stacked'), {{
        type: 'bar',
        data: {{
          labels: yearsP1,
          datasets: [
            {{ label: 'TDA %', data: tdaP1, backgroundColor: '#DC3545' }},
            {{ label: 'TCA %', data: tcaP1, backgroundColor: '#28A745' }},
            {{ label: 'TAP %', data: tapP1, backgroundColor: '#0066CC' }}
          ]
        }},
        options: {{ responsive: true, maintainAspectRatio: false, scales: {{ x: {{ stacked: true }}, y: {{ stacked: true, max: 100 }} }} }}
      }});

      new Chart(document.getElementById('chart-p1-delta'), {{
        type: 'bar',
        data: {{
          labels: yearsP1,
          datasets: [{{ label: 'Salto Anual (Δ p.p.)', data: deltaP1, backgroundColor: '#FF8C00' }}]
        }},
        options: {{ responsive: true, maintainAspectRatio: false }}
      }});

      // Tela 3: Gráficos P2 (Maior e Menor)
      const sigP2 = DATA.p2.filter(r => r.qt_ingressante >= 50);
      const topMaior = [...sigP2].sort((a,b) => b.tda - a.tda).slice(0, 5);
      const topMenor = [...sigP2].sort((a,b) => a.tda - b.tda).slice(0, 5);

      new Chart(document.getElementById('chart-p2-maior'), {{
        type: 'bar',
        data: {{
          labels: topMaior.map(r => r.NO_CINE_ROTULO),
          datasets: [{{ label: 'Desistência (TDA %)', data: topMaior.map(r => r.tda), backgroundColor: '#DC3545' }}]
        }},
        options: {{ indexAxis: 'y', responsive: true, maintainAspectRatio: false }}
      }});

      new Chart(document.getElementById('chart-p2-menor'), {{
        type: 'bar',
        data: {{
          labels: topMenor.map(r => r.NO_CINE_ROTULO),
          datasets: [{{ label: 'Desistência (TDA %)', data: topMenor.map(r => r.tda), backgroundColor: '#28A745' }}]
        }},
        options: {{ indexAxis: 'y', responsive: true, maintainAspectRatio: false }}
      }});

      // Tela 4: Gráficos P3
      const yearsP3 = [2021, 2022, 2023, 2024];
      const segmentsP3 = [...new Set(DATA.p3.map(r => r.segmento))];
      const colorsP3 = ['#1A2B5E', '#0066CC', '#FFC107', '#E83E8C'];

      new Chart(document.getElementById('chart-p3-mat'), {{
        type: 'line',
        data: {{
          labels: yearsP3,
          datasets: segmentsP3.map((seg, i) => ({{
            label: seg,
            data: yearsP3.map(y => DATA.p3.find(r => r.nu_ano_censo === y && r.segmento === seg)?.qt_mat || 0),
            borderColor: colorsP3[i % colorsP3.length],
            borderWidth: 3,
            tension: 0.2
          }}))
        }},
        options: {{ responsive: true, maintainAspectRatio: false }}
      }});

      new Chart(document.getElementById('chart-p3-desv'), {{
        type: 'bar',
        data: {{
          labels: yearsP3,
          datasets: segmentsP3.map((seg, i) => ({{
            label: seg,
            data: yearsP3.map(y => DATA.p3.find(r => r.nu_ano_censo === y && r.segmento === seg)?.pct_desvinculacao || 0),
            backgroundColor: colorsP3[i % colorsP3.length]
          }}))
        }},
        options: {{ responsive: true, maintainAspectRatio: false }}
      }});

      // Tela 5: Gráficos P4
      const p4Evaluated = DATA.p4.filter(r => r.cpc_continuo !== null && !isNaN(r.cpc_continuo));
      new Chart(document.getElementById('chart-p4-scatter'), {{
        type: 'scatter',
        data: {{
          datasets: [{{
            label: 'Cursos Avaliados (CPC vs TDA)',
            data: p4Evaluated.map(r => ({{ x: r.cpc_continuo, y: r.tda }})),
            backgroundColor: '#0066CC'
          }}]
        }},
        options: {{
          responsive: true,
          maintainAspectRatio: false,
          scales: {{
            x: {{ title: {{ display: true, text: 'CPC Contínuo' }} }},
            y: {{ title: {{ display: true, text: 'Desistência Acumulada (%)' }} }}
          }}
        }}
      }});

      const faixas = ['1', '2', '3', '4', '5', 'Sem CPC'];
      const faixasData = faixas.map(f => {{
        const subs = DATA.p4.filter(r => String(r.faixa_cpc) === f);
        if (!subs.length) return 0;
        return (subs.reduce((acc, r) => acc + (r.tda * r.qt_ingressante), 0) / subs.reduce((acc, r) => acc + r.qt_ingressante, 0)).toFixed(1);
      }});
      new Chart(document.getElementById('chart-p4-faixas'), {{
        type: 'bar',
        data: {{
          labels: faixas,
          datasets: [{{ label: 'TDA Ponderada (%)', data: faixasData, backgroundColor: ['#DC3545', '#FFC107', '#0066CC', '#28A745', '#6F42C1', '#6C757D'] }}]
        }},
        options: {{ responsive: true, maintainAspectRatio: false }}
      }});

      // Tela 6: Gráficos P5 Licenciaturas
      new Chart(document.getElementById('chart-p5-tda'), {{
        type: 'bar',
        data: {{
          labels: DATA.p5.map(r => r.NO_CINE_ROTULO),
          datasets: [{{ label: 'Desistência (TDA %)', data: DATA.p5.map(r => r.tda), backgroundColor: '#DC3545' }}]
        }},
        options: {{ indexAxis: 'y', responsive: true, maintainAspectRatio: false }}
      }});

      new Chart(document.getElementById('chart-p5-enade'), {{
        type: 'bar',
        data: {{
          labels: DATA.p5.map(r => r.NO_CINE_ROTULO),
          datasets: [{{ label: '% Proficiente Enade 2025', data: DATA.p5.map(r => r.enade_proficiente_pct), backgroundColor: '#0066CC' }}]
        }},
        options: {{ indexAxis: 'y', responsive: true, maintainAspectRatio: false }}
      }});

      // Tela 7: Gráfico B1 Polos
      const topPolos = [...DATA.b1].filter(r => r.vagas_presenciais > 0).sort((a,b) => b.vagas_por_100_jovens - a.vagas_por_100_jovens).slice(0, 10);
      new Chart(document.getElementById('chart-b1-polos'), {{
        type: 'bar',
        data: {{
          labels: topPolos.map(r => r.no_municipio),
          datasets: [{{ label: 'Vagas por 100 Jovens', data: topPolos.map(r => r.vagas_por_100_jovens), backgroundColor: '#0066CC' }}]
        }},
        options: {{ indexAxis: 'y', responsive: true, maintainAspectRatio: false }}
      }});

      // Tela 8: Gráficos B2 Financiamento
      new Chart(document.getElementById('chart-b2-evol'), {{
        type: 'line',
        data: {{
          labels: DATA.b2.map(r => r.nu_ano_censo),
          datasets: [
            {{ label: '% FIES', data: DATA.b2.map(r => r.pct_fies), borderColor: '#0066CC', borderWidth: 3 }},
            {{ label: '% ProUni', data: DATA.b2.map(r => r.pct_prouni), borderColor: '#6F42C1', borderWidth: 3 }},
            {{ label: '% Apoio Total', data: DATA.b2.map(r => r.pct_apoio_total), borderColor: '#28A745', borderWidth: 3, borderDash: [5, 5] }}
          ]
        }},
        options: {{ responsive: true, maintainAspectRatio: false }}
      }});

      new Chart(document.getElementById('chart-b2-comp'), {{
        type: 'bar',
        data: {{
          labels: DATA.b2.map(r => r.nu_ano_censo),
          datasets: [
            {{ label: 'Financiados (Desvinculação %)', data: DATA.b2.map(r => r.taxa_desvinculacao_financiados), backgroundColor: '#28A745' }},
            {{ label: 'Não Financiados (Desvinculação %)', data: DATA.b2.map(r => r.taxa_desvinculacao_nao_financiados), backgroundColor: '#DC3545' }}
          ]
        }},
        options: {{ responsive: true, maintainAspectRatio: false }}
      }});
    }}

    document.addEventListener('DOMContentLoaded', () => {{
      renderTables();
      initCharts();
    }});
  </script>
</body>
</html>
"""
    return html_content

def main():
    data = load_data()
    html_content = generate_html(data)

    # 1. Salva no projeto (na raiz e em outputs/)
    dashboard_path = PROJECT_ROOT / "dashboard.html"
    outputs_html = OUTPUTS_DIR / "dashboard.html"
    dashboard_path.write_text(html_content, encoding="utf-8")
    outputs_html.write_text(html_content, encoding="utf-8")

    # 2. Salva no diretório de artefatos
    artifact_path = ARTIFACT_DIR / "dashboard.html"
    artifact_path.write_text(html_content, encoding="utf-8")

    print(f"HTML Dashboard gerado em:")
    print(f" - {dashboard_path}")
    print(f" - {outputs_html}")
    print(f" - {artifact_path}")

if __name__ == "__main__":
    main()
