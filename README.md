# TwitterBot: X/Twitter Daily Sentiment Reporter

![Python](https://img.shields.io/badge/Python-3.13-3776AB?style=flat-square&logo=python&logoColor=white)
![Selenium](https://img.shields.io/badge/Selenium-Browser%20Automation-43B02A?style=flat-square&logo=selenium&logoColor=white)
![Focus](https://img.shields.io/badge/Focus-Social%20Listening%20%7C%20Sentiment%20Reporting-0f766e?style=flat-square)

Production-style social listening toolkit for X/Twitter: authenticate through browser when needed, crawl daily feeds through the official API or browser fallback, analyze tweet sentiment, extract trends, and generate Markdown/JSON reports.

This revamps the original 2019 “login and like tweets” script into a safer and more useful reporting system.

## Why This Exists

Most social media bots automate clicks. This project focuses on something more valuable for engineering and business teams: daily feed intelligence.

It helps answer:

- What are people saying about a topic today?
- Is the daily conversation positive, neutral, or negative?
- Which terms, hashtags, and mentions are trending?
- Which tweets should be reviewed manually?
- Can a daily report be generated automatically from crawled feeds?

## Capabilities

| Capability | Implementation |
|---|---|
| Login | Selenium opens X/Twitter login; supports manual login or env-based credentials |
| Crawler | Official X API v2 recent search, browser search fallback, or local JSON input |
| Sentiment analysis | Rule-based positive/negative scoring with explainable terms |
| Trend extraction | Top terms, hashtags, and mentions |
| Reporting | Markdown and JSON daily reports |
| CLI workflows | `login`, `crawl`, `report`, and `daily` commands |
| Testing | Unit tests for sentiment and report generation |

## Architecture

```text
CLI
  -> login / crawl / report / daily
  -> crawler source
       -> X API v2 recent search
       -> Selenium browser search fallback
       -> local JSON feed for offline testing
  -> sentiment analyzer
  -> trend extraction
  -> Markdown + JSON daily report
```

## Responsible Use

Prefer the official X API for reliable and compliant crawling. Browser automation is provided as a fallback for manually authenticated sessions and should be used conservatively. Do not use this project to spam, mass-like, evade platform limits, or bypass access controls.

## Quick Start

```bash
git clone https://github.com/manjeetkumar53/TwitterBot.git
cd TwitterBot

python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Run the full offline demo using sample tweets:

```bash
python app.py daily --query "#AI" --source file \
  --input data/sample_tweets.json \
  --markdown reports/daily-report.md \
  --json reports/daily-report.json
```

Open `reports/daily-report.md` to review the generated report.

## CLI Usage

### Open Browser Login

```bash
python app.py login
```

Optional env vars:

```env
X_USERNAME=
X_PASSWORD=
BROWSER_DRIVER=firefox
HEADLESS=false
```

Manual login is recommended. Do not commit credentials.

### Crawl From Official X API

```bash
export X_BEARER_TOKEN="..."

python app.py crawl \
  --source api \
  --query "agentic AI lang:en -is:retweet" \
  --limit 50 \
  --output output/tweets.json
```

### Crawl From Browser Search

```bash
python app.py crawl \
  --source browser \
  --query "agentic AI" \
  --limit 30 \
  --output output/tweets.json
```

### Generate Report From Crawled Tweets

```bash
python app.py report \
  --query "agentic AI" \
  --input output/tweets.json \
  --markdown reports/daily-report.md \
  --json reports/daily-report.json
```

### Daily One-Command Workflow

```bash
python app.py daily \
  --source api \
  --query "agentic AI lang:en -is:retweet" \
  --limit 50 \
  --markdown reports/agentic-ai-daily.md \
  --json reports/agentic-ai-daily.json
```

## Report Output

The Markdown report includes:

- generated timestamp
- tweet count
- positive / neutral / negative distribution
- top terms
- top hashtags
- top mentions
- tweet-level sentiment table

The JSON report includes the same summary plus raw tweet records and sentiment scores for downstream analysis.

## Data Format

Crawler output is stored as:

```json
{
  "tweets": [
    {
      "id": "1001",
      "author": "ai_builder",
      "created_at": "2026-04-29T07:00:00Z",
      "text": "Great progress in #AI tooling today.",
      "url": "https://x.com/ai_builder/status/1001",
      "metrics": {
        "like_count": 10,
        "retweet_count": 2
      }
    }
  ]
}
```

## Project Structure

```text
TwitterBot/
├── app.py                         # CLI entrypoint
├── x_daily_reporter/
│   ├── analyzer.py                # sentiment + trend extraction
│   ├── auth.py                    # Selenium login helper
│   ├── cli.py                     # command-line interface
│   ├── crawlers.py                # API, browser, and file crawlers
│   ├── models.py                  # Tweet/report dataclasses
│   └── reporter.py                # Markdown and JSON report writers
├── data/
│   └── sample_tweets.json
├── tests/
├── requirements.txt
├── .env.example
└── README.md
```

## Validation

```bash
pytest -q
python app.py daily --query "#AI" --source file --input data/sample_tweets.json
```

## Design Decisions

- **Official API first:** most reliable and appropriate path for production crawling.
- **Browser fallback:** useful for manual research workflows, but intentionally conservative.
- **Rule-based sentiment:** transparent, deterministic, and testable without external AI services.
- **Markdown + JSON reports:** human-readable summary and machine-readable output.
- **Offline sample mode:** contributors can test the full workflow without API keys.

## Production Hardening Backlog

- Add scheduled daily runs through GitHub Actions or cron
- Add pluggable LLM-based sentiment classifier
- Add topic clustering and entity extraction
- Add time-series report history
- Add dashboard for sentiment trend comparison
- Store crawled feeds in SQLite or Postgres

## License

[MIT](LICENSE)
