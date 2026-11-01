from __future__ import annotations

import json
from datetime import datetime
from typing import Any

from .analyze import Finding
from .models import WorkItem


def _markdown_cell(value: str) -> str:
    value = value.replace("\\", "\\\\").replace("\n", " ").replace("\r", " ")
    for character in ("|", "*", "_", "[", "]", "(", ")", "<", ">", "`"):
        value = value.replace(character, "\\" + character)
    return value


def report_data(repo: str, items: list[WorkItem], findings: list[Finding], now: datetime) -> dict[str, Any]:
    return {
        "repository": repo,
        "generated_at": now.isoformat(),
        "summary": {
            "open_items_scanned": len(items),
            "needs_attention": len(findings),
            "issues_scanned": sum(item.kind == "issue" for item in items),
            "pull_requests_scanned": sum(item.kind == "pull request" for item in items),
        },
        "findings": [
            {
                "number": finding.item.number,
                "kind": finding.item.kind,
                "title": finding.item.title,
                "url": finding.item.url,
                "labels": list(finding.item.labels),
                "age_days": finding.age_days,
                "days_since_update": finding.days_since_update,
                "priority": finding.priority,
                "reasons": list(finding.reasons),
            }
            for finding in findings
        ],
    }


def render_json(data: dict[str, Any]) -> str:
    return json.dumps(data, indent=2, ensure_ascii=False) + "\n"


def render_markdown(repo: str, items: list[WorkItem], findings: list[Finding], now: datetime) -> str:
    issues = sum(item.kind == "issue" for item in items)
    pull_requests = len(items) - issues
    lines = [
        f"# Triage snapshot: `{repo}`",
        "",
        f"Generated {now.strftime('%Y-%m-%d %H:%M UTC')} · read-only report",
        "",
        "| Open items scanned | Issues | Pull requests | Need attention |",
        "| ---: | ---: | ---: | ---: |",
        f"| {len(items)} | {issues} | {pull_requests} | {len(findings)} |",
        "",
    ]
    if not findings:
        lines.extend(["No items crossed the configured triage thresholds.", ""])
        return "\n".join(lines)

    lines.extend(
        [
            "## Suggested review queue",
            "",
            "These are metadata signals for human review. The tool does not label, close, assign, or comment on issues.",
            "",
            "| Priority | Type | Item | Title | Updated | Signals |",
            "| --- | --- | ---: | --- | ---: | --- |",
        ]
    )
    for finding in findings:
        title = _markdown_cell(finding.item.title)
        item_link = f"[#{finding.item.number}]({finding.item.url})" if finding.item.url else f"#{finding.item.number}"
        signals = ", ".join(finding.reasons)
        priority = "High" if finding.priority >= 4 else "Review" if finding.priority >= 2 else "Low"
        lines.append(
            f"| {priority} | {finding.item.kind.title()} | {item_link} | {title} | "
            f"{finding.days_since_update}d ago | {signals} |"
        )
    lines.append("")
    return "\n".join(lines)
