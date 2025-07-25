"""WhatsApp messaging utilities using Selenium."""

from __future__ import annotations

from urllib.parse import quote_plus

import os

from selenium import webdriver
from selenium.common.exceptions import TimeoutException, WebDriverException
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from .database import get_connection, log_message


def start_driver(
    driver_path: str | None = None,
    profile_path: str | None = None,
    *,
    headless: bool = True,
) -> webdriver.Chrome:
    """Return a Selenium WebDriver instance configured for Chrome.

    ``profile_path`` or the ``CHROME_PROFILE_DIR`` environment variable can be
    used to specify a Chrome user data directory. Set ``headless=False`` when
    signing in for the first time to display the browser window.
    """

    options = webdriver.ChromeOptions()
    if headless:
        options.add_argument("--headless")

    profile = profile_path or os.environ.get("CHROME_PROFILE_DIR")
    if profile:
        options.add_argument(f"--user-data-dir={profile}")

    path = driver_path or os.environ.get("CHROMEDRIVER_PATH")
    if path:
        service = Service(executable_path=path)
    else:
        service = Service(ChromeDriverManager().install())
    return webdriver.Chrome(service=service, options=options)


def send_message(phone_number: str, text: str, *, profile_path: str | None = None) -> str:
    """Send a WhatsApp message to ``phone_number``.

    ``profile_path`` can point to a Chrome profile directory or be omitted to
    rely on ``CHROME_PROFILE_DIR``. The function launches WhatsApp Web, sends
    ``text`` to the given phone number, writes a record to the database and
    returns the send status. Possible statuses are ``"sent"``,
    ``"invalid_number"`` and ``"connection_error"``.
    """
    status = "sent"
    conn = get_connection()
    driver = None
    profile = profile_path or os.environ.get("CHROME_PROFILE_DIR")
    try:
        driver = start_driver(profile_path=profile)
        url = f"https://web.whatsapp.com/send?phone={phone_number}&text={quote_plus(text)}"
        driver.get(url)

        try:
            # Wait for the message box and press ENTER to send.
            input_box = WebDriverWait(driver, 15).until(
                EC.presence_of_element_located(
                    (By.XPATH, "//div[@contenteditable='true' and @data-tab]")
                )
            )
            prev_out = len(
                driver.find_elements(By.XPATH, "//div[contains(@class, 'message-out')]")
            )
            input_box.send_keys(Keys.ENTER)
            WebDriverWait(driver, 10).until(
                lambda d: len(
                    d.find_elements(By.XPATH, "//div[contains(@class, 'message-out')]")
                )
                > prev_out
            )
            status = "sent"
        except TimeoutException:
            status = "invalid_number"
    except WebDriverException:
        status = "connection_error"
        raise
    finally:
        log_message(conn, phone_number, text, status)
        conn.close()
        if driver:
            driver.quit()
    return status


def wait_for_reply(phone_number: str, timeout: int = 60, *, profile_path: str | None = None) -> str | None:
    """Wait for a reply message from ``phone_number`` within ``timeout`` seconds.

    ``profile_path`` behaves like in :func:`send_message`. The function opens
    WhatsApp Web for the provided phone number and waits until a new incoming
    message appears in the chat. The text of the last received message is
    returned or ``None`` if no reply arrives before the timeout expires.
    """

    profile = profile_path or os.environ.get("CHROME_PROFILE_DIR")
    driver = start_driver(profile_path=profile)
    url = f"https://web.whatsapp.com/send?phone={phone_number}"
    driver.get(url)
    last_selector = "//div[contains(@class, 'message-in')]//span[@class='selectable-text']"
    try:
        # Ensure the chat has loaded
        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.XPATH, "//div[@contenteditable='true' and @data-tab]"))
        )
        existing = driver.find_elements(By.XPATH, last_selector)
        start_count = len(existing)
        WebDriverWait(driver, timeout).until(
            lambda d: len(d.find_elements(By.XPATH, last_selector)) > start_count
        )
        messages = driver.find_elements(By.XPATH, last_selector)
        return messages[-1].text if messages else None
    except TimeoutException:
        return None
    finally:
        driver.quit()
