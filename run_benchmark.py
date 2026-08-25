#!/usr/bin/env python3
"""
Benchmark rápido — testa os modelos mais relevantes para Moodle/Python/n8n.
"""
import json, time, sys, os
from datetime import datetime

try:
    import requests
except ImportError:
    os.system(f"{sys.executable} -m pip install requests -q")
    import requests

BASE = "http://localhost:1234"
TIMEOUT = 180
RUNS = 1
MAX_TOK = 2048
RESULTS_DIR = os.path.join(os.path.dirname(__file__), "resultados")
os.makedirs(RESULTS_DIR, exist_ok=True)

# Modelos priorizados para 24GB Mac — foco em código
PRIORITY_MODELS = [
    "qwen/qwen2.5-coder-14b",          # O melhor para código
    "google/gemma-4-12b",               # Generalista rápido
    "qwen/qwen3.5-9b",                 # Qwen geral
    "qwen/qwen3.6-27b",                # Qwen grande
    "openai/gpt-oss-20b",               # GPT open source
    "google/gemma-4-26b-a4b",           # Gemma MoE
    "prism-ml/bonsai-27b",              # Bonsai (alternative)
]

PROMPTS = [
    # ── MOODLE (10) ──
    {"id":"m01","d":"Moodle","p":"Quais são os 5 tipos de plugins Moodle mais comuns e onde fica cada um?","k":["activity","block","auth","enrol","local"],"code":False},
    {"id":"m02","d":"Moodle","p":"Crie estrutura de arquivos completa de um block plugin Moodle 'block_notificador'.","k":["version.php","block.php","db/access.php","lang/en/"],"code":False},
    {"id":"m03","d":"Moodle","p":"Escreva version.php para plugin 'local_notificador' que requer Moodle 4.0.","k":["$plugin->version","$plugin->requires","$plugin->component","local_notificador"],"code":True,"cm":"<?php"},
    {"id":"m04","d":"Moodle","p":"Crie install.xml XMLDB para tabela 'notificacoes': id, userid, titulo, mensagem, lida, timecreated.","k":["TABLE NAME","FIELD NAME","userid","titulo","mensagem","PRIMARY KEY"],"code":True,"cm":"XMLDB"},
    {"id":"m05","d":"Moodle","p":"Mostre $DB do Moodle: insert_record, get_records, update_record com tabela 'user'.","k":["global $DB","insert_record","get_records","update_record"],"code":True,"cm":"global $DB"},
    {"id":"m06","d":"Moodle","p":"Crie db/external.php para External Function 'obter_notificacoes'.","k":["external_functions","external_description","PARAM_","returns"],"code":True,"cm":"<?php"},
    {"id":"m07","d":"Moodle","p":"Crie Event 'notificacao_enviada' no Moodle. Classe + db/events.php.","k":["extends","core\\event","get_name","get_description"],"code":True,"cm":"<?php"},
    {"id":"m08","d":"Moodle","p":"Crie db/access.php com 3 capabilities: local/notificador:send, manage, view.","k":["$capabilities","risk","captype","contextlevel"],"code":True,"cm":"$capabilities"},
    {"id":"m09","d":"Moodle","p":"Crie lang/en/local_notificador.php com strings.","k":["$string","notificador","send","manage","view"],"code":True,"cm":"$string"},
    {"id":"m10","d":"Moodle","p":"Identifique erros: require_once('config.php'); defined('MOODLE_INTERNAL')||die(); $DB->Execute(\"INSERT INTO foo VALUES ('$_GET[name])'); echo $_GET['content'];","k":["injection","XSS","SQL","$_GET","sanitize","die"],"code":False},
    # ── PYTHON (10) ──
    {"id":"p01","d":"Python","p":"Script Python completo: consumir API Moodle para listar cursos, com token e tratamento de erros.","k":["requests","get","json","token","except","courses"],"code":True,"cm":"import"},
    {"id":"p02","d":"Python","p":"Autenticação na API Moodle com token em Python. Obtenção e uso do token.","k":["token","wsfunction","wstoken","api/moodle"],"code":True,"cm":"import"},
    {"id":"p03","d":"Python","p":"Função Python: receber JSON Moodle (usuários) → extrair nome, email, último login com validação.","k":["json","get","fullname","email","lastaccess","def "],"code":True,"cm":"def "},
    {"id":"p04","d":"Python","p":"POST Python: retries (3x), timeout 30s, exponential backoff, log.","k":["requests.post","retry","timeout","backoff","time.sleep","except"],"code":True,"cm":"import"},
    {"id":"p05","d":"Python","p":"Ler CSV (nome,email,curso) e importar via API Moodle. Tratar duplicatas.","k":["csv","reader","requests","duplicate","open("],"code":True,"cm":"import"},
    {"id":"p06","d":"Python","p":"asyncio Python: requisições assíncronas a múltiplas APIs com gather.","k":["async","await","aiohttp","httpx","asyncio","gather"],"code":True,"cm":"import"},
    {"id":"p07","d":"Python","p":"3 práticas para variáveis de ambiente para senhas de API em Python.","k":["dotenv","os.environ","keyring",".env","load_dotenv","getenv"],"code":False},
    {"id":"p08","d":"Python","p":"Logging estruturado Python: JSON, nível por env, handler arquivo + console.","k":["logging","getLogger","Formatter","StreamHandler","FileHandler"],"code":True,"cm":"import logging"},
    {"id":"p09","d":"Python","p":"Validar email, nome (máx 100 chars) e curso antes de enviar para API.","k":["email","validate","raise","ValueError","pydantic","def "],"code":True,"cm":"def "},
    {"id":"p10","d":"Python","p":"Rate limiting Python: token bucket, 10 req/min, espera automática.","k":["time","sleep","rate","limit","token","bucket"],"code":True,"cm":"import"},
    # ── N8N (10) ──
    {"id":"n01","d":"n8n","p":"Workflow n8n JSON: Webhook POST → validar → salvar no banco + error handler.","k":["nodes","connections","webhook","type","position","parameters"],"code":True,"cm":"{"},
    {"id":"n02","d":"n8n","p":"Code node JS n8n: transformar [{nome,email}] → formato email. Filtre inválidos.","k":["$input","all()","return","json","filter","map"],"code":True,"cm":"return"},
    {"id":"n03","d":"n8n","p":"5 expressões n8n: node anterior, env var, IF, formatar data, concatenar.","k":["{{","}}","$json","$node","$env","DateTime"],"code":False},
    {"id":"n04","d":"n8n","p":"HTTP Request n8n para Moodle: URL dinâmica, token headers, JSON body, erro 401/403.","k":["httpRequest","url","method","header","authorization","token"],"code":False},
    {"id":"n05","d":"n8n","p":"IF node n8n: nota>=7 aprova, >=5 recuperação, <5 reprovado.","k":["IF","condition","value","true","false","email"],"code":False},
    {"id":"n06","d":"n8n","p":"Erros em n8n: Error Trigger, retry, Error Workflow, Stop And Error.","k":["errorTrigger","retryOnFail","Error Workflow","stopAndError","errorMessage"],"code":False},
    {"id":"n07","d":"n8n","p":"Loop n8n: processar 100 alunos com Split In Batches. Nota, média, salvar.","k":["SplitInBatches","batch","loop","item","json","merge"],"code":False},
    {"id":"n08","d":"n8n","p":"Credenciais seguras n8n: credential customizada Moodle + HTTP Request.","k":["credential","authentication","header","generic","oauth","apiKey"],"code":False},
    {"id":"n09","d":"n8n","p":"Schedule n8n diário 8h: alunos nota baixa Moodle → email professor.","k":["scheduleTrigger","rule","interval","cron","hour","email","moodle"],"code":False},
    {"id":"n10","d":"n8n","p":"AI Agent n8n: Webhook → LLM responde → salva no banco. AI Agent + tool.","k":["aiAgent","openAi","model","prompt","tool","memory","chatModel"],"code":False},
]


def check():
    try:
        return requests.get(f"{BASE}/v1/models", timeout=5).status_code == 200
    except: return False

def get_models():
    r = requests.get(f"{BASE}/v1/models", timeout=10)
    return [m["id"] for m in r.json().get("data",[]) if "embed" not in m["id"].lower()]

def load_model(mid):
    try:
        return requests.post(f"{BASE}/api/v1/models/load", json={"model":mid}, timeout=300).status_code == 200
    except: return False

def unload_model(mid):
    try: requests.post(f"{BASE}/api/v1/models/unload", json={"model":mid}, timeout=30)
    except: pass

def chat(mid, prompt):
    payload = {
        "model": mid,
        "messages": [
            {"role":"system","content":"Especialista em Moodle (PHP), Python e n8n. Responda em português. Código quando solicitado."},
            {"role":"user","content": prompt},
        ],
        "temperature": 0.2, "max_tokens": MAX_TOK, "stream": False,
    }
    t0 = time.time()
    try:
        r = requests.post(f"{BASE}/v1/chat/completions", json=payload, timeout=TIMEOUT)
        e = time.time()-t0
        if r.status_code != 200: return {"error": f"HTTP {r.status_code}", "elapsed": e}
        d = r.json()
        c = d["choices"][0]["message"]["content"]
        u = d.get("usage",{})
        s = d.get("stats",{})
        return {
            "content": c,
            "prompt_tokens": u.get("prompt_tokens",0),
            "completion_tokens": u.get("completion_tokens",0),
            "tokens_per_second": s.get("tokens_per_second",0),
            "time_to_first_token": s.get("time_to_first_token",0),
            "generation_time": s.get("generation_time",e),
            "elapsed": e,
        }
    except Exception as ex:
        return {"error": str(ex), "elapsed": time.time()-t0}

def evaluate(response, test):
    cl = response.lower()
    score = 0
    missing = []
    kws = test.get("k",[])
    if kws:
        pts = 70/len(kws)
        for kw in kws:
            if kw.lower() in cl: score += pts
            else: missing.append(kw)
    if test.get("code"):
        cm = test.get("cm","")
        if cm and cm.lower() in cl: score += 30
        elif "```" in response: score += 20
        else: missing.append(f"[código:{cm}]")
    else:
        wc = len(response.split())
        if wc > 50: score += 30
        elif wc > 20: score += 20
        elif wc > 5: score += 10
    return {"score": round(min(score,100),1), "missing": missing}


def main():
    print("\n" + "="*70)
    print("  BENCHMARK LM STUDIO — Moodle / Python / n8n")
    print(f"  {datetime.now().strftime('%Y-%m-%d %H:%M')} | Servidor: {BASE}")
    print("="*70)

    if not check():
        print("\n❌ LM Studio não está rodando em", BASE)
        sys.exit(1)

    all_models = get_models()
    print(f"\n📦 {len(all_models)} modelo(s) LLM encontrado(s)")

    # Filtrar apenas modelos prioritários que existem
    to_test = [m for m in PRIORITY_MODELS if m in all_models]
    extras = [m for m in all_models if m not in PRIORITY_MODELS]
    if extras:
        print(f"   Modelos extras (não priorizados): {', '.join(extras)}")

    print(f"\n🎯 Modelos a testar: {len(to_test)}")
    for i, m in enumerate(to_test, 1):
        print(f"   {i}. {m}")

    print(f"\n⏱️  Estimativa: ~{len(to_test) * len(PROMPTS) * RUNS * 20 / 60:.0f} min\n")
    # Auto-start in non-interactive mode
    try:
        input("  Pressione ENTER para começar...")
    except EOFError:
        print("  (auto-start)\n")

    all_results = []

    for mi, mid in enumerate(to_test):
        print(f"\n{'━'*70}")
        print(f"  🤖 [{mi+1}/{len(to_test)}] {mid}")
        print(f"{'━'*70}")

        if not load_model(mid):
            print(f"  ❌ Falha ao carregar — pulando")
            continue
        print(f"  ✅ Carregado!")
        time.sleep(2)

        print(f"  🔥 Warmup...", end=" ", flush=True)
        chat(mid, "Olá, teste.")
        print("OK")

        scores_m, scores_p, scores_n = [], [], []
        speeds, ttfts = [], []

        for ti, test in enumerate(PROMPTS):
            print(f"  [{ti+1:02d}/{len(PROMPTS)}] {test['d']}/{test['id']}", end=" ", flush=True)

            best_sc = -1
            best_r = None
            best_ev = None

            for run in range(RUNS):
                res = chat(mid, test["p"])
                if "error" in res:
                    print(f"❌{res['error'][:20]}", end=" ")
                    continue
                ev = evaluate(res["content"], test)
                if ev["score"] > best_sc:
                    best_sc = ev["score"]
                    best_r = res
                    best_ev = ev

            if best_r is None:
                print("❌")
                if "Mood" in test["d"]: scores_m.append(0)
                elif "Pyth" in test["d"]: scores_p.append(0)
                else: scores_n.append(0)
                continue

            tps = best_r.get("tokens_per_second",0)
            ttft = best_r.get("time_to_first_token",0)
            sc = best_ev["score"]

            speeds.append(tps)
            ttfts.append(ttft)
            d = test["d"]
            if "Mood" in d: scores_m.append(sc)
            elif "Pyth" in d: scores_p.append(sc)
            else: scores_n.append(sc)

            icon = "🟢" if sc >= 70 else "🟡" if sc >= 40 else "🔴"
            miss = f" falt:{','.join(best_ev['missing'][:2])}" if best_ev['missing'] else ""
            print(f"{icon} {sc:5.1f} {tps:5.1f}t/s {ttft:.1f}s{miss}")

        print(f"\n  ⏳ Descarregando...", end=" ", flush=True)
        unload_model(mid)
        print("✅")

        am = sum(scores_m)/len(scores_m) if scores_m else 0
        ap = sum(scores_p)/len(scores_p) if scores_p else 0
        an = sum(scores_n)/len(scores_n) if scores_n else 0
        aspd = sum(speeds)/len(speeds) if speeds else 0
        attf = sum(ttfts)/len(ttfts) if ttfts else 0
        overall = am*0.35 + ap*0.35 + an*0.30

        bar = lambda v: '█'*int(v/5)+'░'*(20-int(v/5))
        print(f"\n  ┌──────────────────────────────────────────────┐")
        print(f"  │ 📊 {mid[:40]:<40} │")
        print(f"  │  Moodle:  {am:5.1f}  {bar(am)} │")
        print(f"  │  Python:  {ap:5.1f}  {bar(ap)} │")
        print(f"  │  n8n:     {an:5.1f}  {bar(an)} │")
        print(f"  │  Velocidade: {aspd:6.1f} tok/s  TTFT: {attf:.2f}s   │")
        print(f"  │  SCORE GERAL: {overall:5.1f}/100                        │")
        print(f"  └──────────────────────────────────────────────┘")

        all_results.append({
            "model": mid, "moodle": round(am,1), "python": round(ap,1),
            "n8n": round(an,1), "speed": round(aspd,1), "ttft": round(attf,2),
            "overall": round(overall,1),
        })

    if all_results:
        sr = sorted(all_results, key=lambda x: x["overall"], reverse=True)
        print(f"\n{'═'*70}")
        print(f"  🏆  RANKING FINAL")
        print(f"{'═'*70}")
        print(f"  {'#':>2} │ {'Modelo':<32} │ {'Moodle':>6} │ {'Python':>6} │ {'n8n':>6} │ {'Tok/s':>6} │ {'SCORE':>6}")
        print(f"  {'─'*2}─┼─{'─'*32}─┼─{'─'*6}─┼─{'─'*6}─┼─{'─'*6}─┼─{'─'*6}─┼─{'─'*6}")
        for i, r in enumerate(sr, 1):
            mn = r["model"].split("/")[-1] if "/" in r["model"] else r["model"]
            ml = "🥇" if i==1 else "🥈" if i==2 else "🥉" if i==3 else "  "
            print(f"  {ml}{i:2} │ {mn:<32} │ {r['moodle']:5.1f}  │ {r['python']:5.1f}  │ {r['n8n']:5.1f}  │ {r['speed']:5.1f} │ {r['overall']:5.1f}")

        b = sr[0]
        bm = max(sr, key=lambda x: x["moodle"])
        bp = max(sr, key=lambda x: x["python"])
        bn = max(sr, key=lambda x: x["n8n"])
        bf = max(sr, key=lambda x: x["speed"])

        print(f"\n  📋 RECOMENDAÇÕES:")
        print(f"     🏆 GERAL:     {b['model']} ({b['overall']})")
        print(f"     🟦 Moodle:    {bm['model']} ({bm['moodle']})")
        print(f"     🟩 Python:    {bp['model']} ({bp['python']})")
        print(f"     🟨 n8n:       {bn['model']} ({bn['n8n']})")
        print(f"     ⚡ Veloz:     {bf['model']} ({bf['speed']} tok/s)")

        out = os.path.join(RESULTS_DIR, f"ranking_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
        with open(out, "w") as f:
            json.dump({"timestamp": datetime.now().isoformat(), "results": sr}, f, indent=2, ensure_ascii=False)
        print(f"\n  💾 Salvo: {out}")

    print("\n  ✅ BENCHMARK CONCLUÍDO!\n")


if __name__ == "__main__":
    main()
