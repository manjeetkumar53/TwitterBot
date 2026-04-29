from __future__ import annotations

import json

from x_daily_reporter.models import Tweet
from x_daily_reporter.reporter import build_report, write_html, write_json, write_markdown


def test_report_writes_markdown_and_json(tmp_path) -> None:
    tweets = [
        Tweet(id="1", author="alice", text="Great #AI progress and strong opportunity"),
        Tweet(id="2", author="bob", text="Bad outage risk and slow response"),
    ]
    report = build_report("#AI", tweets)
    markdown_path = tmp_path / "report.md"
    json_path = tmp_path / "report.json"
    html_path = tmp_path / "report.html"

    write_markdown(report, markdown_path)
    write_json(report, json_path)
    write_html(report, html_path)

    assert "Daily X/Twitter Sentiment Report" in markdown_path.read_text(encoding="utf-8")
    assert "Tweet-Level Sentiment" in html_path.read_text(encoding="utf-8")
    payload = json.loads(json_path.read_text(encoding="utf-8"))
    assert payload["total"] == 2
    assert payload["distribution"]["positive"] == 1
    assert payload["distribution"]["negative"] == 1
