from __future__ import annotations
import os
import time
from typing import Optional, Dict
from selenium import webdriver
from selenium.common.exceptions import TimeoutException, WebDriverException
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.support.ui import WebDriverWait

from .database import get_connection, log_message

# --- Константы конфигурации ---
DEFAULT_TIMEOUTS: Dict[str, int] = {
    "load_chat": 30,
    "button_click": 5,
    "send_check": 10,
    "reply_check": 60,
}

SELECTORS: Dict[str, list[str] | str] = {
    # Поле ввода сообщения в footer
    "input_box": "//footer//div[@contenteditable='true' and @data-tab]",
    # Возможные XPaths для кнопки "Отправить"
    "send_buttons": [
        "//footer//button[@data-testid='compose-btn-send']",
        "//button[@aria-label='Send']",
        "//button[@data-icon='send']",
        "//span[@data-testid='send']",
    ],
    # Исходящие сообщения (тест по тексту)
    "outgoing_msg": "//div[contains(@class,'message-out')]//span[@class='selectable-text']",
    # Входящие сообщения
    "incoming_msg": "//div[contains(@class,'message-in')]//span[@class='selectable-text']",
}

class WhatsAppClient:
    """
    Контекстный менеджер для управления сессией Selenium Chrome
    и отправки/приёма сообщений через WhatsApp Web.
    """
    def __init__(
        self,
        driver_path: Optional[str] = None,
        profile_path: Optional[str] = None,
        headless: bool = False,
    ):
        options = webdriver.ChromeOptions()
        if headless:
            options.add_argument("--headless")
        profile = profile_path or os.environ.get("CHROME_PROFILE_DIR")
        if profile:
            options.add_argument(f"--user-data-dir={profile}")
        path = driver_path or os.environ.get("CHROMEDRIVER_PATH")
        service = Service(executable_path=path) if path else Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service, options=options)

    def __enter__(self) -> WhatsAppClient:
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.driver:
            self.driver.quit()

    def send_message(
        self,
        phone_number: str,
        text: str,
        debug: bool = False,
    ) -> str:
        """
        Отправить текстовое сообщение в чат с номером phone_number.

        Вернёт один из статусов:
        - "sent": сообщение успешно появилось в чате.
        - "invalid_number": чат не загрузился или сообщение не появилось.
        - "connection_error": ошибка WebDriver.
        """
        status = "sent"
        conn = get_connection()
        try:
            # Открыть чат по номеру
            url = f"https://web.whatsapp.com/send?phone={phone_number}"
            self.driver.get(url)

            # Ожидание поля ввода
            input_box = WebDriverWait(self.driver, DEFAULT_TIMEOUTS['load_chat']).until(
                ec.presence_of_element_located((By.XPATH, SELECTORS['input_box']))
            )
            input_box.click()
            input_box.clear()
            input_box.send_keys(text)
            time.sleep(0.5)  # дать время активировать кнопку

            # Предварительный подсчёт исходящих по тексту
            prev_outgoing = [el.text.strip() for el in self.driver.find_elements(By.XPATH, SELECTORS['outgoing_msg'])]

            # Попытка клика по кнопке отправки
            clicked_with: Optional[str] = None
            for xp in SELECTORS['send_buttons']:
                try:
                    btn = WebDriverWait(self.driver, DEFAULT_TIMEOUTS['button_click']).until(
                        ec.element_to_be_clickable((By.XPATH, xp))
                    )
                    btn.click()
                    clicked_with = xp
                    break
                except Exception:
                    continue

            # Фоллбэк — ENTER
            if not clicked_with:
                input_box.send_keys(Keys.ENTER)
                clicked_with = 'ENTER'

            # Проверка по явному содержимому текста
            def is_sent() -> bool:
                msgs = [el.text.strip() for el in self.driver.find_elements(By.XPATH, SELECTORS['outgoing_msg'])]
                return msgs and msgs[-1] == text

            try:
                WebDriverWait(self.driver, DEFAULT_TIMEOUTS['send_check']).until(lambda d: is_sent())
            except TimeoutException:
                # Если после ENTER не сработало — пробуем JS-клик по кнопке
                if clicked_with == 'ENTER':
                    script = "document.querySelector('footer button[data-testid=\"compose-btn-send\"]')?.click()"
                    self.driver.execute_script(script)
                    WebDriverWait(self.driver, DEFAULT_TIMEOUTS['button_click']).until(lambda d: is_sent())

            if not is_sent():
                raise TimeoutException("Message not detected after all attempts")

            if debug:
                print(f"[DEBUG] Sent via: {clicked_with}")

        except TimeoutException:
            status = "invalid_number"
            if debug:
                # сохраняем дампы для отладки
                self.driver.save_screenshot("whatsapp_debug.png")
                with open("whatsapp_debug.html", "w", encoding="utf-8") as f:
                    f.write(self.driver.page_source)
        except WebDriverException:
            status = "connection_error"
            raise
        finally:
            log_message(conn, phone_number, text, status)
            conn.close()

        return status

    def wait_for_reply(
        self,
        phone_number: str,
        timeout: Optional[int] = None,
    ) -> Optional[str]:
        """
        Открывает чат и ждёт входящее сообщение от phone_number.
        Возвращает текст ответа или None, если время вышло.
        """
        conn = None  # нет логирования здесь
        try:
            url = f"https://web.whatsapp.com/send?phone={phone_number}"
            self.driver.get(url)

            # Подождать поле ввода, чтобы чат загрузился
            WebDriverWait(self.driver, DEFAULT_TIMEOUTS['load_chat']).until(
                ec.presence_of_element_located((By.XPATH, SELECTORS['input_box']))
            )
            existing = self.driver.find_elements(By.XPATH, SELECTORS['incoming_msg'])
            start_count = len(existing)
            wait_time = timeout or DEFAULT_TIMEOUTS['reply_check']

            WebDriverWait(self.driver, wait_time).until(
                lambda d: len(d.find_elements(By.XPATH, SELECTORS['incoming_msg'])) > start_count
            )
            messages = self.driver.find_elements(By.XPATH, SELECTORS['incoming_msg'])
            return messages[-1].text if messages else None
        except TimeoutException:
            return None
        finally:
            # Не закрываем driver, он управляется контекстом
            pass
