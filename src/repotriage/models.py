from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from typing import Any


def parse_timestamp(value: str) -> datetime:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


@dataclass(frozen=True)
class WorkItem:
    number: int
    title: str
    url: str
    kind: str
    created_at: datetime
    updated_at: datetime
    comments: int
    labels: tuple[str, ...]
    draft: bool = False

    @classmethod
    def from_github(cls, raw: dict[str, Any]) -> "WorkItem":
        pull_request = raw.get("pull_request") is not None
        labels = tuple(
            str(label.get("name", ""))
            for label in raw.get("labels", [])
            if isinstance(label, dict) and label.get("name")
        )
        return cls(
            number=int(raw["number"]),
            title=str(raw.get("title", "(untitled)")),
            url=str(raw.get("html_url", "")),
            kind="pull request" if pull_request else "issue",
            created_at=parse_timestamp(str(raw["created_at"])),
            updated_at=parse_timestamp(str(raw["updated_at"])),
            comments=int(raw.get("comments", 0)),
            labels=labels,
            draft=bool(raw.get("draft", False)),
        )

    def to_dict(self, now: datetime) -> dict[str, Any]:
        data = asdict(self)
        data["created_at"] = self.created_at.isoformat()
        data["updated_at"] = self.updated_at.isoformat()
        data["labels"] = list(self.labels)
        data["age_days"] = max(0, (now - self.created_at).days)
        data["days_since_update"] = max(0, (now - self.updated_at).days)
        return data
