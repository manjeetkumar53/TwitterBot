from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


@dataclass(frozen=True)
class Tweet:
    id: str
    text: str
    author: str = "unknown"
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    url: str | None = None
    metrics: dict[str, int] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "Tweet":
        created_at = payload.get("created_at")
        if isinstance(created_at, str):
            created_at = _parse_datetime(created_at)
        if created_at is None:
            created_at = datetime.now(timezone.utc)
        return cls(
            id=str(payload.get("id") or payload.get("tweet_id") or ""),
            text=str(payload.get("text") or ""),
            author=str(payload.get("author") or payload.get("username") or "unknown"),
            created_at=created_at,
            url=payload.get("url"),
            metrics={str(k): int(v) for k, v in dict(payload.get("metrics") or {}).items()},
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "text": self.text,
            "author": self.author,
            "created_at": self.created_at.isoformat(),
            "url": self.url,
            "metrics": self.metrics,
        }


@dataclass(frozen=True)
class SentimentResult:
    tweet_id: str
    label: str
    score: float
    positive_terms: list[str]
    negative_terms: list[str]


@dataclass(frozen=True)
class DailyReport:
    generated_at: datetime
    query: str
    tweets: list[Tweet]
    sentiments: list[SentimentResult]
    top_terms: list[tuple[str, int]]
    top_hashtags: list[tuple[str, int]]
    top_mentions: list[tuple[str, int]]

    @property
    def total(self) -> int:
        return len(self.tweets)

    @property
    def distribution(self) -> dict[str, int]:
        counts = {"positive": 0, "neutral": 0, "negative": 0}
        for result in self.sentiments:
            counts[result.label] = counts.get(result.label, 0) + 1
        return counts


def _parse_datetime(value: str) -> datetime:
    normalized = value.replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError:
        return datetime.now(timezone.utc)
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed
