"""
Phase 2 — RAGAS evaluation runner.

Imports RAGSystem directly (no HTTP) so it works with or without a running server.

Usage:
    cd evals
    python ragas/evaluate_ragas.py

Thresholds:
    faithfulness        > 0.85
    answer_relevancy    > 0.80
    context_precision   > 0.75
    context_recall      > 0.70

Exit code 1 if any threshold is missed.
"""

import json
import os
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Bootstrap Django so we can import backend modules directly.
# ---------------------------------------------------------------------------
BACKEND_DIR = Path(__file__).parent.parent.parent / "backend"
sys.path.insert(0, str(BACKEND_DIR))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")

import django
django.setup()

from chat.rag import get_rag_system  # noqa: E402 — must come after django.setup()

# ---------------------------------------------------------------------------
# RAGAS imports
# ---------------------------------------------------------------------------
from datasets import Dataset  # noqa: E402
from ragas import evaluate  # noqa: E402
from ragas.metrics import (  # noqa: E402
    faithfulness,
    answer_relevancy,
    context_precision,
    context_recall,
)

THRESHOLDS = {
    "faithfulness": 0.85,
    "answer_relevancy": 0.80,
    "context_precision": 0.75,
    "context_recall": 0.70,
}

GOLDEN_PATH = Path(__file__).parent.parent / "datasets" / "golden_qa.json"
RESULTS_DIR = Path(__file__).parent.parent / "results"
RESULTS_DIR.mkdir(exist_ok=True)


def build_ragas_dataset(rag, golden: list[dict]) -> Dataset:
    questions, answers, contexts, ground_truths = [], [], [], []

    for item in golden:
        q = item["question"]
        gt = item["ground_truth"]

        docs = rag.retriever.invoke(q)
        ctx = [doc.page_content for doc in docs]
        answer, _ = rag.chat(q, [])

        questions.append(q)
        answers.append(answer)
        contexts.append(ctx)
        ground_truths.append(gt)
        print(f"  ✓ {q[:60]}...")

    return Dataset.from_dict(
        {
            "question": questions,
            "answer": answers,
            "contexts": contexts,
            "ground_truth": ground_truths,
        }
    )


def run() -> int:
    print("=== RAGAS Evaluation ===\n")

    golden = json.loads(GOLDEN_PATH.read_text(encoding="utf-8"))
    print(f"Loaded {len(golden)} golden Q&A pairs.\n")

    rag = get_rag_system()
    print("Collecting answers from RAG system...")
    dataset = build_ragas_dataset(rag, golden)

    print("\nRunning RAGAS metrics (this calls OpenAI — ~1–2 min)...")
    result = evaluate(
        dataset,
        metrics=[faithfulness, answer_relevancy, context_precision, context_recall],
    )

    scores = {
        "faithfulness": float(result["faithfulness"]),
        "answer_relevancy": float(result["answer_relevancy"]),
        "context_precision": float(result["context_precision"]),
        "context_recall": float(result["context_recall"]),
    }

    print("\n--- Results ---")
    failed = []
    for metric, score in scores.items():
        threshold = THRESHOLDS[metric]
        status = "PASS" if score >= threshold else "FAIL"
        print(f"  {metric:<25} {score:.3f}  (threshold {threshold})  [{status}]")
        if status == "FAIL":
            failed.append(metric)

    out_path = RESULTS_DIR / "ragas_results.json"
    out_path.write_text(json.dumps({"scores": scores, "thresholds": THRESHOLDS, "failed": failed}, indent=2))
    print(f"\nResults saved to {out_path}")

    if failed:
        print(f"\n✗ {len(failed)} metric(s) below threshold: {', '.join(failed)}")
        return 1

    print("\n✓ All metrics passed.")
    return 0


if __name__ == "__main__":
    sys.exit(run())
