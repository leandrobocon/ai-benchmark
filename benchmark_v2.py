#!/usr/bin/env python3
"""AI Benchmark v0.1 — executor modular.

Backend compatível com LM Studio (OpenAI-compatible API).
"""
from __future__ import annotations

import argparse
import json
import os
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import requests

ROOT = Path(__file__).resolve().parent
PROMPTS_FILE = ROOT / "prompts" / "benchmark.json"
RESULTS_DIR = ROOT / "resultados"
DEFAULT_BASE = os.getenv("LMSTUDIO_BASE", "http://localhost:1234")
DEFAULT_TIMEOUT = int(os.getenv("AI_BENCHMARK_TIMEOUT", "180"))
DEFAULT_MAX_TOKENS = int(os.getenv("AI_BENCHMARK_MAX_TOKENS", "2048"))

from evaluator import evaluate


def load_tests(path: Path) -> list[dict[str, Any]]:
    with path.open(encoding="utf-8") as f:
        tests = json.load(f)
    if not isinstance(tests, list) or not tests:
        raise ValueError("O arquivo de testes precisa conter uma lista não vazia.")
    required = {"id", "domain", "prompt", "keywords", "validate_code"}
    for test in tests:
        missing = required - set(test)
        if missing:
            raise ValueError(f"Teste {test.get('id', '<sem id>')} sem campos: {sorted(missing)}")
    return tests


def get_models(base: str, timeout: int) -> list[str]:
    response = requests.get(f"{base}/v1/models", timeout=10)
    response.raise_for_status()
    return [m["id"] for m in response.json().get("data", []) if "embed" not in m["id"].lower()]


def chat(base: str, model: str, prompt: str, timeout: int, max_tokens: int) -> dict[str, Any]:
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": "Responda em português. Seja tecnicamente preciso e forneça código quando solicitado."},
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.2,
        "max_tokens": max_tokens,
        "stream": False,
    }
    started = time.perf_counter()
    response = requests.post(f"{base}/v1/chat/completions", json=payload, timeout=timeout)
    elapsed = time.perf_counter() - started
    response.raise_for_status()
    data = response.json()
    content = data["choices"][0]["message"]["content"]
    usage = data.get("usage", {})
    return {
        "content": content,
        "prompt_tokens": usage.get("prompt_tokens", 0),
        "completion_tokens": usage.get("completion_tokens", 0),
        "elapsed": round(elapsed, 4),
        "tokens_per_second": round((usage.get("completion_tokens", 0) / elapsed), 3) if elapsed else 0,
    }


def run_model(base: str, model: str, tests: list[dict[str, Any]], timeout: int, max_tokens: int) -> dict[str, Any]:
    results = []
    for number, test in enumerate(tests, 1):
        print(f"  [{number:02d}/{len(tests)}] {test['domain']}/{test['id']}", flush=True)
        try:
            answer = chat(base, model, test["prompt"], timeout, max_tokens)
            assessment = evaluate(answer["content"], test)
            results.append({
                "test_id": test["id"],
                "domain": test["domain"],
                "type": test.get("type"),
                "score": assessment["score"],
                "missing": assessment["missing"],
                "metrics": {k: answer[k] for k in ("prompt_tokens", "completion_tokens", "elapsed", "tokens_per_second")},
                "response": answer["content"],
            })
            print(f"      score={assessment['score']:.1f}")
        except Exception as exc:
            results.append({"test_id": test["id"], "domain": test["domain"], "error": str(exc)})
            print(f"      erro: {exc}")

    valid = [r for r in results if "score" in r]
    by_domain: dict[str, list[float]] = {}
    for result in valid:
        by_domain.setdefault(result["domain"], []).append(result["score"])
    summary = {domain: round(sum(scores) / len(scores), 2) for domain, scores in by_domain.items()}
    summary["overall"] = round(sum(r["score"] for r in valid) / len(valid), 2) if valid else 0
    return {"model": model, "summary": summary, "tests": results}


def main() -> None:
    parser = argparse.ArgumentParser(description="Benchmark modular de modelos via LM Studio.")
    parser.add_argument("--model", action="append", help="Modelo específico; pode repetir a opção.")
    parser.add_argument("--domain", action="append", help="Domínio a executar: Moodle, Python ou n8n.")
    parser.add_argument("--base", default=DEFAULT_BASE, help="URL base da API OpenAI-compatible.")
    parser.add_argument("--timeout", type=int, default=DEFAULT_TIMEOUT)
    parser.add_argument("--max-tokens", type=int, default=DEFAULT_MAX_TOKENS)
    parser.add_argument("--no-save-responses", action="store_true", help="Não grava respostas no arquivo de resultados.")
    args = parser.parse_args()

    tests = load_tests(PROMPTS_FILE)
    if args.domain:
        allowed = {d.lower() for d in args.domain}
        tests = [t for t in tests if t["domain"].lower() in allowed]
    if not tests:
        raise SystemExit("Nenhum teste selecionado.")

    models = args.model or get_models(args.base, args.timeout)
    print(f"AI Benchmark — {len(tests)} testes / {len(models)} modelo(s)")
    print(f"API: {args.base}")

    output = {
        "benchmark_version": "0.1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "configuration": {"base": args.base, "timeout": args.timeout, "max_tokens": args.max_tokens},
        "method": "heuristic-v0.1",
        "models": [],
    }
    for model in models:
        print(f"\n== {model} ==")
        output["models"].append(run_model(args.base, model, tests, args.timeout, args.max_tokens))

    if args.no_save_responses:
        for model_result in output["models"]:
            for result in model_result["tests"]:
                result.pop("response", None)

    RESULTS_DIR.mkdir(exist_ok=True)
    filename = RESULTS_DIR / f"run-{datetime.now().strftime('%Y%m%d-%H%M%S')}.json"
    filename.write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nResultado salvo em: {filename}")


if __name__ == "__main__":
    main()
