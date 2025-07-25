# whatsapp_utils.py

from __future__ import annotations
import os
import time
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
    headless: bool = False,
) -> webdriver.Chrome:
    options = webdriver.ChromeOptions()
    if headless:
        options.add_argument("--headless")
    profile = profile_path or os.environ.get("CHROME_PROFILE_DIR")
    if profile:
        options.add_argument(f"--user-data-dir={profile}")
    path = driver_path or os.environ.get("CHROMEDRIVER_PATH")
    service = Service(executable_path=path) if path else Service(ChromeDriverManager().install())
    return webdriver.Chrome(service=service, options=options)


def send_message(phone_number: str, text: str, *, profile_path: str | None = None, debug: bool = False) -> str:
    """
    Send a WhatsApp message. Если debug=True — сохраним screenshot и html при ошибке.
    """
    status = "sent"
    conn = get_connection()
    driver = None
    try:
        driver = start_driver(profile_path=profile_path or os.environ.get("CHROME_PROFILE_DIR"))
        driver.get(f"https://web.whatsapp.com/send?phone={phone_number}")

        # 1) Ждём загрузки chat-box
        input_box = WebDriverWait(driver, 30).until(
            EC.presence_of_element_located((By.XPATH, "//footer//div[@contenteditable='true' and @data-tab]"))
        )
        input_box.click()
        input_box.clear()
        input_box.send_keys(text)

        # даём время JS активировать кнопку
        time.sleep(0.5)

        # считаем исходящие
        prev_out = len(driver.find_elements(By.XPATH, "//div[contains(@class, 'message-out')]"))

        # 2) Пробуем клик по разным селекторам
        btn_xpaths = [
            "//footer//button[@data-testid='compose-btn-send']",
            "//button[@aria-label='Send']",
            "//button[@data-icon='send']",
            "//span[@data-testid='send']"
        ]
        clicked = False
        for xp in btn_xpaths:
            try:
                btn = WebDriverWait(driver, 5).until(EC.element_to_be_clickable((By.XPATH, xp)))
                btn.click()
                clicked = True
                break
            except Exception:
                continue

        # 3) Фоллбек — всегда ENTER
        if not clicked:
            input_box.send_keys(Keys.ENTER)

        # 4) Проверяем, что отправилось
        WebDriverWait(driver, 10).until(
            lambda d: len(d.find_elements(By.XPATH, "//div[contains(@class, 'message-out')]")) > prev_out
        )

    except TimeoutException as e:
        status = "invalid_number"
        if debug and driver:
            driver.save_screenshot("whatsapp_debug.png")
            with open("whatsapp_debug.html", "w", encoding="utf-8") as f:
                f.write(driver.page_source)
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
    profile = profile_path or os.environ.get("CHROME_PROFILE_DIR")
    driver = start_driver(profile_path=profile)
    driver.get(f"https://web.whatsapp.com/send?phone={phone_number}")

    last_sel = "//div[contains(@class, 'message-in')]//span[@class='selectable-text']"
    try:
        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.XPATH, "//footer//div[@contenteditable='true' and @data-tab]"))
        )
        existing = driver.find_elements(By.XPATH, last_sel)
        start_count = len(existing)

        WebDriverWait(driver, timeout).until(
            lambda d: len(d.find_elements(By.XPATH, last_sel)) > start_count
        )
        msgs = driver.find_elements(By.XPATH, last_sel)
        return msgs[-1].text if msgs else None
    except TimeoutException:
        return None
    finally:
        driver.quit()
