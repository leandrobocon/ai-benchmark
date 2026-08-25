#!/usr/bin/env python3
"""LM Studio provider adapter (OpenAI-compatible local API)."""
from __future__ import annotations

import time
from typing import Any

import requests

DEFAULT_BASE = "http://localhost:1234/v1"


def list_models(base: str = DEFAULT_BASE, timeout: int = 30) -> list[dict[str, Any]]:
    response = requests.get(f"{base}/models", timeout=timeout)
    response.raise_for_status()
    models = response.json().get("data", [])
    return [m for m in models if "embed" not in str(m.get("id", "")).lower()]


def chat(
    base: str,
    model: str,
    prompt: str,
    timeout: int,
    max_tokens: int,
    temperature: float,
    top_p: float,
    top_k: int | None,
    seed: int | None,
    reasoning_effort: str | None = None,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "model": model,
        "messages": [
            {"role": "system", "content": "Responda em português. Seja tecnicamente preciso e forneça código quando solicitado."},
            {"role": "user", "content": prompt},
        ],
        "temperature": temperature,
        "top_p": top_p,
        "max_tokens": max_tokens,
        "stream": False,
    }
    if top_k is not None:
        payload["top_k"] = top_k
    if seed is not None:
        payload["seed"] = seed
    if reasoning_effort:
        payload["reasoning"] = {"effort": reasoning_effort}

    started = time.perf_counter()
    response = requests.post(f"{base}/chat/completions", json=payload, timeout=timeout)
    elapsed = time.perf_counter() - started
    response.raise_for_status()
    data = response.json()
    choice = data["choices"][0]
    message = choice.get("message") or {}
    usage = data.get("usage") or {}
    completion_tokens = usage.get("completion_tokens", 0) or 0
    return {
        "content": message.get("content") or "",
        "usage": usage,
        "elapsed": round(elapsed, 4),
        "tokens_per_second": round(completion_tokens / elapsed, 3) if elapsed else 0,
        "finish_reason": choice.get("finish_reason"),
        "response_id": data.get("id"),
        "model_returned": data.get("model") or model,
    }
