"""
Accuracy Report — PDF generator.

Reads evals/results/*.json (RAGAS + G-Eval) and produces a one-page-ish
"Accuracy Report.pdf" suitable for handing to a prospect or stakeholder.

Usage (from repo root):
    python evals/report.py
    python evals/report.py --out path/to/Report.pdf
"""

from __future__ import annotations

import argparse
import io
import json
from datetime import datetime
from pathlib import Path

import matplotlib
matplotlib.use("Agg")  # non-interactive — no display required
import matplotlib.pyplot as plt

from reportlab.lib import colors
from reportlab.lib.pagesizes import LETTER
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, PageBreak,
)

RESULTS_DIR = Path(__file__).parent / "results"
DEFAULT_OUT = RESULTS_DIR / "Accuracy_Report.pdf"


def _load(name: str) -> dict | None:
    path = RESULTS_DIR / name
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None


def _bar_chart(labels: list[str], values: list[float], thresholds: list[float] | None,
               title: str, ymax: float) -> Image:
    """Render a bar chart to PNG bytes and wrap in a reportlab Image."""
    fig, ax = plt.subplots(figsize=(6.5, 3.0), dpi=150)
    x = range(len(labels))
    bar_colors = [
        ("#2e7d32" if (thresholds is None or v >= thresholds[i]) else "#c62828")
        for i, v in enumerate(values)
    ]
    ax.bar(x, values, color=bar_colors, edgecolor="#333", linewidth=0.5)
    if thresholds:
        for i, t in enumerate(thresholds):
            ax.hlines(t, i - 0.4, i + 0.4, colors="#555", linestyles="--", linewidth=1)
    ax.set_xticks(list(x))
    ax.set_xticklabels(labels, rotation=20, ha="right", fontsize=9)
    ax.set_ylim(0, ymax)
    ax.set_title(title, fontsize=11)
    ax.grid(axis="y", linestyle=":", alpha=0.4)
    for i, v in enumerate(values):
        ax.text(i, v + ymax * 0.02, f"{v:.2f}", ha="center", fontsize=8)

    buf = io.BytesIO()
    fig.tight_layout()
    fig.savefig(buf, format="png", bbox_inches="tight")
    plt.close(fig)
    buf.seek(0)
    return Image(buf, width=6.5 * inch, height=3.0 * inch)


def _section(text: str, styles) -> Paragraph:
    return Paragraph(text, styles["section"])


def _kv_table(rows: list[tuple[str, str]]) -> Table:
    t = Table(rows, colWidths=[2.0 * inch, 4.5 * inch])
    t.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("TEXTCOLOR", (0, 0), (-1, -1), colors.HexColor("#222")),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("LINEBELOW", (0, 0), (-1, -1), 0.25, colors.HexColor("#ddd")),
    ]))
    return t


def build(out_path: Path) -> int:
    ragas = _load("ragas_results.json")
    geval = _load("geval_results.json")

    if not ragas and not geval:
        print("No eval results found in evals/results/. Run RAGAS or G-Eval first.")
        return 1

    out_path.parent.mkdir(parents=True, exist_ok=True)
    doc = SimpleDocTemplate(
        str(out_path), pagesize=LETTER,
        leftMargin=0.7 * inch, rightMargin=0.7 * inch,
        topMargin=0.7 * inch, bottomMargin=0.6 * inch,
        title="Accuracy Report",
    )

    base = getSampleStyleSheet()
    styles = {
        "title": ParagraphStyle("title", parent=base["Title"], fontSize=20,
                                textColor=colors.HexColor("#111"), spaceAfter=4),
        "subtitle": ParagraphStyle("subtitle", parent=base["Normal"], fontSize=10,
                                   textColor=colors.HexColor("#666"), spaceAfter=14),
        "section": ParagraphStyle("section", parent=base["Heading2"], fontSize=13,
                                  textColor=colors.HexColor("#222"),
                                  spaceBefore=12, spaceAfter=6),
        "body": ParagraphStyle("body", parent=base["Normal"], fontSize=10,
                               textColor=colors.HexColor("#222"), spaceAfter=4),
        "fail_q": ParagraphStyle("fail_q", parent=base["Normal"], fontSize=9,
                                 textColor=colors.HexColor("#222"),
                                 leftIndent=10, spaceAfter=2),
        "fail_r": ParagraphStyle("fail_r", parent=base["Normal"], fontSize=8,
                                 textColor=colors.HexColor("#666"),
                                 leftIndent=20, spaceAfter=8),
    }

    story = []
    story.append(Paragraph("DocuChat — Accuracy Report", styles["title"]))
    story.append(Paragraph(
        f"Generated {datetime.now().strftime('%Y-%m-%d %H:%M')} &nbsp;·&nbsp; "
        "RAGAS + G-Eval results from evals/results/",
        styles["subtitle"],
    ))

    # ---------------- Summary block ----------------
    story.append(_section("Summary", styles))
    summary_rows: list[tuple[str, str]] = []
    overall_status = "PASS"
    if ragas:
        ragas_failed = ragas.get("failed", [])
        summary_rows.append(("RAGAS metrics",
                             "all passed" if not ragas_failed
                             else f"{len(ragas_failed)} below threshold ({', '.join(ragas_failed)})"))
        if ragas_failed:
            overall_status = "FAIL"
    if geval:
        geval_failed = geval.get("failed", [])
        summary_rows.append(("G-Eval criteria",
                             "all passed" if not geval_failed
                             else f"{len(geval_failed)} below threshold ({', '.join(geval_failed)})"))
        if geval_failed:
            overall_status = "FAIL"

    total_cost = 0.0
    total_queries = 0
    for src in (ragas, geval):
        if src and isinstance(src.get("cost_summary"), dict):
            total_cost += src["cost_summary"].get("cost_usd", 0.0)
            total_queries = max(total_queries, src["cost_summary"].get("queries", 0))

    if total_queries:
        summary_rows.append(("RAG cost", f"${total_cost:.4f} over {total_queries} queries "
                                          f"(${total_cost / total_queries:.6f}/query)"))
    summary_rows.append(("Overall", overall_status))
    story.append(_kv_table(summary_rows))

    # ---------------- RAGAS section ----------------
    if ragas:
        story.append(_section("RAGAS — Retrieval-Augmented Generation Assessment", styles))
        scores = ragas.get("scores", {})
        thresholds = ragas.get("thresholds", {})
        # Drop metrics with no valid score (None / missing) — they'd break matplotlib
        # and clutter the chart. Mention them separately below.
        plottable = [(k, v) for k, v in scores.items() if isinstance(v, (int, float))]
        missing = [k for k, v in scores.items() if not isinstance(v, (int, float))]
        if plottable:
            labels = [k for k, _ in plottable]
            values = [v for _, v in plottable]
            thr = [thresholds.get(k, 0.0) for k in labels]
            story.append(_bar_chart(labels, values, thr,
                                    "RAGAS scores vs. thresholds (dashed)", ymax=1.05))
        if missing:
            story.append(Paragraph(
                f"<i>Metrics with no valid scores (all rows failed): {', '.join(missing)}</i>",
                styles["body"],
            ))

    # ---------------- G-Eval section ----------------
    if geval:
        story.append(_section("G-Eval — LLM-as-Judge", styles))
        averages = geval.get("averages", {})
        threshold = geval.get("threshold", 3.5)
        labels = list(averages.keys())
        values = [averages[k] for k in labels]
        story.append(_bar_chart(labels, values, [threshold] * len(labels),
                                f"G-Eval averages (threshold {threshold}/5)", ymax=5.2))

        # Failed questions with reasoning
        details = geval.get("details", [])
        failures: list[tuple[str, str, str, int]] = []
        for d in details:
            for crit, verdict in (d.get("scores") or {}).items():
                if verdict.get("score", 5) < threshold:
                    failures.append((d.get("question", ""), crit,
                                     verdict.get("reasoning", ""), verdict.get("score", 0)))

        if failures:
            story.append(PageBreak())
            story.append(_section(f"Failed answers ({len(failures)})", styles))
            for q, crit, reasoning, score in failures[:20]:
                story.append(Paragraph(
                    f"<b>{crit}</b> — score {score}/5 &nbsp;·&nbsp; <i>{_escape(q)}</i>",
                    styles["fail_q"],
                ))
                story.append(Paragraph(_escape(reasoning), styles["fail_r"]))
            if len(failures) > 20:
                story.append(Paragraph(
                    f"… plus {len(failures) - 20} more failures (truncated).", styles["body"]))

    story.append(Spacer(1, 0.3 * inch))
    story.append(Paragraph(
        "Methodology: RAGAS computes faithfulness, answer relevancy, context precision/recall "
        "against a curated golden set. G-Eval uses GPT-4o-mini as a judge across multiple "
        "criteria (1–5 scale). Costs are RAG generation only; judge calls are not billed to the user.",
        ParagraphStyle("foot", parent=base["Italic"], fontSize=8,
                       textColor=colors.HexColor("#888")),
    ))

    doc.build(story)
    print(f"Wrote {out_path}")
    return 0


def _escape(s: str) -> str:
    return (s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))[:1000]


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate Accuracy Report PDF from eval results")
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT,
                        help=f"Output PDF path (default: {DEFAULT_OUT})")
    args = parser.parse_args()
    return build(args.out)


if __name__ == "__main__":
    raise SystemExit(main())
