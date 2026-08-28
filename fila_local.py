#!/usr/bin/env python3
"""Fila noturna dos modelos locais, em lotes de dois."""
from __future__ import annotations

import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent
RESULTS = ROOT / "resultados"

# O lote Qwen 3.6 já está em execução; aguardamos seu JSON antes de iniciar.
BATCHES = [
    ["google/gemma-4-26b-a4b-qat", "qwen/qwen3.5-9b"],
    ["openai/gpt-oss-20b", "qwen/qwen2.5-coder-14b"],
    ["qwen3.8-27b-uncensored-mlx", "qwen3.8-27b-mlx"],
]


def result_count() -> int:
    return len(list(RESULTS.glob("run-local-*.json")))


def run_batch(models: list[str]) -> None:
    command = [sys.executable, "benchmark_unified.py", "--provider", "local"]
    for model in models:
        command.extend(["--model", model])
    command.append("--no-save-responses")
    print(f"\n=== Próximo lote: {', '.join(models)} ===", flush=True)
    completed = subprocess.run(command, input="1\ns\n", text=True, cwd=ROOT)
    if completed.returncode != 0:
        print(f"Lote terminou com código {completed.returncode}; seguindo para o próximo.", flush=True)


def main() -> None:
    print("Aguardando o lote Qwen 3.6 atual terminar...", flush=True)
    while result_count() < 4:
        time.sleep(30)
    for batch in BATCHES:
        before = result_count()
        run_batch(batch)
        while result_count() <= before:
            time.sleep(30)
    print("\nFila concluída.", flush=True)


if __name__ == "__main__":
    main()
