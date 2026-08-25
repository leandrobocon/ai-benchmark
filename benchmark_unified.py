#!/usr/bin/env python3
"""AI Benchmark — executor unificado para provedores locais e OpenRouter."""
from __future__ import annotations

import argparse
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from evaluator import evaluate
from providers import lmstudio, openrouter

ROOT = Path(__file__).resolve().parent
PROMPTS_FILE = ROOT / "prompts" / "benchmark.json"
RESULTS_DIR = ROOT / "resultados"
DEFAULT_TIMEOUT = int(os.getenv("AI_BENCHMARK_TIMEOUT", "180"))
DEFAULT_MAX_TOKENS = int(os.getenv("AI_BENCHMARK_MAX_TOKENS", "2048"))
FREE_DAILY_LIMIT = 50


def load_tests() -> list[dict[str, Any]]:
    tests = json.loads(PROMPTS_FILE.read_text(encoding="utf-8"))
    required = {"id", "domain", "prompt", "keywords", "validate_code"}
    if not isinstance(tests, list) or not tests:
        raise ValueError("O arquivo de testes precisa conter uma lista não vazia.")
    for test in tests:
        missing = required - set(test)
        if missing:
            raise ValueError(f"Teste {test.get('id', '<sem id>')} sem campos: {sorted(missing)}")
    return tests


def choose_tests(tests: list[dict[str, Any]]) -> list[dict[str, Any]]:
    print("\nTestes")
    print("[1] Todos")
    print("[2] Moodle")
    print("[3] Python")
    print("[4] n8n")
    print("[5] Selecionar individualmente")
    print("[0] Cancelar")
    while True:
        choice = input("Opção: ").strip()
        if choice == "0":
            raise SystemExit("Execução cancelada.")
        if choice == "1":
            return tests
        if choice in {"2", "3", "4"}:
            domain = {"2": "Moodle", "3": "Python", "4": "n8n"}[choice]
            return [t for t in tests if t["domain"].lower() == domain.lower()]
        if choice == "5":
            for i, test in enumerate(tests, 1):
                print(f"[{i:02d}] {test['domain']}/{test['id']}")
            raw = input("Números (ex.: 1,4,7-10): ").strip()
            indexes: set[int] = set()
            try:
                for part in raw.split(","):
                    if "-" in part:
                        a, b = map(int, part.split("-", 1))
                        indexes.update(range(a, b + 1))
                    else:
                        indexes.add(int(part))
                if not indexes or any(i < 1 or i > len(tests) for i in indexes):
                    raise ValueError
                return [tests[i - 1] for i in sorted(indexes)]
            except ValueError:
                print("Seleção inválida.")


def choose_local(models: list[dict[str, Any]]) -> list[dict[str, Any]]:
    models = sorted(models, key=lambda m: m.get("id", ""))
    print("\nModelos locais disponíveis")
    print("=" * 80)
    for i, model in enumerate(models, 1):
        print(f"[{i:02d}] {model.get('id', '<sem id>')}")
    print("=" * 80)
    while True:
        try:
            choice = int(input("Modelo: ").strip())
        except ValueError:
            print("Digite um número.")
            continue
        if choice == 0:
            raise SystemExit("Execução cancelada.")
        if 1 <= choice <= len(models):
            return [models[choice - 1]]
        print(f"Escolha entre 1 e {len(models)}, ou 0 para cancelar.")


def run(provider: Any, args: argparse.Namespace, model: dict[str, Any], tests: list[dict[str, Any]]) -> dict[str, Any]:
    model_id = model["id"]
    results = []
    for n, test in enumerate(tests, 1):
        print(f"  [{n:02d}/{len(tests)}] {test['domain']}/{test['id']}", flush=True)
        try:
            answer = provider.chat(args.base, model_id, test["prompt"], args.timeout, args.max_tokens, args.temperature, args.top_p, args.top_k, args.seed, args.reasoning_effort)
            assessment = evaluate(answer["content"], test)
            usage = answer.get("usage") or {}
            metrics = {
                "prompt_tokens": usage.get("prompt_tokens", 0),
                "completion_tokens": usage.get("completion_tokens", 0),
                "reasoning_tokens": usage.get("reasoning_tokens", 0),
                "total_tokens": usage.get("total_tokens", 0),
                "cost": usage.get("cost"),
                "elapsed": answer.get("elapsed"),
                "tokens_per_second": answer.get("tokens_per_second"),
            }
            result = {"test_id": test["id"], "domain": test["domain"], "type": test.get("type"), "score": assessment["score"], "missing": assessment["missing"], "metrics": metrics, "finish_reason": answer.get("finish_reason"), "response_id": answer.get("response_id"), "model_returned": answer.get("model_returned")}
            if not args.no_save_responses:
                result["response"] = answer["content"]
            results.append(result)
            print(f"      score={assessment['score']:.1f} tokens={metrics['total_tokens']} cost={metrics['cost']} tok/s={metrics['tokens_per_second']}")
        except Exception as exc:
            results.append({"test_id": test["id"], "domain": test["domain"], "error": str(exc)})
            print(f"      erro: {exc}")

    valid = [r for r in results if "score" in r]
    by_domain: dict[str, list[float]] = {}
    for r in valid:
        by_domain.setdefault(r["domain"], []).append(r["score"])
    summary = {d: round(sum(v) / len(v), 2) for d, v in by_domain.items()}
    summary["overall"] = round(sum(r["score"] for r in valid) / len(valid), 2) if valid else 0
    costs = [r["metrics"]["cost"] for r in valid if isinstance(r["metrics"].get("cost"), (int, float))]
    return {"model": model_id, "model_metadata": model, "summary": summary, "summary_metrics": {"tests_completed": len(valid), "total_tokens": sum((r["metrics"].get("total_tokens") or 0) for r in valid), "total_cost": round(sum(costs), 8) if costs else None, "avg_latency_seconds": round(sum(r["metrics"]["elapsed"] for r in valid) / len(valid), 4) if valid else None}, "tests": results}


def main() -> None:
    p = argparse.ArgumentParser(description="AI Benchmark unificado: local ou OpenRouter.")
    p.add_argument("--provider", choices=["local", "openrouter"], default="local")
    p.add_argument("--model", action="append", help="ID específico; pode repetir.")
    p.add_argument("--free-only", action="store_true")
    p.add_argument("--base")
    p.add_argument("--timeout", type=int, default=DEFAULT_TIMEOUT)
    p.add_argument("--max-tokens", type=int, default=DEFAULT_MAX_TOKENS)
    p.add_argument("--temperature", type=float, default=0.2)
    p.add_argument("--top-p", type=float, default=1.0)
    p.add_argument("--top-k", type=int)
    p.add_argument("--seed", type=int)
    p.add_argument("--reasoning-effort", choices=["low", "medium", "high"])
    p.add_argument("--no-save-responses", action="store_true")
    args = p.parse_args()

    tests = choose_tests(load_tests())
    if args.provider == "local":
        provider = lmstudio
        args.base = args.base or os.getenv("LMSTUDIO_BASE", lmstudio.DEFAULT_BASE)
        catalog = provider.list_models(args.base, args.timeout)
        if not catalog:
            raise SystemExit("Nenhum modelo local encontrado no LM Studio.")
        if args.model:
            by_id = {m["id"]: m for m in catalog}
            missing = [m for m in args.model if m not in by_id]
            if missing:
                raise SystemExit(f"Modelo(s) local(is) não encontrado(s): {', '.join(missing)}")
            models = [by_id[m] for m in args.model]
        else:
            models = choose_local(catalog)
        quota_note = "Local: sem cota de API; limite prático depende do hardware e do tempo."
    else:
        provider = openrouter
        args.base = args.base or os.getenv("OPENROUTER_BASE", openrouter.DEFAULT_BASE)
        if not os.getenv("OPENROUTER_API_KEY"):
            raise SystemExit("Defina OPENROUTER_API_KEY no ambiente.")
        catalog = provider.list_models(args.base, args.timeout, free_only=args.free_only)
        if not catalog:
            raise SystemExit("Nenhum modelo encontrado no OpenRouter.")
        if args.model:
            by_id = {m["id"]: m for m in catalog}
            missing = [m for m in args.model if m not in by_id]
            if missing:
                raise SystemExit(f"Modelo(s) não encontrado(s): {', '.join(missing)}")
            models = [by_id[m] for m in args.model]
        else:
            from benchmark_api import print_model_menu
            models = print_model_menu(catalog)
        quota_note = f"OpenRouter Free: referência de {FREE_DAILY_LIMIT} requisições/dia; o saldo restante não é consultado."

    requests_planned = len(models) * len(tests)
    print(f"\nExecução planejada: {len(models)} modelo(s) × {len(tests)} teste(s) = {requests_planned} requisição(ões).")
    print(quota_note)
    if args.provider == "openrouter" and args.free_only and requests_planned > FREE_DAILY_LIMIT:
        raise SystemExit(f"Execução bloqueada: {requests_planned} requisições excedem a referência de {FREE_DAILY_LIMIT}/dia.")
    if input("Continuar? [s/N]: ").strip().lower() not in {"s", "sim", "y", "yes"}:
        raise SystemExit("Execução cancelada.")

    output = {"benchmark_version": "0.3", "generated_at": datetime.now(timezone.utc).isoformat(), "provider": args.provider, "configuration": {"base": args.base, "timeout": args.timeout, "max_tokens": args.max_tokens, "temperature": args.temperature, "top_p": args.top_p, "top_k": args.top_k, "seed": args.seed, "reasoning_effort": args.reasoning_effort, "free_only": args.free_only, "test_count": len(tests), "model_count": len(models), "estimated_requests": requests_planned}, "method": "heuristic-v0.1", "models": []}
    for model in models:
        print(f"\n== {model['id']} ==")
        output["models"].append(run(provider, args, model, tests))

    RESULTS_DIR.mkdir(exist_ok=True)
    filename = RESULTS_DIR / f"run-{args.provider}-{datetime.now().strftime('%Y%m%d-%H%M%S')}.json"
    filename.write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nResultado salvo em: {filename}")


if __name__ == "__main__":
    main()
