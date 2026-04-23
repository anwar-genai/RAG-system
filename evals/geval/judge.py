"""
Phase 2 — G-Eval LLM-as-Judge.

Uses chain-of-thought + json_object response format for consistent, auditable scores.

Usage:
    cd evals
    python geval/judge.py

Exit code 1 if average score on any criterion falls below threshold (3.5 / 5.0).
"""

import json
import os
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Bootstrap Django to import RAGSystem directly.
# ---------------------------------------------------------------------------
BACKEND_DIR = Path(__file__).parent.parent.parent / "backend"
sys.path.insert(0, str(BACKEND_DIR))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")

import django
django.setup()

from openai import OpenAI  # noqa: E402
from chat.rag import get_rag_system  # noqa: E402
from .criteria import ALL_CRITERIA  # noqa: E402 — relative import for package use

GOLDEN_PATH = Path(__file__).parent.parent / "datasets" / "golden_qa.json"
RESULTS_DIR = Path(__file__).parent.parent / "results"
RESULTS_DIR.mkdir(exist_ok=True)

SCORE_THRESHOLD = 3.5  # out of 5.0

_client: OpenAI | None = None


def _get_client() -> OpenAI:
    global _client
    if _client is None:
        _client = OpenAI()
    return _client


def judge_answer(
    question: str,
    answer: str,
    context: str,
    criterion_name: str,
    criterion_description: str,
) -> dict:
    """
    Ask GPT-4o-mini to score one answer on one criterion.
    Returns {"score": int, "reasoning": str}.
    Chain-of-thought: model reasons first, then emits the JSON score.
    """
    system_prompt = (
        "You are an expert evaluator for AI-generated answers. "
        "You will be given a question, the document context used to answer it, "
        "and the answer produced by the AI. "
        "Evaluate the answer on the specified criterion. "
        "Think step-by-step before giving your final score. "
        "Respond ONLY with valid JSON: {\"reasoning\": \"<your reasoning>\", \"score\": <1-5>}."
    )

    user_prompt = f"""Criterion:
{criterion_description}

Question: {question}

Document context:
{context}

AI Answer: {answer}

Evaluate the answer on the criterion above. Respond with JSON only."""

    response = _get_client().chat.completions.create(
        model="gpt-4o-mini",
        temperature=0,
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
    )

    raw = response.choices[0].message.content or "{}"
    parsed = json.loads(raw)
    return {
        "score": int(parsed.get("score", 1)),
        "reasoning": parsed.get("reasoning", ""),
    }


def run() -> int:
    print("=== G-Eval LLM-as-Judge ===\n")

    golden = json.loads(GOLDEN_PATH.read_text(encoding="utf-8"))
    rag = get_rag_system()

    results = []
    criterion_totals: dict[str, list[int]] = {k: [] for k in ALL_CRITERIA}

    for item in golden:
        q = item["question"]
        print(f"Judging: {q[:60]}...")

        docs = rag.retriever.invoke(q)
        context_text = "\n\n".join(doc.page_content for doc in docs)
        answer, _ = rag.chat(q, [])

        item_scores: dict[str, dict] = {}
        for criterion_name, criterion_desc in ALL_CRITERIA.items():
            verdict = judge_answer(q, answer, context_text, criterion_name, criterion_desc)
            item_scores[criterion_name] = verdict
            criterion_totals[criterion_name].append(verdict["score"])

        results.append({"question": q, "answer": answer, "scores": item_scores})

    print("\n--- Criterion Averages ---")
    averages: dict[str, float] = {}
    failed = []
    for criterion, scores in criterion_totals.items():
        avg = sum(scores) / len(scores) if scores else 0.0
        averages[criterion] = avg
        status = "PASS" if avg >= SCORE_THRESHOLD else "FAIL"
        print(f"  {criterion:<15} avg={avg:.2f}/5.00  (threshold {SCORE_THRESHOLD})  [{status}]")
        if status == "FAIL":
            failed.append(criterion)

    out = {
        "threshold": SCORE_THRESHOLD,
        "averages": averages,
        "failed": failed,
        "details": results,
    }
    out_path = RESULTS_DIR / "geval_results.json"
    out_path.write_text(json.dumps(out, indent=2))
    print(f"\nResults saved to {out_path}")

    if failed:
        print(f"\n✗ {len(failed)} criterion(s) below threshold: {', '.join(failed)}")
        return 1

    print("\n✓ All G-Eval criteria passed.")
    return 0


if __name__ == "__main__":
    # Allow running as a script (not just as a package).
    # Re-import criteria without relative import.
    import importlib, types

    pkg = types.ModuleType("geval")
    pkg.__path__ = [str(Path(__file__).parent)]
    sys.modules["geval"] = pkg

    criteria_mod = importlib.import_module("geval.criteria")
    globals()["ALL_CRITERIA"] = criteria_mod.ALL_CRITERIA

    sys.exit(run())
