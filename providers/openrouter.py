#!/usr/bin/env python3
"""OpenRouter provider adapter for AI Benchmark."""
from __future__ import annotations

import os
import time
from typing import Any

import requests

DEFAULT_BASE = "https://openrouter.ai/api/v1"


def _headers() -> dict[str, str]:
    headers = {
        "Authorization": f"Bearer {os.environ['OPENROUTER_API_KEY']}",
        "Content-Type": "application/json",
    }
    referer = os.getenv("OPENROUTER_HTTP_REFERER")
    title = os.getenv("OPENROUTER_X_TITLE")
    if referer:
        headers["HTTP-Referer"] = referer
    if title:
        headers["X-Title"] = title
    return headers


def list_models(base: str = DEFAULT_BASE, timeout: int = 30, free_only: bool = False) -> list[dict[str, Any]]:
    response = requests.get(f"{base}/models", headers=_headers(), timeout=timeout)
    response.raise_for_status()
    models = response.json().get("data", [])
    if not free_only:
        return models

    free = []
    for model in models:
        pricing = model.get("pricing") or {}
        prompt = str(pricing.get("prompt", ""))
        completion = str(pricing.get("completion", ""))
        if prompt == "0" and completion == "0":
            free.append(model)
    return free


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
        "usage": {"include": True},
    }
    if top_k is not None:
        payload["top_k"] = top_k
    if seed is not None:
        payload["seed"] = seed
    if reasoning_effort:
        payload["reasoning"] = {"effort": reasoning_effort}

    started = time.perf_counter()
    response = requests.post(f"{base}/chat/completions", headers=_headers(), json=payload, timeout=timeout)
    elapsed = time.perf_counter() - started
    response.raise_for_status()
    data = response.json()
    message = data["choices"][0]["message"]
    usage = data.get("usage") or {}
    return {
        "content": message.get("content") or "",
        "usage": usage,
        "elapsed": round(elapsed, 4),
        "finish_reason": data["choices"][0].get("finish_reason"),
        "response_id": data.get("id"),
        "model_returned": data.get("model"),
    }
