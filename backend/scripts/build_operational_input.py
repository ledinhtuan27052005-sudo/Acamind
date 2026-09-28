"""Create a labelled 1,000-execution input dataset from approved QA cases."""

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "data" / "eval_questions.json"
OUTPUT = ROOT / "data" / "operational_test_1000_input.json"
REPETITIONS = 100


def main() -> None:
    base_cases = json.loads(SOURCE.read_text(encoding="utf-8"))
    required = {"question", "ground_truth", "document_ids"}
    if not base_cases or any(required - case.keys() for case in base_cases):
        raise ValueError("eval_questions.json phải chứa question, ground_truth và document_ids.")

    records = []
    for replication in range(1, REPETITIONS + 1):
        for source_case_id, case in enumerate(base_cases, 1):
            execution_id = len(records) + 1
            records.append({
                "case_id": f"OP-{execution_id:04d}",
                "source_case_id": source_case_id,
                "replication": replication,
                "dataset_type": "operational_repeat",
                "question": case["question"],
                "ground_truth": case["ground_truth"],
                "document_ids": case["document_ids"],
                "review_status": "approved_source_case",
            })

    OUTPUT.write_text(json.dumps(records, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Created {len(records)} labelled operational executions: {OUTPUT}")


if __name__ == "__main__":
    main()
