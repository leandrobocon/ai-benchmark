#!/usr/bin/env python3
"""AI Benchmark API runner.

Supports OpenRouter first; the test set and evaluator are shared with local runs.
"""
from __future__ import annotations

import argparse
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from evaluator import evaluate
from providers import openrouter

ROOT = Path(__file__).resolve().parent
PROMPTS_FILE = ROOT / "prompts" / "benchmark.json"
RESULTS_DIR = ROOT / "resultados"
DEFAULT_TIMEOUT = int(os.getenv("AI_BENCHMARK_TIMEOUT", "180"))
DEFAULT_MAX_TOKENS = int(os.getenv("AI_BENCHMARK_MAX_TOKENS", "2048"))


def load_tests(path: Path) -> list[dict[str, Any]]:
    tests = json.loads(path.read_text(encoding="utf-8"))
    required = {"id", "domain", "prompt", "keywords", "validate_code"}
    if not isinstance(tests, list) or not tests:
        raise ValueError("O arquivo de testes precisa conter uma lista não vazia.")
    for test in tests:
        missing = required - set(test)
        if missing:
            raise ValueError(f"Teste {test.get('id', '<sem id>')} sem campos: {sorted(missing)}")
    return tests


def select_models(models: list[dict[str, Any]], requested: list[str] | None, limit: int | None) -> list[dict[str, Any]]:
    if requested:
        by_id = {m.get("id"): m for m in models}
        selected = []
        for model_id in requested:
            if model_id not in by_id:
                raise SystemExit(f"Modelo não encontrado no catálogo OpenRouter: {model_id}")
            selected.append(by_id[model_id])
        return selected
    models = sorted(models, key=lambda m: m.get("id", ""))
    return models[:limit] if limit else models


def token_value(usage: dict[str, Any], key: str) -> int | float:
    value = usage.get(key, 0)
    return value if isinstance(value, (int, float)) else 0


def run_model(args: argparse.Namespace, model_meta: dict[str, Any], tests: list[dict[str, Any]]) -> dict[str, Any]:
    model_id = model_meta["id"]
    results = []
    for number, test in enumerate(tests, 1):
        print(f"  [{number:02d}/{len(tests)}] {test['domain']}/{test['id']}", flush=True)
        try:
            answer = openrouter.chat(
                args.base,
                model_id,
                test["prompt"],
                args.timeout,
                args.max_tokens,
                args.temperature,
                args.top_p,
                args.top_k,
                args.seed,
                args.reasoning_effort,
            )
            assessment = evaluate(answer["content"], test)
            usage = answer["usage"]
            result = {
                "test_id": test["id"],
                "domain": test["domain"],
                "type": test.get("type"),
                "score": assessment["score"],
                "missing": assessment["missing"],
                "metrics": {
                    "prompt_tokens": token_value(usage, "prompt_tokens"),
                    "completion_tokens": token_value(usage, "completion_tokens"),
                    "reasoning_tokens": token_value(usage, "reasoning_tokens"),
                    "total_tokens": token_value(usage, "total_tokens"),
                    "cost": usage.get("cost"),
                    "elapsed": answer["elapsed"],
                },
                "finish_reason": answer["finish_reason"],
                "response_id": answer["response_id"],
                "model_returned": answer["model_returned"],
            }
            if not args.no_save_responses:
                result["response"] = answer["content"]
            results.append(result)
            print(f"      score={assessment['score']:.1f} tokens={result['metrics']['total_tokens']} cost={result['metrics']['cost']}")
        except Exception as exc:
            results.append({"test_id": test["id"], "domain": test["domain"], "error": str(exc)})
            print(f"      erro: {exc}")

    valid = [r for r in results if "score" in r]
    by_domain: dict[str, list[float]] = {}
    for result in valid:
        by_domain.setdefault(result["domain"], []).append(result["score"])
    summary = {d: round(sum(v) / len(v), 2) for d, v in by_domain.items()}
    summary["overall"] = round(sum(r["score"] for r in valid) / len(valid), 2) if valid else 0
    costs = [r["metrics"]["cost"] for r in valid if isinstance(r["metrics"].get("cost"), (int, float))]
    tokens = [r["metrics"]["total_tokens"] for r in valid]
    summary_metrics = {
        "tests_completed": len(valid),
        "total_tokens": sum(tokens),
        "total_cost": round(sum(costs), 8) if costs else None,
        "avg_latency_seconds": round(sum(r["metrics"]["elapsed"] for r in valid) / len(valid), 4) if valid else None,
    }
    return {
        "model": model_id,
        "model_metadata": {
            "name": model_meta.get("name"),
            "context_length": model_meta.get("context_length"),
            "architecture": model_meta.get("architecture"),
            "pricing": model_meta.get("pricing"),
        },
        "summary": summary,
        "summary_metrics": summary_metrics,
        "tests": results,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="AI Benchmark via OpenRouter.")
    parser.add_argument("--model", action="append", help="Modelo OpenRouter; pode repetir a opção.")
    parser.add_argument("--free-only", action="store_true", help="Seleciona somente modelos com preço $0/$0 no catálogo.")
    parser.add_argument("--limit-models", type=int, help="Limita modelos descobertos automaticamente.")
    parser.add_argument("--domain", action="append", help="Domínio: Moodle, Python ou n8n; pode repetir.")
    parser.add_argument("--limit-tests", type=int, help="Limita o número total de testes nesta execução.")
    parser.add_argument("--base", default=os.getenv("OPENROUTER_BASE", openrouter.DEFAULT_BASE))
    parser.add_argument("--timeout", type=int, default=DEFAULT_TIMEOUT)
    parser.add_argument("--max-tokens", type=int, default=DEFAULT_MAX_TOKENS)
    parser.add_argument("--temperature", type=float, default=0.2)
    parser.add_argument("--top-p", type=float, default=1.0)
    parser.add_argument("--top-k", type=int)
    parser.add_argument("--seed", type=int)
    parser.add_argument("--reasoning-effort", choices=["low", "medium", "high"])
    parser.add_argument("--no-save-responses", action="store_true")
    args = parser.parse_args()

    if not os.getenv("OPENROUTER_API_KEY"):
        raise SystemExit("Defina OPENROUTER_API_KEY no ambiente. Nunca coloque a chave no repositório.")

    tests = load_tests(PROMPTS_FILE)
    if args.domain:
        allowed = {d.lower() for d in args.domain}
        tests = [t for t in tests if t["domain"].lower() in allowed]
    if args.limit_tests:
        tests = tests[:args.limit_tests]
    if not tests:
        raise SystemExit("Nenhum teste selecionado.")

    catalog = openrouter.list_models(args.base, args.timeout, free_only=args.free_only)
    models = select_models(catalog, args.model, args.limit_models)
    if not models:
        raise SystemExit("Nenhum modelo selecionado.")

    print(f"AI Benchmark API — {len(tests)} testes / {len(models)} modelo(s)")
    print(f"OpenRouter: {args.base}")
    print(f"Parâmetros: temperature={args.temperature}, top_p={args.top_p}, top_k={args.top_k}, seed={args.seed}, max_tokens={args.max_tokens}, reasoning_effort={args.reasoning_effort}")

    output = {
        "benchmark_version": "0.2",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "provider": "openrouter",
        "configuration": {
            "base": args.base,
            "timeout": args.timeout,
            "max_tokens": args.max_tokens,
            "temperature": args.temperature,
            "top_p": args.top_p,
            "top_k": args.top_k,
            "seed": args.seed,
            "reasoning_effort": args.reasoning_effort,
            "free_only": args.free_only,
            "test_count": len(tests),
        },
        "method": "heuristic-v0.1",
        "models": [],
    }
    for model_meta in models:
        print(f"\n== {model_meta['id']} ==")
        output["models"].append(run_model(args, model_meta, tests))

    RESULTS_DIR.mkdir(exist_ok=True)
    filename = RESULTS_DIR / f"api-openrouter-{datetime.now().strftime('%Y%m%d-%H%M%S')}.json"
    filename.write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nResultado salvo em: {filename}")


if __name__ == "__main__":
    main()
