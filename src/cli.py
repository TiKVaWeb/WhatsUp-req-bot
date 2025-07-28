import csv
from pathlib import Path

import click

from .database import get_connection, init_db
from threading import Semaphore, Thread

from .whatsapp_sender import send_message
from .survey import run_survey_whatsapp


@click.group()
def cli():
    """Командная оболочка для бота WhatsUp."""
    pass


@cli.command("send-messages")
@click.argument("csv_file", type=click.Path(exists=True, path_type=Path))
def send_messages_cmd(csv_file: Path) -> None:
    """Импортировать номера из CSV_FILE и отправить сообщения."""
    with open(csv_file, newline="", encoding="utf-8") as fh:
        try:
            reader = csv.DictReader(fh)
            use_dict = "phone" in (reader.fieldnames or [])
        except csv.Error:
            fh.seek(0)
            use_dict = False
            reader = csv.reader(fh)
        for row in reader:
            phone = row["phone"] if use_dict else row[0]
            message = row.get("message") if use_dict else None
            text = message or "Hello from WhatsUp bot!"
            click.echo(f"Sending to {phone}...")
            try:
                send_message(phone, text)
            except Exception as exc:
                click.echo(f"Error sending to {phone}: {exc}")


@cli.command("survey")
@click.argument("csv_file", type=click.Path(exists=True, path_type=Path))
@click.option("--workers", default=1, show_default=True, help="Parallel surveys")
def run_survey_cmd(csv_file: Path, workers: int) -> None:
    """Запустить интерактивный опрос для номеров из CSV_FILE."""

    with open(csv_file, newline="", encoding="utf-8") as fh:
        try:
            reader = csv.DictReader(fh)
            use_dict = "phone" in (reader.fieldnames or [])
        except csv.Error:
            fh.seek(0)
            use_dict = False
            reader = csv.reader(fh)
        phones = [row["phone"] if use_dict else row[0] for row in reader]

    sem = Semaphore(workers)
    threads: list[Thread] = []

    def worker(number: str) -> None:
        with sem:
            click.echo(f"\nStarting survey for {number}")
            run_survey_whatsapp(number, number)
            click.echo(f"Finished survey for {number}")

    for num in phones:
        thread = Thread(target=worker, args=(num,), daemon=True)
        threads.append(thread)
        thread.start()

    for t in threads:
        t.join()


@cli.command("update-db")
def update_db_cmd() -> None:
    """Инициализировать или обновить базу данных SQLite."""
    with get_connection() as conn:
        init_db(conn)
    click.echo("Database updated")


@cli.command()
def stats() -> None:
    """Показать статистику отправленных сообщений и ответов на опрос."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM messages")
    sent = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM users WHERE answers IS NOT NULL")
    replies = cur.fetchone()[0]
    conn.close()
    click.echo(f"Messages sent: {sent}")
    click.echo(f"Replies received: {replies}")


if __name__ == "__main__":
    cli()
