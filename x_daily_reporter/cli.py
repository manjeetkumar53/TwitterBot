from __future__ import annotations

import argparse
import json
from pathlib import Path

from x_daily_reporter.auth import BrowserLogin
from x_daily_reporter.crawlers import BrowserSearchCrawler, FileCrawler, XApiCrawler
from x_daily_reporter.models import Tweet
from x_daily_reporter.reporter import build_report, write_json, write_markdown


def main() -> int:
    parser = argparse.ArgumentParser(
        prog="twitterbot",
        description="X/Twitter login, crawler, sentiment analyzer, and daily reporter",
    )
    subcommands = parser.add_subparsers(dest="command", required=True)

    subcommands.add_parser("login", help="Open browser login for X/Twitter")

    crawl = subcommands.add_parser("crawl", help="Crawl tweets from API, browser, or file")
    crawl.add_argument("--query", required=True)
    crawl.add_argument("--limit", type=int, default=50)
    crawl.add_argument("--source", choices=["api", "browser", "file"], default="file")
    crawl.add_argument("--input", type=Path, default=Path("data/sample_tweets.json"))
    crawl.add_argument("--output", type=Path, default=Path("output/tweets.json"))
    crawl.add_argument("--headless", action="store_true")

    report = subcommands.add_parser("report", help="Build sentiment report from crawled tweets")
    report.add_argument("--query", required=True)
    report.add_argument("--input", type=Path, default=Path("output/tweets.json"))
    report.add_argument("--markdown", type=Path, default=Path("reports/daily-report.md"))
    report.add_argument("--json", type=Path, default=Path("reports/daily-report.json"))

    daily = subcommands.add_parser("daily", help="Crawl and report in one command")
    daily.add_argument("--query", required=True)
    daily.add_argument("--limit", type=int, default=50)
    daily.add_argument("--source", choices=["api", "browser", "file"], default="file")
    daily.add_argument("--input", type=Path, default=Path("data/sample_tweets.json"))
    daily.add_argument("--markdown", type=Path, default=Path("reports/daily-report.md"))
    daily.add_argument("--json", type=Path, default=Path("reports/daily-report.json"))
    daily.add_argument("--headless", action="store_true")

    args = parser.parse_args()
    if args.command == "login":
        BrowserLogin.from_env().open_login()
        return 0
    if args.command == "crawl":
        tweets = _crawl(args.source, args.query, args.limit, args.input, args.headless)
        _write_tweets(tweets, args.output)
        print(f"Wrote {len(tweets)} tweets to {args.output}")
        return 0
    if args.command == "report":
        tweets = _read_tweets(args.input)
        _write_report(args.query, tweets, args.markdown, args.json)
        return 0
    if args.command == "daily":
        tweets = _crawl(args.source, args.query, args.limit, args.input, args.headless)
        _write_report(args.query, tweets, args.markdown, args.json)
        return 0
    return 1


def _crawl(source: str, query: str, limit: int, input_path: Path, headless: bool) -> list[Tweet]:
    if source == "api":
        return XApiCrawler().crawl(query, limit)
    if source == "browser":
        return BrowserSearchCrawler(headless=headless).crawl(query, limit)
    return FileCrawler(input_path).crawl(query, limit)


def _read_tweets(path: Path) -> list[Tweet]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    return [Tweet.from_dict(item) for item in payload.get("tweets", payload)]


def _write_tweets(tweets: list[Tweet], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps({"tweets": [tweet.to_dict() for tweet in tweets]}, indent=2),
        encoding="utf-8",
    )


def _write_report(query: str, tweets: list[Tweet], markdown_path: Path, json_path: Path) -> None:
    report = build_report(query, tweets)
    write_markdown(report, markdown_path)
    write_json(report, json_path)
    print(f"Wrote Markdown report to {markdown_path}")
    print(f"Wrote JSON report to {json_path}")
