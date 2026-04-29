from __future__ import annotations

from pathlib import Path

from x_daily_reporter.pipeline import DailyFeedPipeline
from x_daily_reporter.storage import SQLiteReportStore


def test_daily_pipeline_writes_reports_and_persists_history(tmp_path: Path) -> None:
    db_path = tmp_path / "twitterbot.sqlite3"
    markdown_path = tmp_path / "report.md"
    json_path = tmp_path / "report.json"
    html_path = tmp_path / "report.html"

    result = DailyFeedPipeline(db_path=db_path).run(
        source="file",
        query="#AI",
        limit=10,
        input_path=Path("data/sample_tweets.json"),
        markdown_path=markdown_path,
        json_path=json_path,
        html_path=html_path,
    )

    assert result.run_id == 1
    assert markdown_path.exists()
    assert json_path.exists()
    assert html_path.exists()

    history = SQLiteReportStore(db_path).recent_runs()
    assert len(history) == 1
    assert history[0]["query"] == "#AI"
    assert history[0]["total"] == 3
