import csv
from pathlib import Path

import click

from .database import get_connection, init_db
from .whatsapp_sender import send_message


@click.group()
def cli():
    """Command line interface for WhatsUp bot."""
    pass


@cli.command("send-messages")
@click.argument("csv_file", type=click.Path(exists=True, path_type=Path))
def send_messages_cmd(csv_file: Path) -> None:
    """Import phone numbers from CSV_FILE and send messages."""
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


@cli.command("update-db")
def update_db_cmd() -> None:
    """Initialize or update the SQLite database."""
    with get_connection() as conn:
        init_db(conn)
    click.echo("Database updated")


@cli.command()
def stats() -> None:
    """Print simple statistics about sent messages and survey replies."""
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
