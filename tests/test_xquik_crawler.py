from __future__ import annotations

import json
from typing import Any

from x_daily_reporter.crawlers import XquikCrawler


class _Response:
    def __init__(self, payload: dict[str, Any]) -> None:
        self.payload = payload

    def __enter__(self) -> "_Response":
        return self

    def __exit__(self, *_args: object) -> None:
        return None

    def read(self) -> bytes:
        return json.dumps(self.payload).encode("utf-8")


def test_xquik_crawler_maps_search_results(monkeypatch) -> None:
    payload = {
        "tweets": [
            {
                "id": "123",
                "text": "Launch update for #AI",
                "author": {"username": "xquik"},
                "createdAt": "2026-06-21T04:00:00.000Z",
                "likeCount": 5,
                "retweetCount": 2,
            }
        ]
    }

    calls = []

    def fake_urlopen(request, timeout):
        calls.append((request.full_url, timeout))
        return _Response(payload)

    monkeypatch.setenv("XQUIK_API_KEY", "test-key")
    monkeypatch.setattr("urllib.request.urlopen", fake_urlopen)

    tweets = XquikCrawler().crawl("#AI", 10)

    assert len(tweets) == 1
    assert tweets[0].id == "123"
    assert tweets[0].author == "xquik"
    assert tweets[0].metrics["like_count"] == 5
    assert "q=%23AI" in calls[0][0]
    assert calls[0][1] == 30
