from __future__ import annotations

import os
import time
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
        from selenium.webdriver.common.by import By
        from selenium.webdriver.common.keys import Keys

        from x_daily_reporter.crawlers import _build_driver

        driver = _build_driver(self.config.driver, self.config.headless)
        try:
            driver.get("https://x.com/i/flow/login")
            time.sleep(3)
            if self.config.username and self.config.password:
                username_input = driver.find_element(By.CSS_SELECTOR, "input[autocomplete='username']")
                username_input.send_keys(self.config.username)
                username_input.send_keys(Keys.ENTER)
                time.sleep(2)
                password_input = driver.find_element(By.CSS_SELECTOR, "input[name='password']")
                password_input.send_keys(self.config.password)
                password_input.send_keys(Keys.ENTER)
            else:
                print("Login page opened. Complete login manually in the browser window.")
            time.sleep(self.config.manual_timeout_seconds)
        finally:
            driver.quit()
