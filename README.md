# TwitterBot: X/Twitter Daily Intelligence Reporter

![Python](https://img.shields.io/badge/Python-3.13-3776AB?style=flat-square&logo=python&logoColor=white)
![Selenium](https://img.shields.io/badge/Selenium-Browser%20Login%20Fallback-43B02A?style=flat-square&logo=selenium&logoColor=white)
![SQLite](https://img.shields.io/badge/Storage-SQLite-003B57?style=flat-square&logo=sqlite&logoColor=white)
![Focus](https://img.shields.io/badge/Focus-Social%20Listening%20%7C%20Sentiment%20Reporting-0f766e?style=flat-square)

TwitterBot is a production-style X/Twitter social listening toolkit. It can authenticate through a browser, crawl daily feeds through the official X API or a browser fallback, analyze sentiment, extract trends, persist history, and generate Markdown, HTML, and JSON reports.

This is a complete rewrite of the original 2019 “login and like tweets” script. The new version focuses on daily intelligence reporting instead of click automation.

## Why This Repo Matters

Social media automation projects often stop at browser scripting. A more useful system answers operational questions:

- What are people saying about a topic today?
- Is the conversation positive, neutral, or negative?
- Which hashtags, mentions, and terms are trending?
- Which tweets should be reviewed by a human?
- Can daily reports be persisted and compared over time?

This repo demonstrates a safer and more valuable direction: crawl, analyze, report, and retain evidence.

## What It Does

| Capability | Implementation |
|---|---|
| Login | Selenium opens X/Twitter login; supports manual login or env-based credentials |
| Crawling | Official X API v2 recent search, Selenium browser search fallback, or local JSON feed |
| Sentiment | Transparent rule-based positive/neutral/negative scoring |
| Trend extraction | Top terms, hashtags, and mentions |
| Reporting | Markdown, HTML, and JSON daily reports |
| Persistence | SQLite report history with tweet-level sentiment records |
| Watchlists | Run multiple configured topics in one command |
| CLI | `login`, `crawl`, `report`, `daily`, `watchlist`, and `history` commands |
| Tests | Offline test suite with no API keys required |

## Architecture

```text
CLI
  -> login / crawl / report / daily / watchlist / history
  -> crawler source
       -> official X API recent search
       -> Selenium browser search fallback
       -> local JSON feed for offline runs
  -> sentiment analyzer
  -> trend extraction
  -> report writers
       -> Markdown
       -> HTML
       -> JSON
  -> SQLite history store
```

## Responsible Use

Prefer the official X API for production crawling. Browser automation is intended for manually authenticated research workflows and should be used conservatively. Do not use this project for spam, mass engagement, credential abuse, platform-limit evasion, or access-control bypassing.

## Quick Start

```bash
git clone https://github.com/manjeetkumar53/TwitterBot.git
cd TwitterBot

python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Run the full offline pipeline:

```bash
python app.py daily \
  --query "#AI" \
  --source file \
  --input data/sample_tweets.json \
  --markdown reports/ai-daily.md \
  --html reports/ai-daily.html \
  --json reports/ai-daily.json
```

View:

- `reports/ai-daily.md` for a readable Markdown report
- `reports/ai-daily.html` for a browser-friendly report
- `reports/ai-daily.json` for machine-readable output
- `data/twitterbot.sqlite3` for persisted report history

## CLI Workflows

### 1. Login

```bash
python app.py login
```

Optional environment variables:

```env
X_USERNAME=
X_PASSWORD=
BROWSER_DRIVER=firefox
HEADLESS=false
```

Manual login is recommended. Never commit credentials.

### 2. Crawl From Official X API

```bash
export X_BEARER_TOKEN="..."

python app.py crawl \
  --source api \
  --query "agentic AI lang:en -is:retweet" \
  --limit 50 \
  --output output/tweets.json
```

### 3. Crawl From Browser Search

```bash
python app.py crawl \
  --source browser \
  --query "agentic AI" \
  --limit 30 \
  --output output/tweets.json
```

### 4. Generate Reports From Existing Tweets

```bash
python app.py report \
  --query "agentic AI" \
  --input output/tweets.json \
  --markdown reports/agentic-ai.md \
  --html reports/agentic-ai.html \
  --json reports/agentic-ai.json
```

### 5. Run Daily Crawl + Analyze + Persist

```bash
python app.py daily \
  --source api \
  --query "RAG evaluation lang:en -is:retweet" \
  --limit 50 \
  --markdown reports/rag-eval.md \
  --html reports/rag-eval.html \
  --json reports/rag-eval.json
```

### 6. Run A Watchlist

```bash
python app.py watchlist \
  --config config/watchlist.json \
  --source api \
  --reports-dir reports
```

### 7. View Persisted History

```bash
python app.py history --limit 10
```

Example output:

```text
   3 | 2026-04-29T08:30:00+00:00 | RAG evaluation lang:en -is:retweet | total=50 dominant=positive avg=0.18
```

## Report Contents

Each daily report includes:

- generated timestamp
- query
- total tweets analyzed
- positive / neutral / negative distribution
- average sentiment score
- dominant sentiment
- top terms
- top hashtags
- top mentions
- tweet-level sentiment table

## Data Model

Crawler output:

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

SQLite tables:

| Table | Purpose |
|---|---|
| `report_runs` | One row per generated report with summary metrics |
| `report_tweets` | Tweet-level sentiment records for each report run |

## Configuration

`.env.example`:

```env
X_BEARER_TOKEN=
X_USERNAME=
X_PASSWORD=
BROWSER_DRIVER=firefox
HEADLESS=false

TWITTERBOT_SOURCE=file
TWITTERBOT_INPUT=data/sample_tweets.json
TWITTERBOT_DB=data/twitterbot.sqlite3
TWITTERBOT_REPORTS_DIR=reports
```

Watchlist config:

```json
{
  "topics": [
    {
      "name": "agentic-ai",
      "query": "agentic AI lang:en -is:retweet",
      "limit": 50
    }
  ]
}
```

## Project Structure

```text
TwitterBot/
├── app.py
├── x_daily_reporter/
│   ├── analyzer.py          # sentiment and trend extraction
│   ├── auth.py              # Selenium login helper
│   ├── cli.py               # command-line interface
│   ├── config.py            # env and watchlist config
│   ├── crawlers.py          # API, browser, and file crawlers
│   ├── models.py            # dataclasses
│   ├── pipeline.py          # daily crawl/analyze/report pipeline
│   ├── reporter.py          # Markdown, HTML, JSON writers
│   └── storage.py           # SQLite report history
├── config/
│   └── watchlist.json
├── data/
│   └── sample_tweets.json
├── tests/
├── requirements.txt
└── README.md
```

## Validation

```bash
pytest -q
python app.py daily --query "#AI" --source file --input data/sample_tweets.json
python app.py history
```

The test suite validates:

- sentiment labels and scoring
- hashtag and mention extraction
- Markdown, HTML, and JSON report generation
- daily pipeline execution
- SQLite report persistence

## Design Decisions

- **No click automation:** the project reports on content instead of liking/following/spamming.
- **Official API first:** stable and appropriate for production crawling.
- **Browser fallback:** available for manual research, isolated behind a crawler interface.
- **Rule-based sentiment first:** transparent, deterministic, and testable without model keys.
- **Multiple report formats:** Markdown for docs, HTML for review, JSON for downstream systems.
- **SQLite history:** simple persistence for trend comparison without external infrastructure.
- **Offline mode:** the full pipeline runs locally with sample data.

## Production Hardening Backlog

- Add scheduled daily execution through GitHub Actions or cron
- Add optional LLM sentiment classifier behind the same analyzer contract
- Add topic clustering and entity extraction
- Add dashboard for trend history
- Add Slack/email report delivery
- Add Postgres storage option for team use

## License

[MIT](LICENSE)
