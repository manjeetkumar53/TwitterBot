from __future__ import annotations

import json
import os
import time
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
            query_lower = query.lower().lstrip("#")
            tweets = [tweet for tweet in tweets if query_lower in tweet.text.lower()]
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


class BrowserSearchCrawler:
    """Selenium browser fallback for manually authenticated X/Twitter sessions.

    Browser automation is intentionally conservative: it opens search pages and
    reads visible tweet cards. Prefer the official API for reliable production use.
    """

    def __init__(self, driver_name: str = "firefox", headless: bool = False) -> None:
        self.driver_name = driver_name
        self.headless = headless

    def crawl(self, query: str, limit: int) -> list[Tweet]:
        from selenium import webdriver
        from selenium.webdriver.common.by import By

        driver = _build_driver(self.driver_name, self.headless)
        tweets: list[Tweet] = []
        try:
            url = "https://x.com/search?" + urllib.parse.urlencode({"q": query, "src": "typed_query", "f": "live"})
            driver.get(url)
            time.sleep(4)
            seen: set[str] = set()
            while len(tweets) < limit:
                articles = driver.find_elements(By.CSS_SELECTOR, "article")
                for article in articles:
                    text = article.text.strip()
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
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight)")
                time.sleep(2)
                if len(seen) == 0:
                    break
        finally:
            driver.quit()
        return tweets


def _build_driver(driver_name: str, headless: bool):
    from selenium import webdriver

    if driver_name == "chrome":
        options = webdriver.ChromeOptions()
        if headless:
            options.add_argument("--headless=new")
        return webdriver.Chrome(options=options)

    options = webdriver.FirefoxOptions()
    if headless:
        options.add_argument("-headless")
    return webdriver.Firefox(options=options)


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
