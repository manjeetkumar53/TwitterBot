from __future__ import annotations

import json
import os
import re
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Protocol

from x_daily_reporter.models import Tweet


class TweetCrawler(Protocol):
    def crawl(self, query: str, limit: int) -> list[Tweet]:
        ...


class FileCrawler:
    def __init__(self, path: Path) -> None:
        self.path = path

    def crawl(self, query: str, limit: int) -> list[Tweet]:
        payload = json.loads(self.path.read_text(encoding="utf-8"))
        tweets = [Tweet.from_dict(item) for item in payload.get("tweets", payload)]
        if query:
            terms = _offline_query_terms(query)
            if terms:
                tweets = [
                    tweet
                    for tweet in tweets
                    if any(term in tweet.text.lower() for term in terms)
                ]
        return tweets[:limit]


class XApiCrawler:
    """Official X API v2 recent-search crawler.

    Requires X_BEARER_TOKEN. This is the most stable and compliant crawl path.
    """

    def __init__(self, bearer_token: str | None = None) -> None:
        self.bearer_token = bearer_token or os.getenv("X_BEARER_TOKEN")
        if not self.bearer_token:
            raise ValueError("X_BEARER_TOKEN is required for API crawling")

    def crawl(self, query: str, limit: int) -> list[Tweet]:
        params = {
            "query": query,
            "max_results": str(max(10, min(limit, 100))),
            "tweet.fields": "created_at,public_metrics,author_id",
            "expansions": "author_id",
            "user.fields": "username",
        }
        url = "https://api.twitter.com/2/tweets/search/recent?" + urllib.parse.urlencode(params)
        request = urllib.request.Request(url, headers={"Authorization": f"Bearer {self.bearer_token}"})
        with urllib.request.urlopen(request, timeout=30) as response:
            payload = json.loads(response.read().decode("utf-8"))

        users = {
            item["id"]: item.get("username", "unknown")
            for item in payload.get("includes", {}).get("users", [])
        }
        tweets: list[Tweet] = []
        for item in payload.get("data", []):
            author = users.get(item.get("author_id"), item.get("author_id", "unknown"))
            metrics = {
                key: int(value)
                for key, value in dict(item.get("public_metrics") or {}).items()
                if isinstance(value, int)
            }
            tweets.append(
                Tweet(
                    id=item["id"],
                    text=item.get("text", ""),
                    author=author,
                    created_at=_parse_time(item.get("created_at")),
                    url=f"https://x.com/{author}/status/{item['id']}",
                    metrics=metrics,
                )
            )
        return tweets[:limit]


class XquikCrawler:
    """Xquik recent-search crawler.

    Requires XQUIK_API_KEY. This keeps the same Tweet model used by the
    existing reporter pipeline while avoiding browser automation.
    """

    def __init__(self, api_key: str | None = None) -> None:
        self.api_key = api_key or os.getenv("XQUIK_API_KEY")
        if not self.api_key:
            raise ValueError("XQUIK_API_KEY is required for Xquik crawling")

    def crawl(self, query: str, limit: int) -> list[Tweet]:
        params = {
            "q": query,
            "queryType": "Latest",
            "limit": str(max(1, min(limit, 200))),
        }
        url = "https://xquik.com/api/v1/x/tweets/search?" + urllib.parse.urlencode(params)
        request = urllib.request.Request(
            url,
            headers={"accept": "application/json", "x-api-key": self.api_key},
        )
        with urllib.request.urlopen(request, timeout=30) as response:
            payload = json.loads(response.read().decode("utf-8"))

        tweets: list[Tweet] = []
        for item in payload.get("tweets", []):
            tweet_id = str(item.get("id") or "")
            text = str(item.get("text") or "")
            author_payload = item.get("author") or {}
            author = (
                str(author_payload.get("username") or "unknown")
                if isinstance(author_payload, dict)
                else "unknown"
            )
            metrics = _xquik_metrics(item)
            tweets.append(
                Tweet(
                    id=tweet_id,
                    text=text,
                    author=author,
                    created_at=_parse_time(item.get("createdAt")),
                    url=f"https://x.com/{author}/status/{tweet_id}" if tweet_id and author != "unknown" else None,
                    metrics=metrics,
                )
            )
        return tweets[:limit]


class BrowserSearchCrawler:
    """Playwright browser fallback for manually authenticated X/Twitter sessions.

    Browser automation is intentionally conservative: it opens search pages and
    reads visible tweet cards. Prefer the official API for reliable production use.
    """

    def __init__(self, driver_name: str = "firefox", headless: bool = False) -> None:
        self.driver_name = driver_name
        self.headless = headless

    def crawl(self, query: str, limit: int) -> list[Tweet]:
        from playwright.sync_api import sync_playwright

        tweets: list[Tweet] = []
        with sync_playwright() as p:
            browser = _launch_browser(p, self.driver_name, self.headless)
            page = browser.new_page()
            try:
                url = "https://x.com/search?" + urllib.parse.urlencode({"q": query, "src": "typed_query", "f": "live"})
                page.goto(url)
                page.wait_for_selector("article", timeout=15_000)
                seen: set[str] = set()
                while len(tweets) < limit:
                    articles = page.query_selector_all("article")
                    for article in articles:
                        text = (article.inner_text() or "").strip()
                        if not text or text in seen:
                            continue
                        seen.add(text)
                        tweet_id = str(abs(hash(text)))
                        tweets.append(
                            Tweet(
                                id=tweet_id,
                                text=text,
                                author=_extract_author(text),
                                created_at=datetime.now(timezone.utc),
                                url=None,
                            )
                        )
                        if len(tweets) >= limit:
                            break
                    if len(tweets) >= limit:
                        break
                    page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                    page.wait_for_timeout(800)
                    if len(seen) == 0:
                        break
            finally:
                browser.close()
        return tweets


def _launch_browser(p, driver_name: str, headless: bool):
    """Launch a Playwright browser by name."""
    if driver_name == "chrome" or driver_name == "chromium":
        return p.chromium.launch(headless=headless)
    if driver_name == "webkit":
        return p.webkit.launch(headless=headless)
    return p.firefox.launch(headless=headless)


def _parse_time(value: str | None) -> datetime:
    if not value:
        return datetime.now(timezone.utc)
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed


def _extract_author(text: str) -> str:
    for line in text.splitlines():
        if line.startswith("@"):
            return line.lstrip("@")
    return "unknown"


def _xquik_metrics(item: dict) -> dict[str, int]:
    fields = {
        "like_count": "likeCount",
        "quote_count": "quoteCount",
        "reply_count": "replyCount",
        "retweet_count": "retweetCount",
        "view_count": "viewCount",
    }
    metrics: dict[str, int] = {}
    for metric_name, payload_name in fields.items():
        value = item.get(payload_name)
        if isinstance(value, int):
            metrics[metric_name] = value
    return metrics


def _offline_query_terms(query: str) -> list[str]:
    ignored = {"and", "en", "is", "lang", "or", "retweet"}
    terms: list[str] = []
    for token in re.findall(r"[#@]?[A-Za-z0-9_]+", query.lower()):
        cleaned = token.lstrip("#@")
        if cleaned and cleaned not in ignored:
            terms.append(cleaned)
    return terms
