#!/usr/bin/env python3
"""
Benchmark automático — executa todos os modelos sem pedir input.
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
WARMUP = 1
RUNS = 2
MAX_TOK = 2048
RESULTS_DIR = os.path.join(os.path.dirname(__file__), "resultados")
os.makedirs(RESULTS_DIR, exist_ok=True)

PROMPTS = [
    # ── MOODLE ──
    {"id":"m01","d":"Mood","p":"Quais são os 5 tipos de plugins Moodle mais comuns? Liste estrutura de pastas.","k":["activity","block","auth","enrol","local"],"code":False},
    {"id":"m02","d":"Mood","p":"Crie estrutura completa de um block plugin Moodle chamado 'block_notificador'. Liste todos os arquivos.","k":["version.php","block.php","db/access.php","lang/en/"],"code":False},
    {"id":"m03","d":"Mood","p":"Escreva o arquivo version.php para um plugin 'local_notificador' que requer Moodle 4.0.","k":["$plugin->version","$plugin->requires","$plugin->component","local_notificador"],"code":True,"cm":"<?php"},
    {"id":"m04","d":"Mood","p":"Crie install.xml Moodle XMLDB para tabela 'notificacoes': id, userid, titulo, mensagem, lida, timecreated.","k":["TABLE NAME","FIELD NAME","userid","titulo","mensagem","PRIMARY KEY"],"code":True,"cm":"XMLDB"},
    {"id":"m05","d":"Mood","p":"Mostre como usar $DB do Moodle para insert_record, get_records e update_record com a tabela 'user'.","k":["global $DB","insert_record","get_records","update_record"],"code":True,"cm":"global $DB"},
    {"id":"m06","d":"Mood","p":"Crie db/external.php para uma External Function 'obter_notificacoes' no Moodle.","k":["external_functions","external_description","PARAM_","returns"],"code":True,"cm":"<?php"},
    {"id":"m07","d":"Mood","p":"Crie um Event personalizado 'notificacao_enviada' no Moodle. Inclua classe e db/events.php.","k":["extends","core\\event","get_name","get_description"],"code":True,"cm":"<?php"},
    {"id":"m08","d":"Mood","p":"Crie db/access.php com 3 capabilities: local/notificador:send, manage e view.","k":["$capabilities","risk","captype","contextlevel"],"code":True,"cm":"$capabilities"},
    {"id":"m09","d":"Mood","p":"Crie lang/en/local_notificador.php com strings do plugin.","k":["$string","notificador","send","manage","view"],"code":True,"cm":"$string"},
    {"id":"m10","d":"Mood","p":"Analise e identifique TODOS os erros: require_once('config.php'); defined('MOODLE_INTERNAL') || die(); $DB->Execute(\"INSERT INTO foo VALUES ('$_GET[name])'); echo $_GET['content'];","k":["injection","XSS","SQL injection","$_GET","sanitize","die"],"code":False},
    # ── PYTHON ──
    {"id":"p01","d":"Pyth","p":"Script Python completo que consuma a REST API do Moodle para listar cursos. Use token e trate erros.","k":["requests","get","json","token","except","courses"],"code":True,"cm":"import"},
    {"id":"p02","d":"Pyth","p":"Como autenticar na API do Moodle com token em Python? Mostre obtenção e uso do token.","k":["token","wsfunction","wstoken","api/moodle"],"code":True,"cm":"import"},
    {"id":"p03","d":"Pyth","p":"Função Python que receba JSON da API Moodle (usuários) e extraia nome, email, último login com validação.","k":["json","get","fullname","email","lastaccess","def "],"code":True,"cm":"def "},
    {"id":"p04","d":"Pyth","p":"Script Python com POST, retries (3 tentativas), timeout 30s, exponential backoff, e log.","k":["requests.post","retry","timeout","backoff","time.sleep","except"],"code":True,"cm":"import"},
    {"id":"p05","d":"Pyth","p":"Script Python que leia CSV (nome,email,curso) e importe via API Moodle. Trate duplicatas.","k":["csv","reader","requests","duplicate","open("],"code":True,"cm":"import"},
    {"id":"p06","d":"Pyth","p":"Código Python com asyncio para requisições assíncronas a múltiplas APIs com gather.","k":["async","await","aiohttp","httpx","asyncio","gather"],"code":True,"cm":"import"},
    {"id":"p07","d":"Pyth","p":"3 melhores práticas para usar variáveis de ambiente para senhas de API em Python.","k":["dotenv","os.environ","keyring",".env","load_dotenv","getenv"],"code":False},
    {"id":"p08","d":"Pyth","p":"Logging estruturado em Python com formato JSON, nível por env var, handler para arquivo + console.","k":["logging","getLogger","Formatter","StreamHandler","FileHandler"],"code":True,"cm":"import logging"},
    {"id":"p09","d":"Pyth","p":"Função Python que valide email, nome (máx 100 chars) e curso antes de enviar para API.","k":["email","validate","raise","ValueError","pydantic","def "],"code":True,"cm":"def "},
    {"id":"p10","d":"Pyth","p":"Implemente rate limiting em Python: token bucket, 10 req/min, espera automática.","k":["time","sleep","rate","limit","token","bucket"],"code":True,"cm":"import"},
    # ── N8N ──
    {"id":"n01","d":"n8n ","p":"Workflow n8n em JSON: Webhook POST → validar → salvar no banco. Inclua error handler.","k":["nodes","connections","webhook","type","position","parameters"],"code":True,"cm":"{"},
    {"id":"n02","d":"n8n ","p":"Code node JS n8n: transformar lista de {nome,email} → formato email. Filtre inválidos.","k":["$input","all()","return","json","filter","map"],"code":True,"cm":"return"},
    {"id":"n03","d":"n8n ","p":"5 expressões n8n: acessar node anterior, variável ambiente, IF, formatar data, concatenar.","k":["{{","}}","$json","$node","$env","DateTime"],"code":False},
    {"id":"n04","d":"n8n ","p":"HTTP Request node n8n para API Moodle: URL dinâmica, token nos headers, JSON body, erro 401/403.","k":["httpRequest","url","method","header","authorization","token"],"code":False},
    {"id":"n05","d":"n8n ","p":"Workflow n8n: nota>=7 aprova, >=5 recuperação, <5 reprovado. Use IF node.","k":["IF","condition","value","true","false","email"],"code":False},
    {"id":"n06","d":"n8n ","p":"Tratar erros em n8n: Error Trigger, retry, Error Workflow, Stop And Error.","k":["errorTrigger","retryOnFail","Error Workflow","stopAndError","errorMessage"],"code":False},
    {"id":"n07","d":"n8n ","p":"Workflow n8n: processar 100 alunos com loop Split In Batches. Buscar nota, calcular média.","k":["SplitInBatches","batch","loop","item","json","merge"],"code":False},
    {"id":"n08","d":"n8n ","p":"Credenciais seguras no n8n: criar credential customizada para API Moodle e usar em HTTP Request.","k":["credential","authentication","header","generic","oauth","apiKey"],"code":False},
    {"id":"n09","d":"n8n ","p":"Workflow n8n diário às 8h: buscar alunos com nota baixa no Moodle e email alerta ao professor.","k":["scheduleTrigger","rule","interval","cron","hour","email","moodle"],"code":False},
    {"id":"n10","d":"n8n ","p":"Workflow n8n com AI Agent: Webhook → LLM responde → salva no banco. AI Agent com tool.","k":["aiAgent","openAi","model","prompt","tool","memory","chatModel"],"code":False},
]


def check():
    try:
        r = requests.get(f"{BASE}/v1/models", timeout=5)
        return r.status_code == 200
    except:
        return False

def models():
    r = requests.get(f"{BASE}/v1/models", timeout=10)
    return [m["id"] for m in r.json().get("data",[]) if "embed" not in m["id"].lower()]

def load(mid):
    try:
        r = requests.post(f"{BASE}/api/v1/models/load", json={"model":mid}, timeout=300)
        if r.status_code == 200:
            time.sleep(5)
            try:
                requests.get(f"{BASE}/v1/models", timeout=10)
            except: pass
            return True
        return False
    except:
        return False

def unload(mid):
    try:
        requests.post(f"{BASE}/api/v1/models/unload", json={"model":mid}, timeout=60)
    except:
        pass
    time.sleep(5)

def chat(mid, prompt):
    payload = {
        "model": mid,
        "messages": [
            {"role":"system","content":"Você é um especialista em Moodle (PHP), Python e n8n. Responda em português, com código quando solicitado."},
            {"role":"user","content": prompt},
        ],
        "temperature": 0.2,
        "max_tokens": MAX_TOK,
        "stream": False,
    }
    for attempt in range(3):
        t0 = time.time()
        try:
            r = requests.post(f"{BASE}/v1/chat/completions", json=payload, timeout=TIMEOUT)
            elapsed = time.time()-t0
            if r.status_code != 200:
                if attempt < 2: time.sleep(5); continue
                return {"error": f"HTTP {r.status_code}", "elapsed": elapsed}
            d = r.json()
            content = d["choices"][0]["message"]["content"]
            usage = d.get("usage",{})
            stats = d.get("stats",{})
            return {
                "content": content,
                "prompt_tokens": usage.get("prompt_tokens",0),
                "completion_tokens": usage.get("completion_tokens",0),
                "tokens_per_second": stats.get("tokens_per_second",0),
                "time_to_first_token": stats.get("time_to_first_token",0),
                "generation_time": stats.get("generation_time",elapsed),
                "elapsed": elapsed,
            }
        except Exception as e:
            if attempt < 2: time.sleep(5); continue
            return {"error": str(e), "elapsed": time.time()-t0}

def evaluate(response, test):
    cl = response.lower()
    score = 0
    found = []
    missing = []
    kws = test.get("k",[])
    if kws:
        pts = 70/len(kws)
        for kw in kws:
            if kw.lower() in cl:
                score += pts
                found.append(kw)
            else:
                missing.append(kw)
    if test.get("code"):
        cm = test.get("cm","")
        if cm and cm.lower() in cl:
            score += 30
        elif "```" in response:
            score += 20
        else:
            missing.append(f"[código:{cm}]")
    else:
        wc = len(response.split())
        if wc > 50: score += 30
        elif wc > 20: score += 20
        elif wc > 5: score += 10
    return {"score": round(min(score,100),1), "found": found, "missing": missing}


def main():
    print("\n" + "="*70)
    print("  BENCHMARK LM STUDIO — Moodle / Python / n8n")
    print(f"  Data: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print("="*70)

    if not check():
        print("\n❌ LM Studio não está rodando em", BASE)
        print("   Abra o LM Studio → Developer → Start server")
        sys.exit(1)

    mlist = models()
    print(f"\n📦 {len(mlist)} modelo(s) LLM encontrado(s):")
    for i, m in enumerate(mlist, 1):
        print(f"   {i:2d}. {m}")

    print(f"\n⏱️  Estimativa: ~{len(mlist) * len(PROMPTS) * (WARMUP+RUNS) * 25 / 60:.0f} min total\n")

    all_results = []

    for mi, mid in enumerate(mlist):
        print(f"\n{'━'*70}")
        print(f"  🤖 [{mi+1}/{len(mlist)}] {mid}")
        print(f"{'━'*70}")

        if not load(mid):
            print(f"  ❌ Falha ao carregar — pulando")
            continue
        print(f"  ✅ Carregado!")

        # Warmup
        print(f"  🔥 Warmup...", end=" ", flush=True)
        chat(mid, "Olá, teste de aquecimento.")
        print("OK")

        scores_m, scores_p, scores_n = [], [], []
        speeds, ttfts = [], []

        for ti, test in enumerate(PROMPTS):
            print(f"  [{ti+1:02d}/{len(PROMPTS)}] {test['d']}/{test.get('id','')}...", end=" ", flush=True)

            best_score = -1
            best_result = None
            best_eval = None

            for run in range(RUNS):
                res = chat(mid, test["p"])
                if "error" in res:
                    print(f"❌ {res['error'][:25]}", end=" ")
                    continue
                ev = evaluate(res["content"], test)
                if ev["score"] > best_score:
                    best_score = ev["score"]
                    best_result = res
                    best_eval = ev

            if best_result is None:
                print("❌ FALHOU")
                d = test["d"]
                if "Mood" in d: scores_m.append(0)
                elif "Pyth" in d: scores_p.append(0)
                else: scores_n.append(0)
                continue

            tps = best_result.get("tokens_per_second",0)
            ttft = best_result.get("time_to_first_token",0)
            sc = best_eval["score"]

            speeds.append(tps)
            ttfts.append(ttft)

            d = test["d"]
            if "Mood" in d: scores_m.append(sc)
            elif "Pyth" in d: scores_p.append(sc)
            else: scores_n.append(sc)

            icon = "🟢" if sc >= 70 else "🟡" if sc >= 40 else "🔴"
            miss_str = f" [falta: {', '.join(best_eval['missing'][:2])}]" if best_eval['missing'] else ""
            print(f"{icon} {sc:5.1f} | {tps:5.1f}tok/s | TTFT {ttft:.2f}s{miss_str}")

        # Descarregar
        print(f"\n  ⏳ Descarregando...", end=" ", flush=True)
        unload(mid)
        print("✅ Aguardando memória...")
        time.sleep(10)

        # Resumo
        am = sum(scores_m)/len(scores_m) if scores_m else 0
        ap = sum(scores_p)/len(scores_p) if scores_p else 0
        an = sum(scores_n)/len(scores_n) if scores_n else 0
        aspd = sum(speeds)/len(speeds) if speeds else 0
        attf = sum(ttfts)/len(ttfts) if ttfts else 0
        overall = am*0.35 + ap*0.35 + an*0.30

        print(f"\n  ┌────────────────────────────────────────────┐")
        print(f"  │ 📊 RESUMO: {mid[:32]:<32} │")
        print(f"  │  Moodle: {am:5.1f}/100  {'█'*int(am/5)}{'░'*(20-int(am/5))} │")
        print(f"  │  Python: {ap:5.1f}/100  {'█'*int(ap/5)}{'░'*(20-int(ap/5))} │")
        print(f"  │  n8n:    {an:5.1f}/100  {'█'*int(an/5)}{'░'*(20-int(an/5))} │")
        print(f"  │  Velocidade: {aspd:6.1f} tok/s                     │")
        print(f"  │  TTFT médio: {attf:6.2f}s                           │")
        print(f"  │  SCORE GERAL: {overall:5.1f}/100                       │")
        print(f"  └────────────────────────────────────────────┘")

        all_results.append({
            "model": mid, "moodle": am, "python": ap, "n8n": an,
            "speed": aspd, "ttft": attf, "overall": overall,
        })

    # ── RANKING FINAL ──
    if all_results:
        sorted_r = sorted(all_results, key=lambda x: x["overall"], reverse=True)
        print(f"\n{'═'*70}")
        print(f"  🏆  RANKING FINAL")
        print(f"{'═'*70}")
        print(f"  {'#':>2} │ {'Modelo':<32} │ {'Moodle':>6} │ {'Python':>6} │ {'n8n':>6} │ {'Tok/s':>6} │ {'TOTAL':>6}")
        print(f"  {'─'*2}─┼─{'─'*32}─┼─{'─'*6}─┼─{'─'*6}─┼─{'─'*6}─┼─{'─'*6}─┼─{'─'*6}")
        for i, r in enumerate(sorted_r, 1):
            mn = r["model"].split("/")[-1] if "/" in r["model"] else r["model"]
            medal = "🥇" if i==1 else "🥈" if i==2 else "🥉" if i==3 else "  "
            print(f"  {medal}{i:2} │ {mn:<32} │ {r['moodle']:5.1f}  │ {r['python']:5.1f}  │ {r['n8n']:5.1f}  │ {r['speed']:5.1f} │ {r['overall']:5.1f}")

        best = sorted_r[0]
        print(f"\n  🏆 MELHOR: {best['model']}")
        print(f"     Moodle {best['moodle']:.1f} | Python {best['python']:.1f} | n8n {best['n8n']:.1f} | {best['speed']:.1f} tok/s")

        bm = max(sorted_r, key=lambda x: x["moodle"])
        bp = max(sorted_r, key=lambda x: x["python"])
        bn = max(sorted_r, key=lambda x: x["n8n"])
        bf = max(sorted_r, key=lambda x: x["speed"])
        print(f"\n  📋 ESPECIALIZADOS:")
        print(f"     🟦 Moodle:  {bm['model']} ({bm['moodle']:.1f})")
        print(f"     🟩 Python:  {bp['model']} ({bp['python']:.1f})")
        print(f"     🟨 n8n:     {bn['model']} ({bn['n8n']:.1f})")
        print(f"     ⚡ Veloz:   {bf['model']} ({bf['speed']:.1f} tok/s)")

        out = os.path.join(RESULTS_DIR, f"ranking_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
        with open(out, "w") as f:
            json.dump(sorted_r, f, indent=2, ensure_ascii=False)
        print(f"\n  💾 Salvo: {out}")

    print("\n  ✅ BENCHMARK CONCLUÍDO!\n")


if __name__ == "__main__":
    main()
