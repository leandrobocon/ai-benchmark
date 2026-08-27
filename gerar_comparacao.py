#!/usr/bin/env python3
"""Gera uma página HTML comparando todas as execuções salvas em resultados/."""
from __future__ import annotations

import html
import json
import platform
import subprocess
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent
RESULTS = ROOT / "resultados"
OUTPUT = RESULTS / "comparacao.html"


def load_rows() -> list[dict]:
    rows = []
    for path in sorted(RESULTS.glob("*.json")):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if not isinstance(data, dict):
            continue
        for model in data.get("models", []):
            tests = [t for t in model.get("tests", []) if "score" in t]
            if not tests:
                continue
            summary = model.get("summary", {})
            metrics = model.get("summary_metrics", {})
            rows.append({
                "arquivo": path.name,
                "modelo": model.get("model", "<sem modelo>"),
                "moodle": summary.get("Moodle", "—"),
                "python": summary.get("Python", "—"),
                "n8n": summary.get("n8n", "—"),
                "overall": summary.get("overall", "—"),
                "testes": metrics.get("tests_completed", len(tests)),
                "tokens": metrics.get("total_tokens", "—"),
                "latencia": metrics.get("avg_latency_seconds", "—"),
            })
    return sorted(rows, key=lambda row: (-(row["overall"] if isinstance(row["overall"], (int, float)) else -1), row["modelo"]))


def cell(value: object) -> str:
    return html.escape(str(value))


def environment_info() -> list[tuple[str, str]]:
    chip = "indisponível"
    try:
        chip = subprocess.run(
            ["sysctl", "-n", "machdep.cpu.brand_string"],
            capture_output=True, text=True, check=False,
        ).stdout.strip() or chip
        if chip == "indisponível":
            hardware = subprocess.run(
                ["system_profiler", "SPHardwareDataType"],
                capture_output=True, text=True, check=False,
            ).stdout
            chip = next((line.split(":", 1)[1].strip() for line in hardware.splitlines() if line.strip().startswith("Chip:")), chip)
    except OSError:
        pass
    return [
        ("Provedor", "LM Studio"),
        ("Hardware", f"{chip} · 24 GB RAM"),
        ("Sistema", f"{platform.system()} {platform.mac_ver()[0] or platform.release()}"),
        ("Python", sys.version.split()[0]),
        ("Atualizado em", datetime.now().strftime("%d/%m/%Y %H:%M")),
    ]


def main() -> None:
    rows = load_rows()
    environment = " · ".join(f"<strong>{html.escape(name)}:</strong> {html.escape(value)}" for name, value in environment_info())
    body = "\n".join(
        "<tr>" + "".join(f"<td>{cell(row[key])}</td>" for key in ("modelo", "moodle", "python", "n8n", "overall", "testes", "tokens", "latencia", "arquivo")) + "</tr>"
        for row in rows
    ) or '<tr><td colspan="9">Nenhum resultado válido encontrado ainda.</td></tr>'
    page = f'''<!doctype html>
<html lang="pt-BR"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Comparação — AI Benchmark</title>
<style>
body{{font:15px system-ui,sans-serif;background:#f5f7fb;color:#172033;margin:32px}} h1{{margin-bottom:6px}}
.note{{color:#5b6578;margin-bottom:22px}} .wrap{{overflow:auto;background:white;border-radius:12px;box-shadow:0 2px 14px #17203318}}
table{{border-collapse:collapse;min-width:1100px;width:100%}} th,td{{padding:12px 14px;border-bottom:1px solid #e7eaf0;text-align:right;white-space:nowrap}}
th{{background:#15243d;color:white;position:sticky;top:0}} th:first-child,td:first-child{{text-align:left;position:sticky;left:0}} td:first-child{{background:white;font-weight:600}}
tr:hover td{{background:#eef5ff}} .score{{font-weight:700;color:#176b46}}
</style></head><body>
<h1>AI Benchmark — comparação</h1><div class="note">{environment}</div>
<div class="wrap"><table><thead><tr><th>Modelo</th><th>Moodle</th><th>Python</th><th>n8n</th><th>Geral</th><th>Testes</th><th>Tokens</th><th>Latência média (s)</th><th>Arquivo</th></tr></thead><tbody>{body}</tbody></table></div>
</body></html>'''
    OUTPUT.write_text(page, encoding="utf-8")
    print(f"Página gerada: {OUTPUT}")
    print(f"Modelos válidos comparados: {len(rows)}")


if __name__ == "__main__":
    main()
