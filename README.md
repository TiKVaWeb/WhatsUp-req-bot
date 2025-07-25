# WhatsUp Requirement Bot

This repository contains a basic structure for a bot project. The source code lives
in the `src/` directory. Use this template to start implementing a messaging
bot or any other automation.

## Goals
- Provide a clean starting point for development.
- Isolate dependencies with a virtual environment.
- Keep the repository small and free from generated files.

## Requirements
- Python 3.11 (tested with 3.11.8).
- Packages listed in `requirements.txt`.
- Google Chrome installed (ChromeDriver is downloaded automatically).

## Setup
1. Create a virtual environment:
   ```bash
   python -m venv .venv
   source .venv/bin/activate
   ```
2. Install dependencies from the requirements file:
   ```bash
   pip install -r requirements.txt
   ```

Development happens inside the `src/` directory.

## ChromeDriver configuration
Selenium relies on the [ChromeDriver](https://chromedriver.chromium.org/) binary.
If no executable is provided the correct version is downloaded automatically.
You can still specify a custom path via the `CHROMEDRIVER_PATH` environment
variable or by passing it to `whatsapp_sender.start_driver()`.

Example:

```bash
export CHROMEDRIVER_PATH=/opt/chromedriver
```

## WhatsApp Web profile
To keep the WhatsApp session active between runs create a separate Chrome
profile and sign in once manually. Launch Chrome with the desired directory,
open WhatsApp Web and scan the QR code:

```bash
google-chrome --user-data-dir=/path/to/wa-profile https://web.whatsapp.com
```

Set the ``CHROME_PROFILE_DIR`` environment variable to this directory (or pass
the path to ``send_message()``/``wait_for_reply()``) before running the bot:

```bash
export CHROME_PROFILE_DIR=/path/to/wa-profile
```


## Database
The project uses SQLite for storing user data and outgoing messages. To create
the local database with some example records run:

```bash
python -m src.database
```

This will generate a `database.sqlite3` file in the project root containing the
required tables.

## Zoom configuration
Zoom API requests now use OAuth (Server-to-Server) credentials. Create an app in
the Zoom marketplace and note the **Client ID**, **Client Secret** and
**Account ID** values. Add them to `config.json` or export matching environment
variables:

```json
{
  "zoom_client_id": "YOUR_CLIENT_ID",
  "zoom_client_secret": "YOUR_CLIENT_SECRET",
  "zoom_account_id": "YOUR_ACCOUNT_ID"
}
```

Environment variable names are `ZOOM_CLIENT_ID`, `ZOOM_CLIENT_SECRET` and
`ZOOM_ACCOUNT_ID`.

## CLI usage
The project exposes a small command line interface with several commands. Run
them using `python -m src.cli` followed by the command name.

```bash
python -m src.cli send-messages phones.csv
python -m src.cli update-db
python -m src.cli stats
```

`send-messages` imports phone numbers from a CSV file and starts sending a
default greeting. `update-db` synchronises the SQLite database creating tables if
needed. `stats` prints how many messages were sent and how many answers were
recorded.
