"""Run reproducible, rate-limited operational tests for the two-URL analysis API.

The script calls the deployed local endpoint instead of importing service functions,
so the result captures the real scraper + Gemini streaming path used by the UI.
"""

from __future__ import annotations

import json
import time
from datetime import datetime, timezone
from pathlib import Path

import requests


BASE_URL = "http://127.0.0.1:8000/api/v1/debate"
OUT_DIR = Path(__file__).resolve().parents[2] / "data" / "two_url_experiment_results"

SOURCES = {
    "A": {
        "url": "https://pubmed.ncbi.nlm.nih.gov/36357950/",
        "label": "Gibbons (2022), stress, personality, coping, motivation",
    },
    "B": {
        "url": "https://pubmed.ncbi.nlm.nih.gov/33291415/",
        "label": "Teacher influence, motivation, stress, learning strategies",
    },
    "C": {
        "url": "https://pubmed.ncbi.nlm.nih.gov/22707964/",
        "label": "Stress, motivation, academic performance in medical students",
    },
}

CASES = [
    ("U01", "A", "B", "Compare how stress, motivation, and learning are related among university students."),
    ("U02", "B", "C", "Compare the evidence about academic stress, motivation, and learning outcomes in higher education."),
    ("U03", "A", "C", "Compare the roles of stress and motivation in student mental health and academic performance."),
]


def post_json(path: str, payload: dict, timeout: int = 90) -> tuple[int, dict | str]:
    response = requests.post(f"{BASE_URL}{path}", json=payload, timeout=timeout)
    try:
        body = response.json()
    except ValueError:
        body = response.text
    return response.status_code, body


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    results: list[dict] = []

    for index, (case_id, source_1, source_2, topic) in enumerate(CASES):
        url1 = SOURCES[source_1]["url"]
        url2 = SOURCES[source_2]["url"]
        payload = {"url1": url1, "url2": url2, "topic": topic}
        started = time.perf_counter()
        record = {
            "case_id": case_id,
            "run_at_utc": datetime.now(timezone.utc).isoformat(),
            "url1": url1,
            "url2": url2,
            "source_1_label": SOURCES[source_1]["label"],
            "source_2_label": SOURCES[source_2]["label"],
            "topic": topic,
        }
        try:
            scrape_status, scrape = post_json("/scrape-multi", payload)
            record["scrape_http_status"] = scrape_status
            record["scrape_preview"] = scrape
            analyze_status, analysis = post_json("/analyze", payload, timeout=180)
            record["analysis_http_status"] = analyze_status
            record["analysis_text"] = analysis
            record["success"] = analyze_status == 200 and isinstance(analysis, str) and "Warning: AI error" not in analysis
        except requests.RequestException as exc:
            record["success"] = False
            record["error"] = str(exc)
        record["elapsed_seconds"] = round(time.perf_counter() - started, 3)
        results.append(record)
        print(f"{case_id}: success={record['success']} elapsed={record['elapsed_seconds']}s")
        if index < len(CASES) - 1:
            # Gemini may temporarily return 503 under burst traffic.  Keep calls
            # below a conservative cadence so the test reflects normal operation.
            time.sleep(30)

    output = OUT_DIR / f"two_url_experiment_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    output.write_text(json.dumps({"protocol": "three real POST calls to /debate/analyze", "cases": results}, ensure_ascii=False, indent=2), encoding="utf-8")
    print(output)


if __name__ == "__main__":
    main()
