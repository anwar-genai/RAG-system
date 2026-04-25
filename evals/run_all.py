"""
Phase 2 — Master eval runner.

Runs RAGAS and G-Eval in sequence. Exits with code 1 if either suite fails.
Promptfoo is HTTP-based (needs a live server + JWT) so it is run separately:
    npx promptfoo eval --config evals/promptfoo/promptfooconfig.yaml

Usage (from repo root):
    python evals/run_all.py              # RAGAS + G-Eval
    python evals/run_all.py --ragas      # RAGAS only
    python evals/run_all.py --geval      # G-Eval only
"""

import argparse
import importlib
import json
import sys
import types
from pathlib import Path

# Force UTF-8 stdout/stderr so emoji/unicode in eval output (✓, ✗, em-dash, etc.)
# don't blow up Windows consoles in legacy cp1252.
for _stream in (sys.stdout, sys.stderr):
    if hasattr(_stream, "reconfigure"):
        try:
            _stream.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass

# Make sibling packages importable when run as a script from repo root.
EVALS_DIR = Path(__file__).parent
sys.path.insert(0, str(EVALS_DIR))

# Register the geval package so relative imports inside judge.py work.
geval_pkg = types.ModuleType("geval")
geval_pkg.__path__ = [str(EVALS_DIR / "geval")]
sys.modules.setdefault("geval", geval_pkg)

RESULTS_DIR = EVALS_DIR / "results"
RESULTS_DIR.mkdir(exist_ok=True)


def _print_header(title: str) -> None:
    print("\n" + "=" * 60)
    print(f"  {title}")
    print("=" * 60)


def run_ragas() -> int:
    _print_header("RAGAS — Retrieval-Augmented Generation Assessment")
    # NB: local package is `ragas_eval` (not `ragas`) to avoid shadowing the
    # installed RAGAS PyPI package — `from ragas import evaluate` inside the
    # runner needs to resolve to the library, not this directory.
    import ragas_eval.evaluate_ragas as ragas_runner
    return ragas_runner.run()


def run_geval() -> int:
    _print_header("G-Eval — LLM-as-Judge")
    # Patch ALL_CRITERIA before importing judge (avoids relative-import issues).
    criteria_mod = importlib.import_module("geval.criteria")
    import geval.judge as judge_mod
    judge_mod.ALL_CRITERIA = criteria_mod.ALL_CRITERIA
    return judge_mod.run()


def summarize_results() -> None:
    _print_header("Summary")
    for result_file in sorted(RESULTS_DIR.glob("*.json")):
        print(f"\n[{result_file.name}]")
        try:
            data = json.loads(result_file.read_text())
            failed = data.get("failed", [])
            if failed:
                print(f"  FAILED metrics/criteria: {', '.join(failed)}")
            else:
                print("  All checks passed.")
        except Exception as e:
            print(f"  Could not read: {e}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Run RAG eval suite")
    parser.add_argument("--ragas", action="store_true", help="Run RAGAS only")
    parser.add_argument("--geval", action="store_true", help="Run G-Eval only")
    args = parser.parse_args()

    run_both = not args.ragas and not args.geval

    exit_codes = []

    if args.ragas or run_both:
        exit_codes.append(run_ragas())

    if args.geval or run_both:
        exit_codes.append(run_geval())

    summarize_results()

    overall = 1 if any(c != 0 for c in exit_codes) else 0
    print(f"\n{'✓ All suites passed.' if overall == 0 else '✗ One or more suites failed.'}\n")
    return overall


if __name__ == "__main__":
    sys.exit(main())
