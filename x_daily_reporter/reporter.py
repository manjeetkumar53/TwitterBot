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
        "average_sentiment": report.average_sentiment,
        "dominant_sentiment": report.dominant_sentiment,
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
        f"- Average sentiment: `{report.average_sentiment}`",
        f"- Dominant sentiment: `{report.dominant_sentiment}`",
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


def write_html(report: DailyReport, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    sentiment_by_id = {item.tweet_id: item for item in report.sentiments}
    rows = []
    for tweet in report.tweets:
        sentiment = sentiment_by_id[tweet.id]
        rows.append(
            "<tr>"
            f"<td><span class='badge {sentiment.label}'>{sentiment.label}</span></td>"
            f"<td>{sentiment.score:.2f}</td>"
            f"<td>{_escape(tweet.author)}</td>"
            f"<td>{_escape(tweet.text)}</td>"
            "</tr>"
        )

    html = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Daily X/Twitter Sentiment Report</title>
  <style>
    body {{ font-family: Arial, sans-serif; margin: 32px; color: #172033; }}
    .summary {{ display: grid; grid-template-columns: repeat(5, minmax(120px, 1fr)); gap: 12px; margin: 24px 0; }}
    .card {{ border: 1px solid #d7dde8; border-radius: 8px; padding: 14px; }}
    .label {{ color: #5b6678; font-size: 12px; text-transform: uppercase; }}
    .value {{ font-size: 24px; font-weight: 700; margin-top: 6px; }}
    table {{ width: 100%; border-collapse: collapse; margin-top: 18px; }}
    th, td {{ border-bottom: 1px solid #e5e9f0; padding: 10px; text-align: left; vertical-align: top; }}
    .badge {{ border-radius: 999px; padding: 4px 8px; font-size: 12px; font-weight: 700; }}
    .positive {{ background: #dcfce7; color: #166534; }}
    .neutral {{ background: #e5e7eb; color: #374151; }}
    .negative {{ background: #fee2e2; color: #991b1b; }}
  </style>
</head>
<body>
  <h1>Daily X/Twitter Sentiment Report</h1>
  <p><strong>Query:</strong> {_escape(report.query)}<br><strong>Generated:</strong> {report.generated_at.isoformat()}</p>
  <section class="summary">
    <div class="card"><div class="label">Tweets</div><div class="value">{report.total}</div></div>
    <div class="card"><div class="label">Positive</div><div class="value">{report.distribution.get("positive", 0)}</div></div>
    <div class="card"><div class="label">Neutral</div><div class="value">{report.distribution.get("neutral", 0)}</div></div>
    <div class="card"><div class="label">Negative</div><div class="value">{report.distribution.get("negative", 0)}</div></div>
    <div class="card"><div class="label">Avg Score</div><div class="value">{report.average_sentiment}</div></div>
  </section>
  <h2>Top Signals</h2>
  <p><strong>Terms:</strong> {_inline_pairs(report.top_terms)}</p>
  <p><strong>Hashtags:</strong> {_inline_pairs(report.top_hashtags)}</p>
  <p><strong>Mentions:</strong> {_inline_pairs(report.top_mentions)}</p>
  <h2>Tweet-Level Sentiment</h2>
  <table>
    <thead><tr><th>Sentiment</th><th>Score</th><th>Author</th><th>Tweet</th></tr></thead>
    <tbody>{''.join(rows)}</tbody>
  </table>
</body>
</html>
"""
    path.write_text(html, encoding="utf-8")


def _format_pairs(items: list[tuple[str, int]]) -> str:
    if not items:
        return "_No data._"
    return "\n".join(f"- `{term}`: {count}" for term, count in items)


def _inline_pairs(items: list[tuple[str, int]]) -> str:
    if not items:
        return "No data"
    return ", ".join(f"{_escape(term)} ({count})" for term, count in items)


def _escape(value: object) -> str:
    return (
        str(value)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )
