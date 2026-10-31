"""Opt-in Vietnamese terminology probe for a local Ollama answer model."""
import json
import sys
import time

import httpx

model = sys.argv[1]
start = time.perf_counter()
response = httpx.post(
    "http://127.0.0.1:11434/api/chat",
    json={"model": model, "stream": False,
          "options": {"temperature": 0, "num_predict": 200, "num_ctx": 4096},
          "messages": [
              {"role": "system", "content": "Trả lời bằng tiếng Việt chuẩn xác trong tối đa hai câu."},
              {"role": "user", "content": "CBT là gì trong tâm lý học?"},
          ]},
    timeout=120.0,
    trust_env=False,
)
response.raise_for_status()
answer = response.json()["message"]["content"]
print(json.dumps({"model": model, "elapsed_ms": round((time.perf_counter() - start) * 1000),
                  "answer": answer}, ensure_ascii=True))
