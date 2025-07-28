"""Простой диалог опроса в WhatsApp."""

from __future__ import annotations

from datetime import datetime
from typing import Callable, List

from .database import get_connection, save_user_survey
from .whatsapp_sender import send_message, wait_for_reply
from .zoom import schedule_meeting

# Вопросы, задаваемые в ходе опроса
QUESTIONS: List[str] = [
    "Сколько вам лет?",
    "Укажите ваше образование",
    "Укажите ваш пол",
]

# Настройки квалификации
AGE_MIN = 25
AGE_MAX = 35
REQUIRED_EDUCATION = {"высшее", "higher"}
ZOOM_LINK = "https://zoom.us/j/123456789"


def _qualifies(age: int, education: str, gender: str | None = None) -> bool:
    """Вернуть ``True``, если ответы удовлетворяют критериям."""

    # параметр ``gender`` пока не участвует в логике отбора, но оставлен для
    # будущих расширений
    _ = gender  # заглушка для неиспользуемого параметра
    return AGE_MIN <= age <= AGE_MAX and any(
        e in education.lower() for e in REQUIRED_EDUCATION
    )


def run_survey(phone: str, name: str, *, get_answer: Callable[[str, str], str | None] | None = None) -> None:
    """Провести с пользователем простой опрос."""
    conn = get_connection()
    answers: List[str] = []
    if get_answer is None:
        def get_answer(_phone: str, question: str) -> str:
            return input(f"{question} ")
    try:
        welcome = (
            "Здравствуйте! Мы проводим небольшой опрос по выбору участников "
            "для исследования. Пожалуйста, ответьте на несколько вопросов."
        )
        send_message(phone, welcome)

        for question in QUESTIONS:
            send_message(phone, question)
            answer = get_answer(phone, question)
            if answer is None:
                break
            answers.append(answer)

        save_user_survey(conn, phone, name, "|".join(answers))

        try:
            age = int(answers[0])
        except (ValueError, IndexError):
            age = 0
        education = answers[1] if len(answers) > 1 else ""
        gender = answers[2] if len(answers) > 2 else ""
        if _qualifies(age, education, gender):
            try:
                link = schedule_meeting({"phone": phone, "name": name})
            except Exception:
                link = ZOOM_LINK
            send_message(phone, f"Вы подходите! Приглашаем на встречу: {link}")
        else:
            send_message(phone, "Спасибо за участие! К сожалению, критерии не соответствуют.")
    finally:
        conn.close()


def run_survey_whatsapp(phone: str, name: str) -> None:
    """Запустить опрос, обмениваясь сообщениями через WhatsApp."""

    def _get_answer(_: str, __: str) -> str | None:
        return wait_for_reply(phone)

    run_survey(phone, name, get_answer=_get_answer)


if __name__ == "__main__":
    phone = input("Phone number: ")
    name = input("Name: ")
    run_survey(phone, name)
