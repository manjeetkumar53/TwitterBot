from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from x_daily_reporter.analyzer import SentimentAnalyzer, top_hashtags, top_mentions, top_terms
from x_daily_reporter.models import DailyReport, Tweet


def build_report(query: str, tweets: list[Tweet]) -> DailyReport:
    analyzer = SentimentAnalyzer()
    return DailyReport(
        generated_at=datetime.now(timezone.utc),
        query=query,
        tweets=tweets,
        sentiments=analyzer.analyze_many(tweets),
        top_terms=top_terms(tweets),
        top_hashtags=top_hashtags(tweets),
        top_mentions=top_mentions(tweets),
    )


def write_json(report: DailyReport, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    sentiment_by_id = {item.tweet_id: item for item in report.sentiments}
    payload = {
        "generated_at": report.generated_at.isoformat(),
        "query": report.query,
        "total": report.total,
        "distribution": report.distribution,
        "top_terms": report.top_terms,
        "top_hashtags": report.top_hashtags,
        "top_mentions": report.top_mentions,
        "tweets": [
            {
                **tweet.to_dict(),
                "sentiment": sentiment_by_id[tweet.id].label,
                "sentiment_score": sentiment_by_id[tweet.id].score,
            }
            for tweet in report.tweets
        ],
    }
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def write_markdown(report: DailyReport, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        f"# Daily X/Twitter Sentiment Report: {report.query}",
        "",
        f"- Generated at: `{report.generated_at.isoformat()}`",
        f"- Tweets analyzed: `{report.total}`",
        f"- Positive: `{report.distribution.get('positive', 0)}`",
        f"- Neutral: `{report.distribution.get('neutral', 0)}`",
        f"- Negative: `{report.distribution.get('negative', 0)}`",
        "",
        "## Top Terms",
        "",
        _format_pairs(report.top_terms),
        "",
        "## Top Hashtags",
        "",
        _format_pairs(report.top_hashtags),
        "",
        "## Top Mentions",
        "",
        _format_pairs(report.top_mentions),
        "",
        "## Tweet-Level Sentiment",
        "",
        "| Sentiment | Score | Author | Tweet |",
        "|---|---:|---|---|",
    ]
    sentiment_by_id = {item.tweet_id: item for item in report.sentiments}
    for tweet in report.tweets:
        sentiment = sentiment_by_id[tweet.id]
        text = " ".join(tweet.text.split()).replace("|", "\\|")
        if len(text) > 180:
            text = text[:177] + "..."
        author = tweet.author.replace("|", "\\|")
        lines.append(f"| {sentiment.label} | {sentiment.score:.2f} | {author} | {text} |")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _format_pairs(items: list[tuple[str, int]]) -> str:
    if not items:
        return "_No data._"
    return "\n".join(f"- `{term}`: {count}" for term, count in items)
