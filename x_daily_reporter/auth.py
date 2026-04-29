from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class LoginConfig:
    username: str | None = None
    password: str | None = None
    driver: str = "firefox"
    headless: bool = False
    manual_timeout_seconds: int = 120


class BrowserLogin:
    """Open X/Twitter login and optionally submit credentials from env vars.

    Prefer manual login or OAuth/API tokens for real use. Do not commit passwords.
    """

    def __init__(self, config: LoginConfig) -> None:
        self.config = config

    @classmethod
    def from_env(cls) -> "BrowserLogin":
        return cls(
            LoginConfig(
                username=os.getenv("X_USERNAME") or os.getenv("TWITTER_USERNAME"),
                password=os.getenv("X_PASSWORD") or os.getenv("TWITTER_PASSWORD"),
                driver=os.getenv("BROWSER_DRIVER", "firefox"),
                headless=os.getenv("HEADLESS", "false").lower() == "true",
            )
        )

    def open_login(self) -> None:
        from playwright.sync_api import sync_playwright

        from x_daily_reporter.crawlers import _launch_browser

        with sync_playwright() as p:
            browser = _launch_browser(p, self.config.driver, self.config.headless)
            page = browser.new_page()
            try:
                page.goto("https://x.com/i/flow/login")
                if self.config.username and self.config.password:
                    page.wait_for_selector("input[autocomplete='username']", timeout=15_000)
                    page.fill("input[autocomplete='username']", self.config.username)
                    page.press("input[autocomplete='username']", "Enter")
                    page.wait_for_selector("input[name='password']", timeout=10_000)
                    page.fill("input[name='password']", self.config.password)
                    page.press("input[name='password']", "Enter")
                else:
                    print("Login page opened. Complete login manually in the browser window.")
                page.wait_for_timeout(self.config.manual_timeout_seconds * 1000)
            finally:
                browser.close()
