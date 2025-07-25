"""Simple survey dialogue over WhatsApp."""

from __future__ import annotations

from datetime import datetime
from typing import List

from .database import get_connection, save_user_survey
from .whatsapp_sender import send_message
from .zoom import schedule_meeting

# Questions asked during the survey
QUESTIONS: List[str] = [
    "Сколько вам лет?",
    "Укажите ваше образование",
]

# Qualification settings
AGE_MIN = 25
AGE_MAX = 35
REQUIRED_EDUCATION = {"высшее", "higher"}
ZOOM_LINK = "https://zoom.us/j/123456789"


def _qualifies(age: int, education: str) -> bool:
    """Return ``True`` if the provided answers satisfy the criteria."""
    return AGE_MIN <= age <= AGE_MAX and any(e in education.lower() for e in REQUIRED_EDUCATION)


def run_survey(phone: str, name: str) -> None:
    """Conduct a simple questionnaire with the user."""
    conn = get_connection()
    answers: List[str] = []
    try:
        welcome = (
            "Здравствуйте! Мы проводим небольшой опрос по выбору участников "
            "для исследования. Пожалуйста, ответьте на несколько вопросов."
        )
        send_message(phone, welcome)

        for question in QUESTIONS:
            send_message(phone, question)
            answer = input(f"{question} ")
            answers.append(answer)

        save_user_survey(conn, phone, name, "|".join(answers))

        try:
            age = int(answers[0])
        except (ValueError, IndexError):
            age = 0
        education = answers[1] if len(answers) > 1 else ""
        if _qualifies(age, education):
            try:
                link = schedule_meeting({"phone": phone, "name": name})
            except Exception:
                link = ZOOM_LINK
            send_message(phone, f"Вы подходите! Приглашаем на встречу: {link}")
        else:
            send_message(phone, "Спасибо за участие! К сожалению, критерии не соответствуют.")
    finally:
        conn.close()


if __name__ == "__main__":
    phone = input("Phone number: ")
    name = input("Name: ")
    run_survey(phone, name)
