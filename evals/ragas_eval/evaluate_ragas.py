"""
Phase 2 — RAGAS evaluation runner.

Imports RAGSystem directly (no HTTP) so it works with or without a running server.

Usage:
    python evals/run_all.py --ragas

NOTE: this directory is named `ragas_eval` (not `ragas`) on purpose —
otherwise `from ragas import evaluate` below would import this empty
package instead of the installed RAGAS library.

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
import httpx  # noqa: E402
from datasets import Dataset  # noqa: E402
from langchain_openai import ChatOpenAI, OpenAIEmbeddings  # noqa: E402
from ragas import evaluate  # noqa: E402
from ragas.llms import LangchainLLMWrapper  # noqa: E402
from ragas.embeddings import LangchainEmbeddingsWrapper  # noqa: E402
from ragas.metrics import (  # noqa: E402
    faithfulness,
    answer_relevancy,
    context_precision,
    context_recall,
)

# gpt-4o-mini pricing — used to compute judge-side cost from RAGAS token totals.
COST_PER_INPUT_TOKEN = 0.150 / 1_000_000   # $0.150 per 1M input tokens
COST_PER_OUTPUT_TOKEN = 0.600 / 1_000_000  # $0.600 per 1M output tokens


def _build_evaluator_clients() -> tuple[ChatOpenAI, OpenAIEmbeddings]:
    """Patient eval clients — separate from rag.llm/rag.embeddings, which are
    intentionally fast-fail (max_retries=0, short timeouts) for snappy chat UX.
    Eval is a batch job: it should retry on transient APIConnection/Timeout errors
    instead of dropping a row's score and forcing a re-spend on the next run."""
    proxy = os.environ.get("OPENAI_PROXY", "").strip()
    timeout = httpx.Timeout(connect=10.0, read=120.0, write=30.0, pool=10.0)
    http_kwargs = {
        "http_client": httpx.Client(proxy=proxy or None, timeout=timeout),
        "http_async_client": httpx.AsyncClient(proxy=proxy or None, timeout=timeout),
    }
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.0, max_retries=4,
                     timeout=120.0, **http_kwargs)
    emb = OpenAIEmbeddings(model="text-embedding-3-small", max_retries=4,
                           timeout=60.0, **http_kwargs)
    return llm, emb


def _safe_judge_cost_and_tokens(result) -> tuple[float, int]:
    """RAGAS exposes total_cost/total_tokens as methods (not attrs); both can
    raise. Try, and on any failure return (0, 0) — the run already succeeded."""
    judge_cost = 0.0
    judge_tokens = 0
    try:
        judge_cost = float(result.total_cost(
            cost_per_input_token=COST_PER_INPUT_TOKEN,
            cost_per_output_token=COST_PER_OUTPUT_TOKEN,
        ) or 0.0)
    except Exception as e:
        print(f"  [warn] Could not extract judge cost: {e}")
    try:
        usage = result.total_tokens()
        # total_tokens() can return a TokenUsage object or a list of them
        if isinstance(usage, list):
            judge_tokens = sum(int(getattr(u, "input_tokens", 0)) +
                               int(getattr(u, "output_tokens", 0)) for u in usage)
        elif usage is not None:
            judge_tokens = int(getattr(usage, "input_tokens", 0)) + \
                           int(getattr(usage, "output_tokens", 0))
    except Exception as e:
        print(f"  [warn] Could not extract judge token count: {e}")
    return judge_cost, judge_tokens

THRESHOLDS = {
    "faithfulness": 0.85,
    "answer_relevancy": 0.80,
    "context_precision": 0.75,
    "context_recall": 0.70,
}

GOLDEN_PATH = Path(__file__).parent.parent / "datasets" / "golden_qa.json"
RESULTS_DIR = Path(__file__).parent.parent / "results"
RESULTS_DIR.mkdir(exist_ok=True)


def build_ragas_dataset(rag, golden: list[dict]) -> tuple[Dataset, dict]:
    questions, answers, contexts, ground_truths = [], [], [], []
    cost_total = 0.0
    tokens_in_total = 0
    tokens_out_total = 0

    for item in golden:
        q = item["question"]
        gt = item["ground_truth"]

        docs = rag.retriever.invoke(q)
        ctx = [doc.page_content for doc in docs]
        answer, _, usage = rag.chat(q, [])

        cost_total += usage.get("cost_usd", 0.0)
        tokens_in_total += usage.get("tokens_in", 0)
        tokens_out_total += usage.get("tokens_out", 0)

        questions.append(q)
        answers.append(answer)
        contexts.append(ctx)
        ground_truths.append(gt)
        print(f"  ✓ {q[:60]}...")

    dataset = Dataset.from_dict(
        {
            "question": questions,
            "answer": answers,
            "contexts": contexts,
            "ground_truth": ground_truths,
        }
    )
    cost_summary = {
        "queries": len(golden),
        "tokens_in": tokens_in_total,
        "tokens_out": tokens_out_total,
        "cost_usd": round(cost_total, 6),
        "cost_per_query_usd": round(cost_total / len(golden), 6) if golden else 0.0,
    }
    return dataset, cost_summary


def run() -> int:
    print("=== RAGAS Evaluation ===\n")

    golden = json.loads(GOLDEN_PATH.read_text(encoding="utf-8"))
    print(f"Loaded {len(golden)} golden Q&A pairs.\n")

    rag = get_rag_system()
    print("Collecting answers from RAG system...")
    dataset, cost_summary = build_ragas_dataset(rag, golden)

    # Build PATIENT eval clients (retries=4, long timeouts). We deliberately do
    # NOT reuse rag.llm/rag.embeddings — those are configured for fast-fail in
    # chat (max_retries=0, ~30s) and cause RAGAS jobs to drop on every transient
    # APIConnectionError/TimeoutError, forcing you to re-pay on the next run.
    # Wrappers are required so RAGAS doesn't fall back to its own
    # `ragas.embeddings.openai_provider.OpenAIEmbeddings` (which lacks embed_query).
    eval_llm, eval_emb = _build_evaluator_clients()
    evaluator_llm = LangchainLLMWrapper(eval_llm)
    evaluator_embeddings = LangchainEmbeddingsWrapper(eval_emb)

    print("\nRunning RAGAS metrics (this calls OpenAI — ~1–2 min)...")
    result = evaluate(
        dataset,
        metrics=[faithfulness, answer_relevancy, context_precision, context_recall],
        llm=evaluator_llm,
        embeddings=evaluator_embeddings,
    )

    # In RAGAS 0.4.x `result[<metric>]` is a per-row list (one entry per question),
    # not a scalar. The stable public surface is `to_pandas()` — average each metric
    # column with `skipna=True` so a single failed job (e.g. transient APIConnectionError
    # on one row) doesn't poison the whole metric.
    df = result.to_pandas()
    scores: dict[str, float] = {}
    nan_counts: dict[str, int] = {}
    for metric in THRESHOLDS:
        if metric in df.columns:
            col = df[metric]
            nan_counts[metric] = int(col.isna().sum())
            mean = col.dropna().mean()
            scores[metric] = float(mean) if mean == mean else float("nan")  # NaN-safe
        else:
            scores[metric] = float("nan")
            nan_counts[metric] = len(df)

    print("\n--- Results ---")
    failed = []
    for metric, score in scores.items():
        threshold = THRESHOLDS[metric]
        if score != score:  # NaN
            status = "FAIL"
            print(f"  {metric:<25} (no valid scores — all rows failed)  [FAIL]")
            failed.append(metric)
        else:
            status = "PASS" if score >= threshold else "FAIL"
            n = nan_counts.get(metric, 0)
            note = f"  ({n} row(s) failed)" if n else ""
            print(f"  {metric:<25} {score:.3f}  (threshold {threshold})  [{status}]{note}")
            if status == "FAIL":
                failed.append(metric)

    # IMPORTANT: write the JSON BEFORE attempting any optional cost extraction.
    # If anything below this line raises, the scores from this (paid) run are
    # already on disk — we never lose a successful evaluation to a formatting bug.
    out_path = RESULTS_DIR / "ragas_results.json"
    json_scores = {k: (None if v != v else v) for k, v in scores.items()}  # NaN -> null

    def _save():
        out_path.write_text(json.dumps({
            "generated_at": __import__("datetime").datetime.now().isoformat(timespec="seconds"),
            "scores": json_scores,
            "thresholds": THRESHOLDS,
            "failed": failed,
            "nan_row_counts": nan_counts,
            "cost_summary": cost_summary,
        }, indent=2))

    _save()  # save what we have right now

    judge_cost, judge_tokens = _safe_judge_cost_and_tokens(result)
    cost_summary["judge_cost_usd"] = round(judge_cost, 6)
    cost_summary["judge_tokens"] = judge_tokens
    cost_summary["total_cost_usd"] = round(cost_summary["cost_usd"] + judge_cost, 6)

    print(f"\n  RAG cost:   ${cost_summary['cost_usd']:.4f}")
    print(f"  Judge cost: ${judge_cost:.4f}  ({judge_tokens} tokens)")
    print(f"  Total:      ${cost_summary['total_cost_usd']:.4f}")

    _save()  # re-save with cost data appended
    print(f"\nResults saved to {out_path}")

    if failed:
        print(f"\n✗ {len(failed)} metric(s) below threshold: {', '.join(failed)}")
        return 1

    print("\n✓ All metrics passed.")
    return 0


if __name__ == "__main__":
    sys.exit(run())
