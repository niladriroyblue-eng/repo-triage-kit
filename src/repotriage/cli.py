from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Sequence

from .analyze import review_queue
from .github import GitHubError, fetch_open_items, validate_repo
from .models import WorkItem
from .render import render_json, render_markdown, report_data


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="repo-triage",
        description="Create a read-only triage snapshot from GitHub issue metadata.",
    )
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--repo", help="GitHub repository in owner/name format.")
    source.add_argument("--input", type=Path, help="Path to a GitHub issues JSON export or fixture.")
    parser.add_argument("--token", default=os.environ.get("GITHUB_TOKEN"), help="GitHub token (or set GITHUB_TOKEN).")
    parser.add_argument("--stale-days", type=int, default=30, help="Flag items with no updates for this many days (default: 30).")
    parser.add_argument("--first-response-days", type=int, default=7, help="Flag unanswered items after this many days (default: 7).")
    parser.add_argument("--format", choices=("markdown", "json"), default="markdown", help="Output format (default: markdown).")
    parser.add_argument("--output", type=Path, help="Write the report to a file instead of stdout.")
    parser.add_argument("--now", help="Override current time as ISO 8601 for repeatable reports.")
    return parser


def _read_fixture(path: Path) -> tuple[str, list[WorkItem]]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise GitHubError(f"Could not read input JSON: {error}") from error
    if isinstance(payload, list):
        raw_items = payload
        repo = "local/input"
    elif isinstance(payload, dict) and isinstance(payload.get("items"), list):
        raw_items = payload["items"]
        repo = str(payload.get("repository", "local/input"))
    else:
        raise GitHubError("Input JSON must be an array or an object with an 'items' array.")
    try:
        return repo, [WorkItem.from_github(record) for record in raw_items if isinstance(record, dict)]
    except (KeyError, TypeError, ValueError) as error:
        raise GitHubError(f"Input JSON contains a record missing required GitHub issue fields: {error}") from error


def _parse_now(value: str | None) -> datetime:
    if value is None:
        return datetime.now(timezone.utc)
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as error:
        raise GitHubError("--now must be an ISO 8601 date or timestamp.") from error
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def run(args: argparse.Namespace) -> int:
    if args.stale_days < 1 or args.first_response_days < 1:
        raise GitHubError("Triage thresholds must be positive integers.")
    if args.repo:
        validate_repo(args.repo)
        repo = args.repo
        items = fetch_open_items(repo, args.token)
    else:
        repo, items = _read_fixture(args.input)

    now = _parse_now(args.now)
    findings = review_queue(items, now, args.stale_days, args.first_response_days)
    if args.format == "json":
        output = render_json(report_data(repo, items, findings, now))
    else:
        output = render_markdown(repo, items, findings, now)

    if args.output:
        try:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(output, encoding="utf-8")
        except OSError as error:
            raise GitHubError(f"Could not write report: {error}") from error
    else:
        sys.stdout.write(output)
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return run(args)
    except GitHubError as error:
        parser.error(str(error))
    return 2
