from __future__ import annotations

import argparse
import json
from pathlib import Path

from x_daily_reporter.auth import BrowserLogin
from x_daily_reporter.config import AppConfig, load_watchlist
from x_daily_reporter.models import Tweet
from x_daily_reporter.pipeline import DailyFeedPipeline
from x_daily_reporter.reporter import build_report, write_html, write_json, write_markdown
from x_daily_reporter.storage import SQLiteReportStore


def main() -> int:
    config = AppConfig.from_env()
    parser = argparse.ArgumentParser(
        prog="twitterbot",
        description="X/Twitter login, crawler, sentiment analyzer, and daily reporter",
    )
    subcommands = parser.add_subparsers(dest="command", required=True)

    subcommands.add_parser("login", help="Open browser login for X/Twitter")

    crawl = subcommands.add_parser("crawl", help="Crawl tweets from API, Xquik, browser, or file")
    crawl.add_argument("--query", required=True)
    crawl.add_argument("--limit", type=int, default=50)
    crawl.add_argument("--source", choices=["api", "xquik", "browser", "file"], default=config.source)
    crawl.add_argument("--input", type=Path, default=config.default_input)
    crawl.add_argument("--output", type=Path, default=Path("output/tweets.json"))
    crawl.add_argument("--headless", action="store_true")

    report = subcommands.add_parser("report", help="Build sentiment report from crawled tweets")
    report.add_argument("--query", required=True)
    report.add_argument("--input", type=Path, default=Path("output/tweets.json"))
    report.add_argument("--markdown", type=Path, default=config.reports_dir / "daily-report.md")
    report.add_argument("--json", type=Path, default=config.reports_dir / "daily-report.json")
    report.add_argument("--html", type=Path, default=config.reports_dir / "daily-report.html")
    report.add_argument("--db", type=Path, default=config.database_path)
    report.add_argument("--no-persist", action="store_true")

    daily = subcommands.add_parser("daily", help="Crawl and report in one command")
    daily.add_argument("--query", required=True)
    daily.add_argument("--limit", type=int, default=50)
    daily.add_argument("--source", choices=["api", "xquik", "browser", "file"], default=config.source)
    daily.add_argument("--input", type=Path, default=config.default_input)
    daily.add_argument("--markdown", type=Path, default=config.reports_dir / "daily-report.md")
    daily.add_argument("--json", type=Path, default=config.reports_dir / "daily-report.json")
    daily.add_argument("--html", type=Path, default=config.reports_dir / "daily-report.html")
    daily.add_argument("--db", type=Path, default=config.database_path)
    daily.add_argument("--no-persist", action="store_true")
    daily.add_argument("--headless", action="store_true")

    watchlist = subcommands.add_parser("watchlist", help="Run daily reports for every topic in a JSON watchlist")
    watchlist.add_argument("--config", type=Path, default=Path("config/watchlist.json"))
    watchlist.add_argument("--source", choices=["api", "xquik", "browser", "file"], default=config.source)
    watchlist.add_argument("--input", type=Path, default=config.default_input)
    watchlist.add_argument("--reports-dir", type=Path, default=config.reports_dir)
    watchlist.add_argument("--db", type=Path, default=config.database_path)
    watchlist.add_argument("--headless", action="store_true")

    history = subcommands.add_parser("history", help="Show recent persisted report runs")
    history.add_argument("--db", type=Path, default=config.database_path)
    history.add_argument("--limit", type=int, default=10)

    args = parser.parse_args()
    if args.command == "login":
        BrowserLogin.from_env().open_login()
        return 0
    if args.command == "crawl":
        tweets = DailyFeedPipeline().crawl(
            source=args.source,
            query=args.query,
            limit=args.limit,
            input_path=args.input,
            headless=args.headless,
        )
        _write_tweets(tweets, args.output)
        print(f"Wrote {len(tweets)} tweets to {args.output}")
        return 0
    if args.command == "report":
        tweets = _read_tweets(args.input)
        _write_report(args.query, tweets, args.markdown, args.json, args.html, args.db, not args.no_persist)
        return 0
    if args.command == "daily":
        result = DailyFeedPipeline(db_path=None if args.no_persist else args.db).run(
            source=args.source,
            query=args.query,
            limit=args.limit,
            input_path=args.input,
            markdown_path=args.markdown,
            json_path=args.json,
            html_path=args.html,
            headless=args.headless,
            persist=not args.no_persist,
        )
        _print_result(result.run_id, result.markdown_path, result.json_path, result.html_path)
        return 0
    if args.command == "watchlist":
        for topic in load_watchlist(args.config):
            slug = _slug(topic.name)
            result = DailyFeedPipeline(db_path=args.db).run(
                source=args.source,
                query=topic.query,
                limit=topic.limit,
                input_path=args.input,
                markdown_path=args.reports_dir / f"{slug}.md",
                json_path=args.reports_dir / f"{slug}.json",
                html_path=args.reports_dir / f"{slug}.html",
                headless=args.headless,
                persist=True,
            )
            _print_result(result.run_id, result.markdown_path, result.json_path, result.html_path)
        return 0
    if args.command == "history":
        for row in SQLiteReportStore(args.db).recent_runs(args.limit):
            print(
                f"{row['id']:>4} | {row['generated_at']} | {row['query']} | "
                f"total={row['total']} dominant={row['dominant_sentiment']} avg={row['average_sentiment']}"
            )
        return 0
    return 1


def _read_tweets(path: Path) -> list[Tweet]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    return [Tweet.from_dict(item) for item in payload.get("tweets", payload)]


def _write_tweets(tweets: list[Tweet], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps({"tweets": [tweet.to_dict() for tweet in tweets]}, indent=2),
        encoding="utf-8",
    )


def _write_report(
    query: str,
    tweets: list[Tweet],
    markdown_path: Path,
    json_path: Path,
    html_path: Path,
    db_path: Path,
    persist: bool,
) -> None:
    report = build_report(query, tweets)
    write_markdown(report, markdown_path)
    write_json(report, json_path)
    write_html(report, html_path)
    run_id = SQLiteReportStore(db_path).save(report) if persist else None
    _print_result(run_id, markdown_path, json_path, html_path)


def _print_result(run_id: int | None, markdown_path: Path, json_path: Path, html_path: Path | None) -> None:
    if run_id is not None:
        print(f"Persisted report run #{run_id}")
    print(f"Wrote Markdown report to {markdown_path}")
    print(f"Wrote JSON report to {json_path}")
    if html_path:
        print(f"Wrote HTML report to {html_path}")


def _slug(value: str) -> str:
    return "".join(char.lower() if char.isalnum() else "-" for char in value).strip("-")
