"""WhatsApp messaging utilities using Selenium."""

from __future__ import annotations

from urllib.parse import quote_plus

from selenium import webdriver
from selenium.common.exceptions import TimeoutException, WebDriverException
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from .database import get_connection, log_message


def start_driver() -> webdriver.Chrome:
    """Return a Selenium WebDriver instance configured for Chrome."""
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")
    return webdriver.Chrome(options=options)


def send_message(phone_number: str, text: str) -> str:
    """Send a WhatsApp message to ``phone_number``.

    The function launches WhatsApp Web, sends ``text`` to the given phone
    number, writes a record to the database and returns the send status.
    Possible statuses are ``"sent"``, ``"invalid_number"`` and
    ``"connection_error"``.
    """
    status = "sent"
    conn = get_connection()
    driver = None
    try:
        driver = start_driver()
        url = f"https://web.whatsapp.com/send?phone={phone_number}&text={quote_plus(text)}"
        driver.get(url)

        try:
            # Wait for the message box and press ENTER to send.
            input_box = WebDriverWait(driver, 15).until(
                EC.presence_of_element_located((By.XPATH, "//div[@contenteditable='true' and @data-tab]"))
            )
            input_box.send_keys(Keys.ENTER)
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


def wait_for_reply(phone_number: str, timeout: int = 60) -> str | None:
    """Wait for a reply message from ``phone_number`` within ``timeout`` seconds.

    The function opens WhatsApp Web for the provided phone number and waits
    until a new incoming message appears in the chat. The text of the last
    received message is returned or ``None`` if no reply arrives before the
    timeout expires.
    """

    driver = start_driver()
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
