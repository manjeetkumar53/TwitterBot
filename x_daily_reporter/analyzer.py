from __future__ import annotations

import re
from collections import Counter

from x_daily_reporter.models import SentimentResult, Tweet


POSITIVE_TERMS = {
    "amazing",
    "benefit",
    "best",
    "bullish",
    "excellent",
    "gain",
    "good",
    "great",
    "growth",
    "happy",
    "improve",
    "improved",
    "love",
    "opportunity",
    "positive",
    "profit",
    "strong",
    "success",
    "win",
}

NEGATIVE_TERMS = {
    "bad",
    "bearish",
    "bug",
    "crash",
    "decline",
    "delay",
    "drop",
    "fail",
    "failed",
    "fear",
    "loss",
    "negative",
    "outage",
    "problem",
    "risk",
    "slow",
    "weak",
    "worse",
    "worst",
}

STOPWORDS = {
    "about",
    "after",
    "again",
    "also",
    "and",
    "are",
    "because",
    "been",
    "from",
    "has",
    "have",
    "into",
    "just",
    "more",
    "that",
    "the",
    "their",
    "this",
    "with",
    "your",
}


class SentimentAnalyzer:
    def analyze(self, tweet: Tweet) -> SentimentResult:
        tokens = tokenize(tweet.text)
        positive = [token for token in tokens if token in POSITIVE_TERMS]
        negative = [token for token in tokens if token in NEGATIVE_TERMS]
        raw_score = len(positive) - len(negative)
        normalized = raw_score / max(len(positive) + len(negative), 1)
        if normalized >= 0.20:
            label = "positive"
        elif normalized <= -0.20:
            label = "negative"
        else:
            label = "neutral"
        return SentimentResult(
            tweet_id=tweet.id,
            label=label,
            score=round(normalized, 4),
            positive_terms=positive,
            negative_terms=negative,
        )

    def analyze_many(self, tweets: list[Tweet]) -> list[SentimentResult]:
        return [self.analyze(tweet) for tweet in tweets]


def tokenize(text: str) -> list[str]:
    return [token.lower() for token in re.findall(r"[A-Za-z][A-Za-z0-9_'-]{1,}", text)]


def top_terms(tweets: list[Tweet], limit: int = 12) -> list[tuple[str, int]]:
    counter: Counter[str] = Counter()
    for tweet in tweets:
        for token in tokenize(tweet.text):
            if token not in STOPWORDS and not token.startswith("http"):
                counter[token] += 1
    return counter.most_common(limit)


def top_hashtags(tweets: list[Tweet], limit: int = 10) -> list[tuple[str, int]]:
    counter: Counter[str] = Counter()
    for tweet in tweets:
        counter.update(tag.lower() for tag in re.findall(r"#([A-Za-z0-9_]+)", tweet.text))
    return counter.most_common(limit)


def top_mentions(tweets: list[Tweet], limit: int = 10) -> list[tuple[str, int]]:
    counter: Counter[str] = Counter()
    for tweet in tweets:
        counter.update(handle.lower() for handle in re.findall(r"@([A-Za-z0-9_]+)", tweet.text))
    return counter.most_common(limit)
