from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from x_daily_reporter.models import DailyReport


class SQLiteReportStore:
    def __init__(self, path: Path) -> None:
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS report_runs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    query TEXT NOT NULL,
                    generated_at TEXT NOT NULL,
                    total INTEGER NOT NULL,
                    positive INTEGER NOT NULL,
                    neutral INTEGER NOT NULL,
                    negative INTEGER NOT NULL,
                    average_sentiment REAL NOT NULL,
                    dominant_sentiment TEXT NOT NULL,
                    top_terms_json TEXT NOT NULL,
                    top_hashtags_json TEXT NOT NULL,
                    top_mentions_json TEXT NOT NULL
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS report_tweets (
                    run_id INTEGER NOT NULL,
                    tweet_id TEXT NOT NULL,
                    author TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    text TEXT NOT NULL,
                    url TEXT,
                    metrics_json TEXT NOT NULL,
                    sentiment TEXT NOT NULL,
                    sentiment_score REAL NOT NULL,
                    FOREIGN KEY (run_id) REFERENCES report_runs(id)
                )
                """
            )

    def save(self, report: DailyReport) -> int:
        distribution = report.distribution
        sentiment_by_id = {item.tweet_id: item for item in report.sentiments}
        with self._connect() as conn:
            cursor = conn.execute(
                """
                INSERT INTO report_runs (
                    query,
                    generated_at,
                    total,
                    positive,
                    neutral,
                    negative,
                    average_sentiment,
                    dominant_sentiment,
                    top_terms_json,
                    top_hashtags_json,
                    top_mentions_json
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    report.query,
                    report.generated_at.isoformat(),
                    report.total,
                    distribution.get("positive", 0),
                    distribution.get("neutral", 0),
                    distribution.get("negative", 0),
                    report.average_sentiment,
                    report.dominant_sentiment,
                    json.dumps(report.top_terms),
                    json.dumps(report.top_hashtags),
                    json.dumps(report.top_mentions),
                ),
            )
            run_id = int(cursor.lastrowid)
            conn.executemany(
                """
                INSERT INTO report_tweets (
                    run_id,
                    tweet_id,
                    author,
                    created_at,
                    text,
                    url,
                    metrics_json,
                    sentiment,
                    sentiment_score
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                [
                    (
                        run_id,
                        tweet.id,
                        tweet.author,
                        tweet.created_at.isoformat(),
                        tweet.text,
                        tweet.url,
                        json.dumps(tweet.metrics),
                        sentiment_by_id[tweet.id].label,
                        sentiment_by_id[tweet.id].score,
                    )
                    for tweet in report.tweets
                ],
            )
        return run_id

    def recent_runs(self, limit: int = 10) -> list[dict]:
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT id, query, generated_at, total, positive, neutral, negative,
                       average_sentiment, dominant_sentiment
                FROM report_runs
                ORDER BY id DESC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()
        return [dict(row) for row in rows]
