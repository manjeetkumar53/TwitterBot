from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class WatchTopic:
    name: str
    query: str
    limit: int = 50


@dataclass(frozen=True)
class AppConfig:
    source: str = "file"
    database_path: Path = Path("data/twitterbot.sqlite3")
    reports_dir: Path = Path("reports")
    default_input: Path = Path("data/sample_tweets.json")

    @classmethod
    def from_env(cls) -> "AppConfig":
        return cls(
            source=os.getenv("TWITTERBOT_SOURCE", "file"),
            database_path=Path(os.getenv("TWITTERBOT_DB", "data/twitterbot.sqlite3")),
            reports_dir=Path(os.getenv("TWITTERBOT_REPORTS_DIR", "reports")),
            default_input=Path(os.getenv("TWITTERBOT_INPUT", "data/sample_tweets.json")),
        )


def load_watchlist(path: Path) -> list[WatchTopic]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    topics = payload.get("topics", payload)
    return [
        WatchTopic(
            name=str(item["name"]),
            query=str(item["query"]),
            limit=int(item.get("limit", 50)),
        )
        for item in topics
    ]
