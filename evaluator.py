#!/usr/bin/env python3
"""Heurística inicial de avaliação para o AI Benchmark.

A pontuação não mede 'inteligência' de forma absoluta. Ela verifica a presença
 de critérios declarados no teste e deve ser complementada por revisão humana
 quando a correção técnica for importante.
"""
from __future__ import annotations

from typing import Any


def evaluate(response: str, test: dict[str, Any]) -> dict[str, Any]:
    text = response.lower()
    keywords = test.get("keywords", [])
    score = 0.0
    missing: list[str] = []

    if keywords:
        points = 70.0 / len(keywords)
        for keyword in keywords:
            if str(keyword).lower() in text:
                score += points
            else:
                missing.append(str(keyword))

    if test.get("validate_code"):
        marker = str(test.get("code_marker", "")).lower()
        if marker and marker in text:
            score += 30.0
        elif "```" in response:
            score += 20.0
            missing.append(f"[código:{marker}]")
        else:
            missing.append(f"[código:{marker}]")
    else:
        words = len(response.split())
        if words > 50:
            score += 30.0
        elif words > 20:
            score += 20.0
        elif words > 5:
            score += 10.0

    return {
        "score": round(min(score, 100.0), 1),
        "missing": missing,
        "method": "heuristic-v0.1",
    }
