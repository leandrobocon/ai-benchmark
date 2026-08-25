#!/usr/bin/env python3
"""
Benchmark LM Studio - Moodle / Python / n8n
Testa seus modelos locais com perguntas específicas para seus casos de uso.
"""

import json
import time
import sys
import os
from datetime import datetime
from typing import Optional

try:
    import requests
except ImportError:
    print("Instalando requests...")
    os.system(f"{sys.executable} -m pip install requests -q")
    import requests

# ── Configuração ──────────────────────────────────────────────
LMSTUDIO_BASE = "http://localhost:1234"
API_TIMEOUT = 180  # segundos máximo de espera por resposta
WARMUP_RUNS = 1
MEASURE_RUNS = 2
MAX_TOKENS = 2048

# ── Prompts de Benchmark ──────────────────────────────────────
BENCHMARK_PROMPTS = [
    # ════════════════ MOODLE (10 testes) ════════════════
    {
        "id": "moodle_01",
        "domain": "Moodle",
        "type": "Conhecimento",
        "prompt": "Quais são os 5 tipos de plugins Moodle mais comuns e onde cada um fica na estrutura de pastas? Responda em português.",
        "keywords": ["activity", "block", "auth", "enrol", "local", "mod/", "blocks/", "auth/"],
        "validate_code": False,
    },
    {
        "id": "moodle_02",
        "domain": "Moodle",
        "type": "Estrutura",
        "prompt": "Crie a estrutura completa de arquivos de um block plugin Moodle chamado 'block_notificador'. Liste todos os arquivos necessários e o conteúdo de cada um.",
        "keywords": ["version.php", "block.php", "db/access.php", "lang/en/", "classes/", "notificador"],
        "validate_code": False,
    },
    {
        "id": "moodle_03",
        "domain": "Moodle",
        "type": "PHP",
        "prompt": "Escreva o arquivo version.php completo para um plugin Moodle chamado 'local_notificador' que requer Moodle 4.0 no mínimo. Inclua todas as propriedades necessárias.",
        "keywords": ["$plugin->version", "$plugin->requires", "$plugin->component", "local_notificador", "400"],
        "validate_code": True,
        "code_marker": "<?php",
    },
    {
        "id": "moodle_04",
        "domain": "Moodle",
        "type": "Banco de Dados",
        "prompt": "Crie um arquivo install.xml Moodle XMLDB para uma tabela 'notificacoes' com campos: id (autoincrement), userid (int), titulo (varchar 255), mensagem (text), lida (tinyint default 0), timecreated (int), timemodified (int).",
        "keywords": ["TABLE NAME", "FIELD NAME", "userid", "titulo", "mensagem", "lida", "timecreated", "PRIMARY KEY"],
        "validate_code": True,
        "code_marker": "XMLDB",
    },
    {
        "id": "moodle_05",
        "domain": "Moodle",
        "type": "API Moodle",
        "prompt": "Mostre como usar a API $DB do Moodle para: 1) Inserir um registro, 2) Buscar registros por condição, 3) Atualizar um registro. Use a tabela 'user' como exemplo.",
        "keywords": ["global $DB", "insert_record", "get_records", "update_record", "user"],
        "validate_code": True,
        "code_marker": "global $DB",
    },
    {
        "id": "moodle_06",
        "domain": "Moodle",
        "type": "Web Services",
        "prompt": "Como registrar uma External Function no Moodle? Crie o arquivo db/external.php completo para uma função 'obter_notificacoes' que retorna notificações do usuário.",
        "keywords": ["external_functions", "external_description", "EXTERNAL_API", "PARAM_", "returns"],
        "validate_code": True,
        "code_marker": "<?php",
    },
    {
        "id": "moodle_07",
        "domain": "Moodle",
        "type": "Events",
        "prompt": "Crie um Event personalizado no Moodle chamado 'notificacao_enviada' que dispara quando uma notificação é enviada. Inclua a classe PHP e o registro em db/events.php.",
        "keywords": ["extends", "\\core\\event\\", "get_name", "get_description", "create()", "events.php"],
        "validate_code": True,
        "code_marker": "<?php",
    },
    {
        "id": "moodle_08",
        "domain": "Moodle",
        "type": "Capabilities",
        "prompt": "Como definir capabilities num plugin Moodle? Crie o arquivo db/access.php com 3 capabilities: local/notificador:send (teacher), local/notificador:manage (editingteacher), local/notificador:view (student).",
        "keywords": ["$capabilities", "risk", "captype", "contextlevel", "local/notificador"],
        "validate_code": True,
        "code_marker": "$capabilities",
    },
    {
        "id": "moodle_09",
        "domain": "Moodle",
        "type": "Lang",
        "prompt": "Crie o arquivo lang/en/local_notificador.php com as seguintes strings: plugin name, plugin description, send notification, manage notifications, view notifications.",
        "keywords": ["$string['local_notificador']", "notificador", "send", "manage", "view"],
        "validate_code": True,
        "code_marker": "$string",
    },
    {
        "id": "moodle_10",
        "domain": "Moodle",
        "type": "Debug",
        "prompt": "Analise este código Moodle e identifique TODOS os erros:\n\n<?php\nrequire_once('config.php');\ndefined('MOODLE_INTERNAL') || die();\n$USER->firstname = $_GET['name'];\n$DB->Execute(\"INSERT INTO foo VALUES ('$USER->firstname')\");\necho $_GET['content'];",
        "keywords": ["injection", "XSS", "SQL injection", "$_GET", "require_once", "die", "prepend", "sanitize"],
        "validate_code": False,
    },
    # ════════════════ PYTHON (10 testes) ════════════════
    {
        "id": "python_01",
        "domain": "Python",
        "type": "API",
        "prompt": "Escreva um script Python completo que consuma a REST API do Moodle para listar todos os cursos visíveis. Use autenticação por token e trate erros de conexão.",
        "keywords": ["requests", "get", "json", "token", "except", "courses", "api"],
        "validate_code": True,
        "code_marker": "import",
    },
    {
        "id": "python_02",
        "domain": "Python",
        "type": "Auth",
        "prompt": "Como autenticar na API do Moodle com token em Python? Mostre como obter o token manualmente e usar nas requisições. Inclua exemplo com login por web service.",
        "keywords": ["token", "wsfunction", "moodle_token", "wstoken", "api/moodle"],
        "validate_code": True,
        "code_marker": "import",
    },
    {
        "id": "python_03",
        "domain": "Python",
        "type": "JSON",
        "prompt": "Escreva uma função Python que receba uma resposta JSON da API Moodle (lista de usuários) e extraia: nome completo, email e data do último login. Valide se os campos existem antes de acessar.",
        "keywords": ["json", "get", "fullname", "email", "lastaccess", "def ", "try", "KeyError"],
        "validate_code": True,
        "code_marker": "def ",
    },
    {
        "id": "python_04",
        "domain": "Python",
        "type": "HTTP",
        "prompt": "Escreva um script Python que faça POST para uma API com: retries automáticos (3 tentativas), timeout de 30s, exponential backoff, e log de cada tentativa.",
        "keywords": ["requests.post", "retry", "timeout", "backoff", "time.sleep", "except", "try"],
        "validate_code": True,
        "code_marker": "import",
    },
    {
        "id": "python_05",
        "domain": "Python",
        "type": "CSV",
        "prompt": "Escreva um script Python que leia um CSV com colunas (nome, email, curso) e importe cada registro via API do Moodle usando web services. Trate duplicatas.",
        "keywords": ["csv", "reader", "import", "requests", "duplicate", "open(", "with"],
        "validate_code": True,
        "code_marker": "import",
    },
    {
        "id": "python_06",
        "domain": "Python",
        "type": "Async",
        "prompt": "Escreva código Python com asyncio que faça requisições assíncronas para múltiplas APIs e aguarde todas completarem. Use aiohttp ou httpx.",
        "keywords": ["async", "await", "aiohttp", "httpx", "asyncio", "gather", "def ", "async def"],
        "validate_code": True,
        "code_marker": "import",
    },
    {
        "id": "python_07",
        "domain": "Python",
        "type": "Env",
        "prompt": "Como usar variáveis de ambiente para armazenar senhas de API em Python? Mostre as 3 melhores práticas: dotenv, os.environ, e keyring.",
        "keywords": ["dotenv", "os.environ", "keyring", ".env", "load_dotenv", "getenv"],
        "validate_code": False,
    },
    {
        "id": "python_08",
        "domain": "Python",
        "type": "Logging",
        "prompt": "Adicione logging estruturado a um script de integração Python. Use o módulo logging com formato JSON, nível configurável por variável de ambiente, e handler para arquivo + console.",
        "keywords": ["logging", "getLogger", "Formatter", "StreamHandler", "FileHandler", "dictConfig", "json"],
        "validate_code": True,
        "code_marker": "import logging",
    },
    {
        "id": "python_09",
        "domain": "Python",
        "type": "Validation",
        "prompt": "Escreva uma função Python que valide dados de entrada antes de enviar para uma API. Valide: email (formato), nome (não vazio, máx 100 chars), curso (deve estar na lista permitida). Use pydantic ou validação manual.",
        "keywords": ["email", "validate", "raise", "ValueError", "pydantic", "BaseModel", "def "],
        "validate_code": True,
        "code_marker": "def ",
    },
    {
        "id": "python_10",
        "domain": "Python",
        "type": "Rate Limit",
        "prompt": "Implemente rate limiting em Python para chamadas a uma API. Use token bucket ou sliding window. Limite: 10 requisições por minuto. Inclua espera automática.",
        "keywords": ["time", "sleep", "rate", "limit", "token", "bucket", "throttle", "deque"],
        "validate_code": True,
        "code_marker": "import",
    },
    # ════════════════ N8N (10 testes) ════════════════
    {
        "id": "n8n_01",
        "domain": "n8n",
        "type": "Workflow JSON",
        "prompt": "Crie um workflow n8n completo em JSON que: receba dados via Webhook POST, valide o payload, e salve no banco de dados. Inclua nó de erro handler.",
        "keywords": ["nodes", "connections", "webhook", "type", "position", "parameters"],
        "validate_code": True,
        "code_marker": "{",
    },
    {
        "id": "n8n_02",
        "domain": "n8n",
        "type": "Code Node",
        "prompt": "Escreva um Code node em JavaScript para n8n que transforme uma lista de entrada (array de objetos com 'nome' e 'email') em formato para envio de email. Filtre emails inválidos e formate o nome.",
        "keywords": ["$input", "all()", "return", "json", "filter", "map", "push"],
        "validate_code": True,
        "code_marker": "return",
    },
    {
        "id": "n8n_03",
        "domain": "n8n",
        "type": "Expressions",
        "prompt": "Mostre 5 exemplos práticos de expressões n8n para: acessar dados de um node anterior, usar variáveis de ambiente, condicionar um IF, formatar data, e concatenar strings.",
        "keywords": ["{{", "}}", "$json", "$node", "$env", "DateTime", "first().json"],
        "validate_code": False,
    },
    {
        "id": "n8n_04",
        "domain": "n8n",
        "type": "HTTP Request",
        "prompt": "Configure um HTTP Request node no n8n para chamar a API do Moodle. Inclua: URL dinâmica, autenticação via token nos headers, body em JSON, e tratamento de erro 401/403/500.",
        "keywords": ["httpRequest", "url", "method", "header", "authorization", "token", "error"],
        "validate_code": False,
    },
    {
        "id": "n8n_05",
        "domain": "n8n",
        "type": "IF/Switch",
        "prompt": "Crie um workflow n8n que receba nota do aluno e: se nota >= 7, aprova e envia email de parabéns; se nota >= 5, envia para recuperação; se nota < 5, reprovado. Use IF node.",
        "keywords": ["IF", "condition", "value", "true", "false", "email", "aprovado", "reprovado"],
        "validate_code": False,
    },
    {
        "id": "n8n_06",
        "domain": "n8n",
        "type": "Error Handling",
        "prompt": "Como tratar erros em workflows n8n? Mostre: Error Trigger node, retry policy, Error Workflow configurado, e como usar Stop And Error node para validação customizada.",
        "keywords": ["errorTrigger", "retryOnFail", "Error Workflow", "stopAndError", "errorMessage"],
        "validate_code": False,
    },
    {
        "id": "n8n_07",
        "domain": "n8n",
        "type": "Loop",
        "prompt": "Crie um workflow n8n que processe uma lista de 100 alunos usando loop. Para cada aluno: buscar nota, calcular média, e salvar resultado. Use Split In Batches.",
        "keywords": ["SplitInBatches", "batch", "loop", "item", "json", "merge"],
        "validate_code": False,
    },
    {
        "id": "n8n_08",
        "domain": "n8n",
        "type": "Credentials",
        "prompt": "Como configurar credenciais seguras no n8n? Mostre como criar uma credential customizada para API do Moodle, usá-la em um HTTP Request node, e quais tipos de auth são suportados.",
        "keywords": ["credential", "authentication", "header", "generic", "oauth", "apiKey"],
        "validate_code": False,
    },
    {
        "id": "n8n_09",
        "domain": "n8n",
        "type": "Schedule",
        "prompt": "Crie um workflow n8n que rode todo dia às 8h da manhã: busque alunos com nota abaixo da média do Moodle, e envie um email de alerta para o professor. Inclua Schedule Trigger.",
        "keywords": ["scheduleTrigger", "rule", "interval", "cron", "hour", "email", "moodle"],
        "validate_code": False,
    },
    {
        "id": "n8n_10",
        "domain": "n8n",
        "type": "AI Agent",
        "prompt": "Crie um workflow n8n com AI Agent que: receba uma pergunta via Webhook, use um modelo LLM para responder, e salve a conversa no banco de dados. Inclua AI Agent node com tool.",
        "keywords": ["aiAgent", "openAi", "model", "prompt", "tool", "memory", "chatModel"],
        "validate_code": False,
    },
]


# ── Funções Auxiliares ────────────────────────────────────────
def check_lmstudio() -> bool:
    """Verifica se LM Studio está rodando."""
    try:
        r = requests.get(f"{LMSTUDIO_BASE}/v1/models", timeout=5)
        return r.status_code == 200
    except Exception:
        return False


def list_models() -> list[dict]:
    """Lista todos os modelos disponíveis no LM Studio."""
    r = requests.get(f"{LMSTUDIO_BASE}/v1/models", timeout=10)
    data = r.json()
    models = []
    for m in data.get("data", []):
        models.append({
            "id": m.get("id", ""),
            "object": m.get("object", ""),
        })
    return models


def load_model(model_id: str) -> bool:
    """Carrega um modelo via API REST v1 do LM Studio."""
    try:
        r = requests.post(
            f"{LMSTUDIO_BASE}/api/v1/models/load",
            json={"model": model_id},
            timeout=300,
        )
        if r.status_code == 200:
            time.sleep(5)
            try:
                requests.get(f"{LMSTUDIO_BASE}/v1/models", timeout=10)
            except: pass
            return True
        return False
    except Exception:
        return False


def unload_model(model_id: str) -> bool:
    """Descarrega um modelo."""
    try:
        r = requests.post(
            f"{LMSTUDIO_BASE}/api/v1/models/unload",
            json={"model": model_id},
            timeout=60,
        )
        time.sleep(5)
        return r.status_code == 200
    except Exception:
        time.sleep(5)
        return False


def chat_completion(model_id: str, prompt: str) -> dict:
    """Envia um prompt e retorna resposta + métricas."""
    payload = {
        "model": model_id,
        "messages": [
            {"role": "system", "content": "Você é um especialista em desenvolvimento Moodle, Python e n8n. Responda sempre em português, de forma técnica e objetiva. Inclua código quando solicitado."},
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.2,
        "max_tokens": MAX_TOKENS,
        "stream": False,
    }

    start_total = time.time()
    for attempt in range(3):
        start = time.time()
        try:
            r = requests.post(
                f"{LMSTUDIO_BASE}/v1/chat/completions",
                json=payload,
                timeout=API_TIMEOUT,
            )
            elapsed = time.time() - start

            if r.status_code != 200:
                if attempt < 2:
                    time.sleep(5)
                    continue
                return {"error": f"HTTP {r.status_code}", "elapsed": elapsed}

            data = r.json()
            content = data["choices"][0]["message"]["content"]
            usage = data.get("usage", {})
            stats = data.get("stats", {})

            return {
                "content": content,
                "prompt_tokens": usage.get("prompt_tokens", 0),
                "completion_tokens": usage.get("completion_tokens", 0),
                "total_tokens": usage.get("total_tokens", 0),
                "tokens_per_second": stats.get("tokens_per_second", 0),
                "time_to_first_token": stats.get("time_to_first_token", 0),
                "generation_time": stats.get("generation_time", elapsed),
                "elapsed": elapsed,
            }
        except Exception as e:
            if attempt < 2:
                time.sleep(5)
                continue
            return {"error": str(e), "elapsed": time.time() - start_total}


def evaluate_quality(response: str, test: dict) -> dict:
    """Avalia a qualidade da resposta baseado em keywords e validação de código."""
    content_lower = response.lower()
    score = 0
    max_score = 100
    found = []
    missing = []

    # Keyword matching (70 pontos)
    keywords = test.get("keywords", [])
    if keywords:
        kw_score_per = 70 / len(keywords)
        for kw in keywords:
            if kw.lower() in content_lower:
                score += kw_score_per
                found.append(kw)
            else:
                missing.append(kw)

    # Validação de código (30 pontos)
    if test.get("validate_code"):
        code_marker = test.get("code_marker", "")
        if code_marker and code_marker.lower() in content_lower:
            score += 30
        elif "```" in response:
            score += 20  # Tem bloco de código mas sem marker específico
        else:
            missing.append(f"[código: {code_marker}]")
    else:
        # Pergunta conceitual - dar pontos por extensão e qualidade
        word_count = len(response.split())
        if word_count > 50:
            score += 30
        elif word_count > 20:
            score += 20
        elif word_count > 5:
            score += 10

    return {
        "score": round(min(score, 100), 1),
        "found": found,
        "missing": missing,
    }


def print_header():
    """Imprime cabeçalho do benchmark."""
    print()
    print("╔══════════════════════════════════════════════════════════════════════╗")
    print("║  BENCHMARK LM STUDIO — Moodle / Python / n8n                      ║")
    print("║  Modelos: carrega 1 por vez, testa, mede, descarrega              ║")
    print("╠══════════════════════════════════════════════════════════════════════╣")
    print(f"║  Data: {datetime.now().strftime('%Y-%m-%d %H:%M')}  |  Servidor: {LMSTUDIO_BASE}            ║")
    print(f"║  Warmup: {WARMUP_RUNS}x  |  Medições: {MEASURE_RUNS}x  |  Max tokens: {MAX_TOKENS}            ║")
    print("╚══════════════════════════════════════════════════════════════════════╝")
    print()


def run_benchmark(model_id: str) -> dict:
    """Executa o benchmark completo em um modelo."""
    results = {
        "model": model_id,
        "tests": [],
        "scores": {"moodle": [], "python": [], "n8n": []},
        "speeds": [],
        "ttfts": [],
    }

    # Warmup
    print(f"  🔥 Warmup...")
    chat_completion(model_id, "Olá, este é um teste de aquecimento.")

    # Executar cada teste
    for i, test in enumerate(BENCHMARK_PROMPTS):
        domain = test["domain"]
        test_type = test["type"]
        print(f"  📝 [{i+1:02d}/{len(BENCHMARK_PROMPTS)}] {domain}/{test_type}...", end=" ", flush=True)

        best_result = None
        best_eval = None
        best_score = -1

        for run in range(MEASURE_RUNS):
            result = chat_completion(model_id, test["prompt"])

            if "error" in result:
                print(f"❌ {result['error'][:30]}")
                continue

            eval_result = evaluate_quality(result["content"], test)

            if eval_result["score"] > best_score:
                best_score = eval_result["score"]
                best_result = result
                best_eval = eval_result

        if best_result is None:
            print("❌ FALHOU")
            results["scores"][domain].append(0)
            continue

        tps = best_result.get("tokens_per_second", 0)
        ttft = best_result.get("time_to_first_token", 0)
        score = best_eval["score"]

        results["scores"][domain].append(score)
        results["speeds"].append(tps)
        results["ttfts"].append(ttft)
        results["tests"].append({
            "id": test["id"],
            "domain": domain,
            "type": test_type,
            "score": score,
            "tokens_per_second": tps,
            "time_to_first_token": ttft,
            "missing": best_eval["missing"],
        })

        score_icon = "🟢" if score >= 70 else "🟡" if score >= 40 else "🔴"
        print(f"{score_icon} {score:5.1f} pts | {tps:5.1f} tok/s | TTFT {ttft:.2f}s")

    return results


def print_model_summary(results: dict):
    """Imprime resumo de um modelo."""
    model = results["model"]
    scores_moodle = results["scores"]["moodle"]
    scores_python = results["scores"]["python"]
    scores_n8n = results["scores"]["n8n"]

    avg_moodle = sum(scores_moodle) / len(scores_moodle) if scores_moodle else 0
    avg_python = sum(scores_python) / len(scores_python) if scores_python else 0
    avg_n8n = sum(scores_n8n) / len(scores_n8n) if scores_n8n else 0
    avg_speed = sum(results["speeds"]) / len(results["speeds"]) if results["speeds"] else 0
    avg_ttft = sum(results["ttfts"]) / len(results["ttfts"]) if results["ttfts"] else 0

    overall = (avg_moodle * 0.35 + avg_python * 0.35 + avg_n8n * 0.30)

    print()
    print(f"  ┌─────────────────────────────────────────────────────────┐")
    print(f"  │ 📊 {model[:48]:<48} │")
    print(f"  ├─────────────────────────────────────────────────────────┤")
    print(f"  │  Moodle:  {avg_moodle:5.1f}/100  ██████{'█' * int(avg_moodle/5)}{'░' * (20 - int(avg_moodle/5))}  │")
    print(f"  │  Python:  {avg_python:5.1f}/100  ██████{'█' * int(avg_python/5)}{'░' * (20 - int(avg_python/5))}  │")
    print(f"  │  n8n:     {avg_n8n:5.1f}/100  ██████{'█' * int(avg_n8n/5)}{'░' * (20 - int(avg_n8n/5))}  │")
    print(f"  ├─────────────────────────────────────────────────────────┤")
    print(f"  │  Velocidade média:     {avg_speed:6.1f} tok/s                    │")
    print(f"  │  TTFT médio:           {avg_ttft:6.2f}s                          │")
    print(f"  │  SCORE GERAL:          {overall:6.1f}/100                       │")
    print(f"  └─────────────────────────────────────────────────────────┘")
    print()

    return {"model": model, "moodle": avg_moodle, "python": avg_python, "n8n": avg_n8n, "speed": avg_speed, "ttft": avg_ttft, "overall": overall}


def print_final_ranking(all_results: list[dict]):
    """Imprime ranking final comparativo."""
    print()
    print("╔══════════════════════════════════════════════════════════════════════════════╗")
    print("║                     RANKING FINAL — TODOS OS MODELOS                       ║")
    print("╠══════════════════════════════════════════════════════════════════════════════╣")
    print(f"║ {'#':>2} │ {'Modelo':<35} │ {'Moodle':>7} │ {'Python':>7} │ {'n8n':>7} │ {'Tok/s':>6} │ {'Score':>6} ║")
    print("╠══════════════════════════════════════════════════════════════════════════════╣")

    sorted_results = sorted(all_results, key=lambda x: x["overall"], reverse=True)

    for i, r in enumerate(sorted_results, 1):
        model_short = r["model"].split("/")[-1] if "/" in r["model"] else r["model"]
        medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else "  "
        print(f"║{medal}{i:2} │ {model_short:<35} │ {r['moodle']:6.1f}  │ {r['python']:6.1f}  │ {r['n8n']:6.1f}  │ {r['speed']:5.1f} │ {r['overall']:5.1f} ║")

    print("╚══════════════════════════════════════════════════════════════════════════════╝")
    print()

    # Diagnóstico
    best = sorted_results[0] if sorted_results else None
    worst = sorted_results[-1] if sorted_results else None

    if best:
        print(f"  🏆 MELHOR MODELO GERAL: {best['model']}")
        print(f"     → Moodle: {best['moodle']:.1f} | Python: {best['python']:.1f} | n8n: {best['n8n']:.1f}")
        print()

    # Recomendações
    print("  📋 RECOMENDAÇÕES:")
    print()

    # Melhor para Moodle
    best_moodle = max(sorted_results, key=lambda x: x["moodle"])
    print(f"     🟦 MELHOR PARA MOODLE:  {best_moodle['model']}")
    print(f"        Score: {best_moodle['moodle']:.1f}/100")

    # Melhor para Python
    best_python = max(sorted_results, key=lambda x: x["python"])
    print(f"     🟩 MELHOR PARA PYTHON:  {best_python['model']}")
    print(f"        Score: {best_python['python']:.1f}/100")

    # Melhor para n8n
    best_n8n = max(sorted_results, key=lambda x: x["n8n"])
    print(f"     🟨 MELHOR PARA N8N:     {best_n8n['model']}")
    print(f"        Score: {best_n8n['n8n']:.1f}/100")

    # Mais rápido
    fastest = max(sorted_results, key=lambda x: x["speed"])
    print(f"     ⚡ MAIS RÁPIDO:         {fastest['model']}")
    print(f"        Velocidade: {fastest['speed']:.1f} tok/s")

    print()
    print("  💾 ESPAÇO EM DISCO:")
    print("     Seus 12 modelos ocupam ~128 GB. Considere apagar modelos redundantes.")

    # Salvar resultados
    output_file = os.path.join(RESULTS_DIR, f"benchmark_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
    with open(output_file, "w") as f:
        json.dump(sorted_results, f, indent=2, ensure_ascii=False)
    print(f"\n  💾 Resultados salvos em: {output_file}")


# ── Main ──────────────────────────────────────────────────────
RESULTS_DIR = os.path.join(os.path.dirname(__file__), "resultados")
os.makedirs(RESULTS_DIR, exist_ok=True)

def main():
    print_header()

    # Verificar LM Studio
    print("🔍 Verificando LM Studio...")
    if not check_lmstudio():
        print("❌ LM Studio não está rodando ou não está acessível em", LMSTUDIO_BASE)
        print("   → Abra o LM Studio e ative o servidor (Developer → Start server)")
        sys.exit(1)
    print("   ✅ LM Studio conectado!\n")

    # Listar modelos
    print("🔍 Buscando modelos instalados...")
    models = list_models()
    # Filtrar apenas LLMs (excluir embedding)
    models = [m for m in models if "embed" not in m["id"].lower()]

    if not models:
        print("   ❌ Nenhum modelo LLM encontrado. Baixe modelos no LM Studio.")
        sys.exit(1)

    print(f"   📦 {len(models)} modelo(s) encontrado(s):\n")
    for m in models:
        print(f"      • {m['id']}")
    print()

    # Perguntar quais testar
    print("─" * 60)
    print("  Opções:")
    print("    ENTER  = Testar TODOS os modelos")
    print("    1,2,3  = Testar apenas esses (ex: 1,3,5)")
    print("    q      = Sair")
    print("─" * 60)
    choice = input("  Selecione: ").strip()

    if choice.lower() == "q":
        print("Saindo...")
        sys.exit(0)

    selected_models = models
    if choice:
        try:
            indices = [int(x.strip()) - 1 for x in choice.split(",")]
            selected_models = [models[i] for i in indices if 0 <= i < len(models)]
        except (ValueError, IndexError):
            print("  ⚠️  Opção inválida, testando todos.")

    # Estimativa de tempo
    estimated_minutes = len(selected_models) * (len(BENCHMARK_PROMPTS) * (WARMUP_RUNS + MEASURE_RUNS) * 30) / 60
    print(f"\n⏱️  Tempo estimado: ~{estimated_minutes:.0f} minutos para {len(selected_models)} modelo(s)")
    print(f"   ({len(BENCHMARK_PROMPTS)} testes × {WARMUP_RUNS + MEASURE_RUNS} runs × ~30s por teste)")
    input("\n  Pressione ENTER para começar...")

    # Executar benchmarks
    all_results = []
    for idx, model in enumerate(selected_models):
        model_id = model["id"]
        print(f"\n{'═' * 60}")
        print(f"  🤖 Modelo {idx+1}/{len(selected_models)}: {model_id}")
        print(f"{'═' * 60}")

        # Carregar modelo
        print(f"  ⏳ Carregando modelo...")
        if not load_model(model_id):
            print(f"  ❌ Falha ao carregar {model_id} — pulando...")
            continue
        print(f"  ✅ Modelo carregado!\n")

        # Executar benchmark
        results = run_benchmark(model_id)

        # Descarregar modelo
        print(f"\n  ⏳ Descarregando modelo...")
        unload_model(model_id)
        print(f"  ✅ Modelo descarregado. Aguardando memória...")
        time.sleep(10)

        # Salvar resultado parcial
        partial_file = os.path.join(RESULTS_DIR, f"partial_{model_id.replace('/', '_')}.json")
        with open(partial_file, "w") as f:
            json.dump(results, f, indent=2, ensure_ascii=False)

        summary = print_model_summary(results)
        all_results.append(summary)

    # Ranking final
    if all_results:
        print_final_ranking(all_results)
    else:
        print("\n  ❌ Nenhum modelo foi testado com sucesso.")

    print("\n  ✅ Benchmark concluído!\n")


if __name__ == "__main__":
    main()
