#!/usr/bin/env python3
"""Gera o dashboard HTML a partir dos JSONs de resultados do benchmark."""
from __future__ import annotations

import html
import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent
RESULTS = ROOT / "resultados"
OUTPUT = RESULTS / "comparacao.html"


def number(value):
    return value if isinstance(value, (int, float)) and not isinstance(value, bool) else None


def load_rows() -> list[dict]:
    rows: list[dict] = []
    for path in sorted(RESULTS.glob("run-*.json")):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if not isinstance(data, dict):
            continue

        provider = data.get("provider", "—")
        benchmark_version = data.get("benchmark_version", "—")
        generated_at = data.get("generated_at", "—")
        configuration = data.get("configuration", {}) or {}

        for model in data.get("models", []):
            if not isinstance(model, dict):
                continue
            tests = [t for t in model.get("tests", []) if isinstance(t, dict) and "score" in t]
            if not tests:
                continue

            summary = model.get("summary", {}) or {}
            overall = number(summary.get("overall"))
            # Modelos com execução registrada, mas pontuação geral zero, ficam
            # fora do quadro público até serem reavaliados.
            if overall is not None and overall <= 0:
                continue
            summary_metrics = model.get("summary_metrics", {}) or {}
            total_tokens = summary_metrics.get("total_tokens")
            if total_tokens is None:
                total_tokens = sum((t.get("metrics", {}) or {}).get("total_tokens") or 0 for t in tests)

            latencies = [number((t.get("metrics", {}) or {}).get("elapsed")) for t in tests]
            latencies = [v for v in latencies if v is not None]
            speeds = [number((t.get("metrics", {}) or {}).get("tokens_per_second")) for t in tests]
            speeds = [v for v in speeds if v is not None]

            input_tokens = sum((t.get("metrics", {}) or {}).get("prompt_tokens") or 0 for t in tests)
            output_tokens = sum((t.get("metrics", {}) or {}).get("completion_tokens") or 0 for t in tests)
            reasoning_tokens = sum((t.get("metrics", {}) or {}).get("reasoning_tokens") or 0 for t in tests)
            costs = [number((t.get("metrics", {}) or {}).get("cost")) for t in tests]
            costs = [v for v in costs if v is not None]

            rows.append({
                "arquivo": path.name,
                "modelo": model.get("model", "<sem modelo>"),
                "model_returned": next((t.get("model_returned") for t in tests if t.get("model_returned")), None),
                "provider": provider,
                "benchmark_version": benchmark_version,
                "generated_at": generated_at,
                "moodle": summary.get("Moodle", "—"),
                "python": summary.get("Python", "—"),
                "n8n": summary.get("n8n", "—"),
                "overall": summary.get("overall", "—"),
                "testes": summary_metrics.get("tests_completed", len(tests)),
                "tokens": total_tokens,
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "reasoning_tokens": reasoning_tokens,
                "latencia": summary_metrics.get("avg_latency_seconds") if summary_metrics.get("avg_latency_seconds") is not None else (sum(latencies) / len(latencies) if latencies else None),
                "tokens_per_second": (sum(speeds) / len(speeds)) if speeds else None,
                "custo": summary_metrics.get("total_cost") if summary_metrics.get("total_cost") is not None else (sum(costs) if costs else None),
                "configuration": configuration,
                "tests_detail": [
                    {
                        "id": t.get("test_id", "—"),
                        "domain": t.get("domain", "—"),
                        "score": t.get("score", "—"),
                        "input_tokens": (t.get("metrics", {}) or {}).get("prompt_tokens", "—"),
                        "output_tokens": (t.get("metrics", {}) or {}).get("completion_tokens", "—"),
                        "reasoning_tokens": (t.get("metrics", {}) or {}).get("reasoning_tokens", "—"),
                        "total_tokens": (t.get("metrics", {}) or {}).get("total_tokens", "—"),
                        "latency": (t.get("metrics", {}) or {}).get("elapsed", "—"),
                        "tokens_per_second": (t.get("metrics", {}) or {}).get("tokens_per_second", "—"),
                        "cost": (t.get("metrics", {}) or {}).get("cost", "—"),
                        "finish_reason": t.get("finish_reason", "—"),
                        "model_returned": t.get("model_returned", "—"),
                        "missing": t.get("missing", []),
                        "error": t.get("error"),
                    }
                    for t in tests
                ],
            })

    return sorted(rows, key=lambda r: (-(number(r.get("overall")) if number(r.get("overall")) is not None else -1), str(r.get("modelo"))))


def main() -> None:
    rows = load_rows()
    payload = json.dumps(rows, ensure_ascii=False).replace("</", "<\\/")

    page = f'''<!doctype html>
<html lang="pt-BR">
<head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>AI Benchmark — Dashboard</title>
<style>
:root {{ color-scheme:light; --bg:#f5f7fb; --panel:#fff; --ink:#172033; --muted:#657085; --line:#e3e7ee; --accent:#1d4ed8; }}
* {{ box-sizing:border-box }} body {{ margin:0; font:15px/1.5 system-ui,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif; background:var(--bg); color:var(--ink) }}
header {{ padding:34px max(24px,calc((100vw - 1280px)/2)) 22px; background:var(--ink); color:white }} header h1 {{ margin:0 0 4px; font-size:28px }} header p {{ margin:0; color:#c8d0dd }}
main {{ max-width:1280px; margin:24px auto; padding:0 24px }} .toolbar,.panel {{ background:var(--panel); border:1px solid var(--line); border-radius:14px; padding:18px; margin-bottom:18px }}
.toolbar {{ display:grid; grid-template-columns:1fr 180px 180px auto; gap:12px; align-items:end }} label {{ display:block; font-size:12px; font-weight:700; color:var(--muted); margin-bottom:5px }}
input,select,button {{ width:100%; padding:10px 11px; border:1px solid #ccd3df; border-radius:9px; background:white; color:var(--ink); font:inherit }} button {{ cursor:pointer; font-weight:700; background:var(--ink); color:white; border-color:var(--ink) }}
.stats {{ display:grid; grid-template-columns:repeat(4,1fr); gap:12px; margin-bottom:18px }} .stat {{ background:white; border:1px solid var(--line); border-radius:12px; padding:15px }} .stat b {{ display:block; font-size:20px }} .stat span {{ color:var(--muted); font-size:12px }}
.table-wrap {{ overflow:auto }} table {{ border-collapse:collapse; width:100%; min-width:1080px }} th,td {{ padding:11px 12px; border-bottom:1px solid var(--line); text-align:right; white-space:nowrap }} th {{ background:#f0f3f8; position:sticky; top:0; z-index:2 }} th:first-child,td:first-child {{ text-align:left; position:sticky; left:0; z-index:1 }} td:first-child {{ background:white; font-weight:700 }} tr:hover td {{ background:#f7faff }} tr:hover td:first-child {{ background:#f7faff }}
.score {{ font-weight:800 }} .muted,.notice {{ color:var(--muted) }} .link {{ color:var(--accent); cursor:pointer; text-decoration:underline; background:none; border:0; padding:0; width:auto }}
.detail {{ display:none; margin-top:18px }} .detail.show {{ display:block }} .detail-grid {{ display:grid; grid-template-columns:repeat(5,1fr); gap:10px; margin-bottom:16px }} .mini {{ padding:12px; background:#f7f8fb; border-radius:10px }} .mini b {{ display:block; font-size:17px; overflow-wrap:anywhere }} .notice {{ font-size:13px }}
@media(max-width:800px) {{ .toolbar,.stats,.detail-grid {{ grid-template-columns:1fr }} main {{ padding:0 14px }} header {{ padding-left:14px;padding-right:14px }} }}
</style>
</head>
<body>
<header><h1>AI Benchmark</h1><p>Resultados das execuções registradas — qualidade, eficiência e custo</p></header>
<main>
<section class="toolbar">
<div><label for="search">Modelo</label><input id="search" placeholder="Filtrar por modelo..." oninput="render()"></div>
<div><label for="domain">Domínio</label><select id="domain" onchange="render()"><option value="all">Todos</option><option value="Moodle">Moodle</option><option value="Python">Python</option><option value="n8n">n8n</option></select></div>
<div><label for="provider">Provedor</label><select id="provider" onchange="render()"><option value="all">Todos</option></select></div>
<div><button onclick="clearFilters()">Limpar filtros</button></div>
</section>
<section class="stats"><div class="stat"><b id="count">0</b><span>execuções exibidas</span></div><div class="stat"><b id="best">—</b><span>melhor geral observado</span></div><div class="stat"><b id="tokens">—</b><span>tokens nas execuções exibidas</span></div><div class="stat"><b id="cost">—</b><span>custo informado</span></div></section>
<section class="panel"><div class="table-wrap"><table><thead><tr><th>Modelo</th><th>Moodle</th><th>Python</th><th>n8n</th><th>Geral</th><th>Testes</th><th>Tokens</th><th>Latência média</th><th>Tokens/s</th><th>Custo</th><th>Detalhes</th></tr></thead><tbody id="tbody"></tbody></table></div><p id="empty" class="notice" style="display:none">Nenhum resultado corresponde aos filtros.</p></section>
<section id="detail" class="panel detail"></section>
<p class="notice">O dashboard é gerado exclusivamente a partir dos arquivos <code>resultados/run-*.json</code>. Uma execução isolada não deve ser interpretada como prova de superioridade geral entre modelos.</p>
</main>
<script>
const DATA = {payload};
const providers = [...new Set(DATA.map(r => r.provider).filter(Boolean))].sort();
const providerSelect = document.getElementById('provider');
providers.forEach(p => providerSelect.insertAdjacentHTML('beforeend', `<option value="${{esc(p)}}">${{esc(p)}}</option>`));
function esc(v) {{ return String(v ?? '—').replace(/[&<>"']/g, c => ({{'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}}[c])); }}
function fmt(v) {{ return typeof v === 'number' ? v.toLocaleString('pt-BR',{{maximumFractionDigits:2}}) : esc(v); }}
function filtered() {{ const q=document.getElementById('search').value.toLowerCase(); const d=document.getElementById('domain').value; const p=providerSelect.value; return DATA.filter(r => (!q || String(r.modelo).toLowerCase().includes(q)) && (p==='all'||r.provider===p) && (d==='all'||r[d.toLowerCase()] !== '—')); }}
function render() {{ const rows=filtered(); const body=document.getElementById('tbody'); body.innerHTML=''; rows.forEach(r=>{{ const tr=document.createElement('tr'); tr.innerHTML=`<td>${{esc(r.modelo)}}</td><td>${{fmt(r.moodle)}}</td><td>${{fmt(r.python)}}</td><td>${{fmt(r.n8n)}}</td><td class="score">${{fmt(r.overall)}}</td><td>${{fmt(r.testes)}}</td><td>${{fmt(r.tokens)}}</td><td>${{fmt(r.latencia)}} s</td><td>${{fmt(r.tokens_per_second)}}</td><td>${{r.custo===null||r.custo===undefined?'—':fmt(r.custo)}}</td><td><button class="link" onclick="details(${{DATA.indexOf(r)}})">ver execução</button></td>`; body.appendChild(tr); }}); document.getElementById('empty').style.display=rows.length?'none':'block'; document.getElementById('count').textContent=rows.length; const best=rows.filter(r=>typeof r.overall==='number').sort((a,b)=>b.overall-a.overall)[0]; document.getElementById('best').textContent=best?`${{best.modelo}} · ${{fmt(best.overall)}}`:'—'; const total=rows.reduce((s,r)=>s+(typeof r.tokens==='number'?r.tokens:0),0); document.getElementById('tokens').textContent=total?total.toLocaleString('pt-BR'):'—'; const costs=rows.map(r=>typeof r.custo==='number'?r.custo:null).filter(v=>v!==null); document.getElementById('cost').textContent=costs.length?costs.reduce((a,b)=>a+b,0).toLocaleString('pt-BR',{{style:'currency',currency:'USD'}}):'—'; }}
function details(i) {{ const r=DATA[i],d=document.getElementById('detail'),tests=r.tests_detail||[],c=r.configuration||{{}}; d.innerHTML=`<h2>${{esc(r.modelo)}}</h2><div class="detail-grid"><div class="mini"><span class="muted">Provedor</span><b>${{esc(r.provider)}}</b></div><div class="mini"><span class="muted">Benchmark</span><b>${{esc(r.benchmark_version)}}</b></div><div class="mini"><span class="muted">Tokens</span><b>${{fmt(r.tokens)}}</b></div><div class="mini"><span class="muted">Latência</span><b>${{fmt(r.latencia)}} s</b></div><div class="mini"><span class="muted">Custo</span><b>${{r.custo===null||r.custo===undefined?'—':fmt(r.custo)}}</b></div></div><p class="notice">Execução: ${{esc(r.generated_at)}} · arquivo: ${{esc(r.arquivo)}} · parâmetros: temperature=${{esc(c.temperature)}}, max_tokens=${{esc(c.max_tokens)}}, top_p=${{esc(c.top_p)}}, top_k=${{esc(c.top_k)}}, seed=${{esc(c.seed)}}, reasoning_effort=${{esc(c.reasoning_effort)}}</p><div class="table-wrap"><table><thead><tr><th>Teste</th><th>Domínio</th><th>Score</th><th>Entrada</th><th>Saída</th><th>Reasoning</th><th>Total</th><th>Latência</th><th>Tokens/s</th><th>Custo</th><th>Finalização</th></tr></thead><tbody>${{tests.map(t=>`<tr><td>${{esc(t.id)}}</td><td>${{esc(t.domain)}}</td><td class="score">${{fmt(t.score)}}</td><td>${{fmt(t.input_tokens)}}</td><td>${{fmt(t.output_tokens)}}</td><td>${{fmt(t.reasoning_tokens)}}</td><td>${{fmt(t.total_tokens)}}</td><td>${{fmt(t.latency)}} s</td><td>${{fmt(t.tokens_per_second)}}</td><td>${{fmt(t.cost)}}</td><td>${{esc(t.finish_reason)}}</td></tr>`).join('')}}</tbody></table></div><p><button onclick="d.classList.remove('show')">Fechar</button></p>`; d.classList.add('show'); d.scrollIntoView({{behavior:'smooth',block:'start'}}); }}
function clearFilters() {{ document.getElementById('search').value=''; document.getElementById('domain').value='all'; providerSelect.value='all'; render(); }}
render();
</script>
</body></html>'''

    OUTPUT.write_text(page, encoding="utf-8")
    print(f"Dashboard gerado: {OUTPUT}")
    print(f"Execuções/modelos válidos: {len(rows)}")


if __name__ == "__main__":
    main()
