#!/usr/bin/env python3
"""Gera um dashboard HTML consultável a partir dos resultados JSON."""
from __future__ import annotations

import html
import json
import platform
import subprocess
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent
RESULTS = ROOT / "resultados"
OUTPUT = RESULTS / "comparacao.html"


def load_rows() -> list[dict]:
    rows: list[dict] = []
    for path in sorted(RESULTS.glob("*.json")):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if not isinstance(data, dict):
            continue
        benchmark_version = data.get("benchmark_version", "—")
        provider = data.get("provider", data.get("environment", {}).get("provider", "—"))
        for model in data.get("models", []):
            tests = [t for t in model.get("tests", []) if "score" in t]
            if not tests:
                continue
            summary = model.get("summary", {})
            metrics = model.get("summary_metrics", {})
            rows.append({
                "arquivo": path.name,
                "modelo": model.get("model", model.get("model_id", "<sem modelo>")),
                "provider": provider,
                "benchmark_version": benchmark_version,
                "moodle": summary.get("Moodle", "—"),
                "python": summary.get("Python", "—"),
                "n8n": summary.get("n8n", "—"),
                "overall": summary.get("overall", "—"),
                "testes": metrics.get("tests_completed", len(tests)),
                "tokens": metrics.get("total_tokens", "—"),
                "input_tokens": metrics.get("input_tokens", "—"),
                "output_tokens": metrics.get("output_tokens", "—"),
                "reasoning_tokens": metrics.get("reasoning_tokens", "—"),
                "latencia": metrics.get("avg_latency_seconds", "—"),
                "tokens_per_second": metrics.get("avg_tokens_per_second", "—"),
                "custo": metrics.get("total_cost", model.get("total_cost", "—")),
                "tests_detail": [
                    {
                        "id": t.get("id", "—"),
                        "domain": t.get("domain", "—"),
                        "score": t.get("score", "—"),
                        "input_tokens": t.get("input_tokens", "—"),
                        "output_tokens": t.get("output_tokens", "—"),
                        "total_tokens": t.get("total_tokens", "—"),
                        "latency": t.get("latency_seconds", t.get("latency", "—")),
                        "cost": t.get("cost", "—"),
                        "finish_reason": t.get("finish_reason", "—"),
                    }
                    for t in tests
                ],
            })
    return sorted(rows, key=lambda row: (-(row["overall"] if isinstance(row["overall"], (int, float)) else -1), row["modelo"]))


def environment_info() -> list[tuple[str, str]]:
    chip = "indisponível"
    try:
        chip = subprocess.run(
            ["sysctl", "-n", "machdep.cpu.brand_string"],
            capture_output=True, text=True, check=False,
        ).stdout.strip() or chip
        if chip == "indisponível":
            hardware = subprocess.run(
                ["system_profiler", "SPHardwareDataType"],
                capture_output=True, text=True, check=False,
            ).stdout
            chip = next((line.split(":", 1)[1].strip() for line in hardware.splitlines() if line.strip().startswith("Chip:")), chip)
    except OSError:
        pass
    return [
        ("Provedor", "LM Studio"),
        ("Hardware", f"{chip} · 24 GB RAM"),
        ("Sistema", f"{platform.system()} {platform.mac_ver()[0] or platform.release()}"),
        ("Python", sys.version.split()[0]),
        ("Gerado em", datetime.now().strftime("%d/%m/%Y %H:%M")),
    ]


def fmt(value: object) -> str:
    if isinstance(value, float):
        return f"{value:.2f}"
    return str(value)


def main() -> None:
    rows = load_rows()
    environment = environment_info()
    payload = json.dumps(rows, ensure_ascii=False).replace("</", "<\\/")
    env_html = " · ".join(f"<strong>{html.escape(name)}:</strong> {html.escape(value)}" for name, value in environment)
    page = f'''<!doctype html>
<html lang="pt-BR">
<head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>AI Benchmark — Dashboard</title>
<style>
:root {{ color-scheme: light; --bg:#f5f7fb; --panel:#fff; --ink:#172033; --muted:#657085; --line:#e3e7ee; --accent:#1d4ed8; }}
* {{ box-sizing:border-box }} body {{ margin:0; font:15px/1.5 system-ui,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif; background:var(--bg); color:var(--ink) }}
header {{ padding:34px max(24px,calc((100vw - 1280px)/2)) 22px; background:var(--ink); color:white }}
header h1 {{ margin:0 0 4px; font-size:28px }} header p {{ margin:0; color:#c8d0dd }}
main {{ max-width:1280px; margin:24px auto; padding:0 24px }}
.toolbar,.panel {{ background:var(--panel); border:1px solid var(--line); border-radius:14px; padding:18px; margin-bottom:18px }}
.toolbar {{ display:grid; grid-template-columns:1fr 180px 180px auto; gap:12px; align-items:end }}
label {{ display:block; font-size:12px; font-weight:700; color:var(--muted); margin-bottom:5px }}
input,select,button {{ width:100%; padding:10px 11px; border:1px solid #ccd3df; border-radius:9px; background:white; color:var(--ink); font:inherit }}
button {{ cursor:pointer; font-weight:700; background:var(--ink); color:white; border-color:var(--ink) }}
.stats {{ display:grid; grid-template-columns:repeat(4,1fr); gap:12px; margin-bottom:18px }}
.stat {{ background:white; border:1px solid var(--line); border-radius:12px; padding:15px }} .stat b {{ display:block; font-size:23px }} .stat span {{ color:var(--muted); font-size:12px }}
.table-wrap {{ overflow:auto }} table {{ border-collapse:collapse; width:100%; min-width:1000px }} th,td {{ padding:11px 12px; border-bottom:1px solid var(--line); text-align:right; white-space:nowrap }} th {{ text-align:right; background:#f0f3f8; position:sticky;top:0;z-index:2 }} th:first-child,td:first-child {{ text-align:left; position:sticky;left:0;z-index:1 }} td:first-child {{ background:white; font-weight:700 }} tr:hover td {{ background:#f7faff }} tr:hover td:first-child {{ background:#f7faff }}
.score {{ font-weight:800 }} .muted {{ color:var(--muted) }} .link {{ color:var(--accent); cursor:pointer; text-decoration:underline; background:none;border:0;padding:0;width:auto }}
.detail {{ display:none; margin-top:18px }} .detail.show {{ display:block }} .detail-grid {{ display:grid; grid-template-columns:repeat(4,1fr); gap:10px; margin-bottom:16px }} .mini {{ padding:12px; background:#f7f8fb; border-radius:10px }} .mini b {{ display:block;font-size:18px }}
.detail table {{ min-width:700px }} .notice {{ color:var(--muted); font-size:13px }}
@media(max-width:800px) {{ .toolbar,.stats,.detail-grid {{ grid-template-columns:1fr }} main {{ padding:0 14px }} header {{ padding-left:14px;padding-right:14px }} }}
</style>
</head>
<body>
<header><h1>AI Benchmark</h1><p>Dashboard consultável das execuções registradas</p></header>
<main>
<section class="toolbar">
  <div><label for="search">Modelo</label><input id="search" placeholder="Filtrar por modelo..." oninput="render()"></div>
  <div><label for="domain">Domínio</label><select id="domain" onchange="render()"><option value="all">Todos</option><option value="Moodle">Moodle</option><option value="Python">Python</option><option value="n8n">n8n</option></select></div>
  <div><label for="provider">Provedor</label><select id="provider" onchange="render()"><option value="all">Todos</option></select></div>
  <div><button onclick="clearFilters()">Limpar filtros</button></div>
</section>
<section class="stats">
  <div class="stat"><b id="count">0</b><span>modelos / execuções</span></div>
  <div class="stat"><b id="best">—</b><span>melhor geral observado</span></div>
  <div class="stat"><b id="tokens">—</b><span>tokens nas execuções exibidas</span></div>
  <div class="stat"><b id="cost">—</b><span>custo informado, quando disponível</span></div>
</section>
<section class="panel">
  <div class="table-wrap"><table><thead><tr><th>Modelo</th><th>Moodle</th><th>Python</th><th>n8n</th><th>Geral</th><th>Testes</th><th>Tokens</th><th>Latência média</th><th>Tokens/s</th><th>Custo</th><th>Detalhes</th></tr></thead><tbody id="tbody"></tbody></table></div>
  <p id="empty" class="notice" style="display:none">Nenhum resultado corresponde aos filtros.</p>
</section>
<section id="detail" class="panel detail"></section>
<p class="notice">Os resultados refletem as condições registradas em cada execução. Uma execução isolada não deve ser interpretada como prova de superioridade geral entre modelos.</p>
</main>
<script>
const DATA = {payload};
const providers = [...new Set(DATA.map(r => r.provider).filter(Boolean))].sort();
const providerSelect = document.getElementById('provider');
providers.forEach(p => providerSelect.insertAdjacentHTML('beforeend', `<option value="${esc(p)}">${esc(p)}</option>`));
function esc(v) {{ return String(v ?? '—').replace(/[&<>"']/g, c => ({{'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}}[c])); }}
function num(v) {{ return typeof v === 'number' ? v : null; }}
function fmt(v) {{ return typeof v === 'number' ? v.toLocaleString('pt-BR',{{maximumFractionDigits:2}}) : esc(v); }}
function filtered() {{
 const q=document.getElementById('search').value.toLowerCase(); const d=document.getElementById('domain').value; const p=providerSelect.value;
 return DATA.filter(r => (!q || String(r.modelo).toLowerCase().includes(q)) && (p==='all'||r.provider===p) && (d==='all'||num(r[d.toLowerCase()])!==null || r[d.toLowerCase()]!=='—'));
}}
function render() {{
 const rows=filtered(); const body=document.getElementById('tbody'); body.innerHTML='';
 rows.forEach((r,i)=>{{ const tr=document.createElement('tr'); tr.innerHTML=`<td>${{esc(r.modelo)}}</td><td>${{fmt(r.moodle)}}</td><td>${{fmt(r.python)}}</td><td>${{fmt(r.n8n)}}</td><td class="score">${{fmt(r.overall)}}</td><td>${{fmt(r.testes)}}</td><td>${{fmt(r.tokens)}}</td><td>${{fmt(r.latencia)}} s</td><td>${{fmt(r.tokens_per_second)}}</td><td>${{fmt(r.custo)}}</td><td><button class="link" onclick="details(${{DATA.indexOf(r)}})">ver testes</button></td>`; body.appendChild(tr); }});
 document.getElementById('empty').style.display=rows.length?'none':'block'; document.getElementById('count').textContent=rows.length;
 const best=rows.filter(r=>num(r.overall)!==null).sort((a,b)=>b.overall-a.overall)[0]; document.getElementById('best').textContent=best?`${{best.modelo}} · ${{fmt(best.overall)}}`:'—';
 const total=rows.reduce((s,r)=>s+(num(r.tokens)||0),0); document.getElementById('tokens').textContent=total?total.toLocaleString('pt-BR'):'—';
 const costs=rows.map(r=>num(r.custo)).filter(v=>v!==null); document.getElementById('cost').textContent=costs.length?costs.reduce((a,b)=>a+b,0).toLocaleString('pt-BR',{{style:'currency',currency:'USD'}}):'—';
}}
function details(index) {{ const r=DATA[index]; const d=document.getElementById('detail'); const tests=r.tests_detail||[]; d.innerHTML=`<h2>${{esc(r.modelo)}}</h2><div class="detail-grid"><div class="mini"><span class="muted">Provedor</span><b>${{esc(r.provider)}}</b></div><div class="mini"><span class="muted">Benchmark</span><b>${{esc(r.benchmark_version)}}</b></div><div class="mini"><span class="muted">Entrada</span><b>${{fmt(r.input_tokens)}}</b></div><div class="mini"><span class="muted">Saída</span><b>${{fmt(r.output_tokens)}}</b></div></div><div class="table-wrap"><table><thead><tr><th>Teste</th><th>Domínio</th><th>Score</th><th>Entrada</th><th>Saída</th><th>Total</th><th>Latência</th><th>Custo</th><th>Finalização</th></tr></thead><tbody>${{tests.map(t=>`<tr><td>${{esc(t.id)}}</td><td>${{esc(t.domain)}}</td><td class="score">${{fmt(t.score)}}</td><td>${{fmt(t.input_tokens)}}</td><td>${{fmt(t.output_tokens)}}</td><td>${{fmt(t.total_tokens)}}</td><td>${{fmt(t.latency)}} s</td><td>${{fmt(t.cost)}}</td><td>${{esc(t.finish_reason)}}</td></tr>`).join('')}}</tbody></table></div><p><button onclick="document.getElementById('detail').classList.remove('show')">Fechar detalhes</button></p>`; d.classList.add('show'); d.scrollIntoView({{behavior:'smooth',block:'start'}}); }}
function clearFilters() {{ document.getElementById('search').value=''; document.getElementById('domain').value='all'; providerSelect.value='all'; render(); }}
render();
</script>
</body></html>'''
    OUTPUT.write_text(page, encoding="utf-8")
    print(f"Dashboard gerado: {OUTPUT}")
    print(f"Execuções/modelos válidos: {len(rows)}")


if __name__ == "__main__":
    main()
