from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from x_daily_reporter.crawlers import BrowserSearchCrawler, FileCrawler, XApiCrawler, XquikCrawler
from x_daily_reporter.models import DailyReport, Tweet
from x_daily_reporter.reporter import build_report, write_html, write_json, write_markdown
from x_daily_reporter.storage import SQLiteReportStore


@dataclass(frozen=True)
class PipelineResult:
    report: DailyReport
    markdown_path: Path
    json_path: Path
    html_path: Path | None
    run_id: int | None


class DailyFeedPipeline:
    def __init__(self, *, db_path: Path | None = None) -> None:
        self.store = SQLiteReportStore(db_path) if db_path else None

    def crawl(self, *, source: str, query: str, limit: int, input_path: Path, headless: bool = False) -> list[Tweet]:
        if source == "api":
            return XApiCrawler().crawl(query, limit)
        if source == "xquik":
            return XquikCrawler().crawl(query, limit)
        if source == "browser":
            return BrowserSearchCrawler(headless=headless).crawl(query, limit)
        return FileCrawler(input_path).crawl(query, limit)

    def run(
        self,
        *,
        source: str,
        query: str,
        limit: int,
        input_path: Path,
        markdown_path: Path,
        json_path: Path,
        html_path: Path | None = None,
        headless: bool = False,
        persist: bool = True,
    ) -> PipelineResult:
        tweets = self.crawl(source=source, query=query, limit=limit, input_path=input_path, headless=headless)
        report = build_report(query, tweets)
        write_markdown(report, markdown_path)
        write_json(report, json_path)
        if html_path:
            write_html(report, html_path)
        run_id = self.store.save(report) if persist and self.store else None
        return PipelineResult(
            report=report,
            markdown_path=markdown_path,
            json_path=json_path,
            html_path=html_path,
            run_id=run_id,
        )
