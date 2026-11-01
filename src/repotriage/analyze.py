from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from .models import WorkItem


@dataclass(frozen=True)
class Finding:
    item: WorkItem
    reasons: tuple[str, ...]
    priority: int
    age_days: int
    days_since_update: int


def review_queue(
    items: list[WorkItem],
    now: datetime,
    stale_days: int = 30,
    first_response_days: int = 7,
) -> list[Finding]:
    findings: list[Finding] = []
    for item in items:
        age_days = max(0, (now - item.created_at).days)
        days_since_update = max(0, (now - item.updated_at).days)
        reasons: list[str] = []
        priority = 0

        if item.comments == 0 and age_days >= first_response_days:
            reasons.append("no response yet")
            priority += 4
        if not item.labels and age_days >= first_response_days:
            reasons.append("needs labels")
            priority += 2
        if days_since_update >= stale_days:
            reasons.append("stale activity")
            priority += 1

        if reasons:
            findings.append(
                Finding(
                    item=item,
                    reasons=tuple(reasons),
                    priority=priority,
                    age_days=age_days,
                    days_since_update=days_since_update,
                )
            )

    return sorted(
        findings,
        key=lambda finding: (
            -finding.priority,
            -finding.days_since_update,
            finding.item.number,
        ),
    )
