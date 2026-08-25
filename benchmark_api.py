#!/usr/bin/env python3
"""AI Benchmark API runner.

OpenRouter runner with explicit interactive model and test selection. By default
it never runs the benchmark against every discovered model or every test: the
user selects one model and a test scope before any inference request is made.
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
FREE_DAILY_LIMIT = 50


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
    by_id = {m.get("id"): m for m in models}
    if requested:
        selected = []
        for model_id in requested:
            if model_id not in by_id:
                raise SystemExit(f"Modelo não encontrado no catálogo OpenRouter: {model_id}")
            selected.append(by_id[model_id])
        return selected
    if limit:
        return sorted(models, key=lambda m: m.get("id", ""))[:limit]
    return []


def model_price(model: dict[str, Any]) -> str:
    pricing = model.get("pricing") or {}
    prompt = pricing.get("prompt")
    completion = pricing.get("completion")
    if prompt == "0" and completion == "0":
        return "FREE"
    return f"in={prompt} / out={completion}"


def print_model_menu(models: list[dict[str, Any]]) -> list[dict[str, Any]]:
    models = sorted(models, key=lambda m: m.get("id", ""))
    print("\nModelos OpenRouter disponíveis para teste")
    print("=" * 90)
    print(f"Cota de referência: até {FREE_DAILY_LIMIT} requisições/dia no plano Free.")
    print("Cada teste do benchmark faz 1 requisição. Nada será executado até a escolha.\n")
    for index, model in enumerate(models, 1):
        model_id = model.get("id", "<sem id>")
        name = model.get("name") or model_id
        context = model.get("context_length") or "?"
        print(f"[{index:02d}] {name}")
        print(f"     id: {model_id}")
        print(f"     contexto: {context} | preço: {model_price(model)}")
    print("=" * 90)
    print("Digite o número do modelo para selecionar apenas esse modelo.")
    print("Digite 0 para cancelar.")

    while True:
        raw = input("\nModelo: ").strip()
        try:
            choice = int(raw)
        except ValueError:
            print("Digite um número válido.")
            continue
        if choice == 0:
            raise SystemExit("Execução cancelada pelo usuário.")
        if 1 <= choice <= len(models):
            selected = models[choice - 1]
            print(f"Selecionado: {selected.get('id')}")
            return [selected]
        print(f"Escolha um número entre 1 e {len(models)}, ou 0 para cancelar.")


def print_test_menu(tests: list[dict[str, Any]]) -> list[dict[str, Any]]:
    domains = {}
    for test in tests:
        domains.setdefault(test["domain"], []).append(test)

    print("\nTestes disponíveis")
    print("=" * 90)
    print("[1] Todos os testes")
    domain_items = list(domains.items())
    for index, (domain, domain_tests) in enumerate(domain_items, 2):
        print(f"[{index}] {domain} ({len(domain_tests)} testes)")
    print(f"[{len(domain_items) + 2}] Escolher testes individualmente")
    print("[0] Cancelar")
    print("=" * 90)

    while True:
        raw = input("\nOpção de testes: ").strip()
        try:
            choice = int(raw)
        except ValueError:
            print("Digite um número válido.")
            continue
        if choice == 0:
            raise SystemExit("Execução cancelada pelo usuário.")
        if choice == 1:
            return tests
        domain_index = choice - 2
        if 0 <= domain_index < len(domain_items):
            domain, domain_tests = domain_items[domain_index]
            return domain_tests
        if choice == len(domain_items) + 2:
            return select_individual_tests(tests)
        print("Opção inválida.")


def select_individual_tests(tests: list[dict[str, Any]]) -> list[dict[str, Any]]:
    print("\nSeleção individual")
    print("Digite os números separados por vírgula. Exemplo: 1,4,7")
    print("Também é possível usar intervalos. Exemplo: 1-5,8,12-14")
    print("Digite 0 para cancelar.")
    for index, test in enumerate(tests, 1):
        print(f"[{index:02d}] {test['domain']:<8} {test['id']:<14} {test.get('type', '')}")

    while True:
        raw = input("\nTestes: ").strip()
        if raw == "0":
            raise SystemExit("Execução cancelada pelo usuário.")
        try:
            selected_numbers = parse_selection(raw, len(tests))
        except ValueError as exc:
            print(f"Seleção inválida: {exc}")
            continue
        if not selected_numbers:
            print("Nenhum teste selecionado.")
            continue
        selected = [tests[number - 1] for number in selected_numbers]
        print(f"Selecionados: {len(selected)} teste(s).")
        return selected


def parse_selection(raw: str, maximum: int) -> list[int]:
    values: set[int] = set()
    for part in raw.replace(" ", "").split(","):
        if not part:
            continue
        if "-" in part:
            pieces = part.split("-", 1)
            if len(pieces) != 2 or not pieces[0].isdigit() or not pieces[1].isdigit():
                raise ValueError(f"intervalo inválido: {part}")
            start, end = int(pieces[0]), int(pieces[1])
            if start > end:
                start, end = end, start
            values.update(range(start, end + 1))
        elif part.isdigit():
            values.add(int(part))
        else:
            raise ValueError(f"valor inválido: {part}")
    invalid = sorted(value for value in values if value < 1 or value > maximum)
    if invalid:
        raise ValueError(f"número(s) fora do intervalo 1-{maximum}: {invalid}")
    return sorted(values)


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
    parser.add_argument("--free-only", action="store_true", help="Mostra somente modelos com preço $0/$0 no catálogo.")
    parser.add_argument("--limit-models", type=int, help="Seleciona automaticamente até N modelos; use somente em execução controlada.")
    parser.add_argument("--all", action="store_true", help="Executa em todos os modelos descobertos. Evite no plano Free.")
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
    if not catalog:
        raise SystemExit("Nenhum modelo encontrado no catálogo OpenRouter.")

    if args.model:
        models = select_models(catalog, args.model, args.limit_models)
    elif args.all:
        models = sorted(catalog, key=lambda m: m.get("id", ""))
    elif args.limit_models:
        models = select_models(catalog, None, args.limit_models)
    else:
        models = print_model_menu(catalog)

    if args.domain or args.limit_tests:
        # Command-line filters intentionally remain authoritative when supplied.
        selected_tests = tests
    else:
        selected_tests = print_test_menu(tests)

    estimated_requests = len(models) * len(selected_tests)
    print(f"\nExecução planejada: {len(models)} modelo(s) × {len(selected_tests)} teste(s) = {estimated_requests} requisição(ões).")
    if args.free_only and estimated_requests > FREE_DAILY_LIMIT:
        raise SystemExit(
            f"Execução bloqueada: {estimated_requests} requisições excedem a referência de {FREE_DAILY_LIMIT}/dia do plano Free. "
            "Use --limit-tests, selecione menos testes ou execute em outro dia."
        )
    if args.free_only:
        print(f"Atenção: o plano Free do OpenRouter tem limite diário de {FREE_DAILY_LIMIT} requisições e limite por minuto. Esta execução não consulta o saldo restante da conta.")
        confirmation = input("Continuar? [s/N]: ").strip().lower()
        if confirmation not in {"s", "sim", "y", "yes"}:
            raise SystemExit("Execução cancelada pelo usuário.")

    print(f"AI Benchmark API — {len(selected_tests)} testes / {len(models)} modelo(s)")
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
            "test_count": len(selected_tests),
            "model_count": len(models),
            "estimated_requests": estimated_requests,
        },
        "method": "heuristic-v0.1",
        "models": [],
    }
    for model_meta in models:
        print(f"\n== {model_meta['id']} ==")
        output["models"].append(run_model(args, model_meta, selected_tests))

    RESULTS_DIR.mkdir(exist_ok=True)
    filename = RESULTS_DIR / f"api-openrouter-{datetime.now().strftime('%Y%m%d-%H%M%S')}.json"
    filename.write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nResultado salvo em: {filename}")


if __name__ == "__main__":
    main()
