from __future__ import annotations

from x_daily_reporter.analyzer import SentimentAnalyzer, top_hashtags, top_mentions
from x_daily_reporter.models import Tweet


def test_sentiment_analyzer_labels_positive_and_negative() -> None:
    analyzer = SentimentAnalyzer()

    positive = analyzer.analyze(Tweet(id="1", text="Great success and strong growth for #AI"))
    negative = analyzer.analyze(Tweet(id="2", text="Bad outage risk and weak response"))

    assert positive.label == "positive"
    assert positive.score > 0
    assert negative.label == "negative"
    assert negative.score < 0


def test_extracts_hashtags_and_mentions() -> None:
    tweets = [Tweet(id="1", text="Thanks @team for the great #AI update. #AI")]

    assert top_hashtags(tweets)[0] == ("ai", 2)
    assert top_mentions(tweets)[0] == ("team", 1)
