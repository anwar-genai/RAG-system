"""
Export thumbs-up/down feedback into evals/datasets/feedback_candidates.json.

Up-voted answers become candidates for the golden set (positive examples).
Down-voted answers become candidates for the adversarial set (failure examples).

This command never modifies golden_qa.json directly — it produces a review file
so a human can decide what to fold in.

Usage:
    python manage.py fold_feedback
    python manage.py fold_feedback --out path/to/file.json
"""

import json
from datetime import datetime
from pathlib import Path

from django.core.management.base import BaseCommand

from chat.models import Message


DEFAULT_OUT = Path(__file__).resolve().parents[4] / "evals" / "datasets" / "feedback_candidates.json"


class Command(BaseCommand):
    help = "Export thumbs-up/down feedback to a candidates JSON for golden-set review."

    def add_arguments(self, parser):
        parser.add_argument(
            "--out",
            type=Path,
            default=DEFAULT_OUT,
            help=f"Output JSON path (default: {DEFAULT_OUT})",
        )

    def handle(self, *args, **opts):
        out_path: Path = opts["out"]

        positive: list[dict] = []
        negative: list[dict] = []

        rated = Message.objects.filter(
            message_type="assistant",
        ).exclude(feedback=0).select_related("session").order_by("created_at")

        for ai_msg in rated:
            # Find the user message immediately preceding this one in the same session.
            user_msg = (
                Message.objects.filter(
                    session=ai_msg.session,
                    message_type="user",
                    created_at__lt=ai_msg.created_at,
                )
                .order_by("-created_at")
                .first()
            )
            if not user_msg:
                continue  # orphan assistant message — skip

            entry = {
                "question": user_msg.content,
                "answer": ai_msg.content,
                "sources": ai_msg.sources or [],
                "message_id": ai_msg.id,
                "session_id": str(ai_msg.session.session_id),
                "created_at": ai_msg.created_at.isoformat(timespec="seconds"),
            }
            (positive if ai_msg.feedback == 1 else negative).append(entry)

        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps(
            {
                "exported_at": datetime.now().isoformat(timespec="seconds"),
                "positive": positive,
                "negative": negative,
            },
            indent=2,
        ), encoding="utf-8")

        self.stdout.write(self.style.SUCCESS(
            f"Exported {len(positive)} positive + {len(negative)} negative candidates to {out_path}"
        ))
