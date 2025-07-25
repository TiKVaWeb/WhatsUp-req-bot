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

## Setup
1. Create a virtual environment:
   ```bash
   python -m venv .venv
   source .venv/bin/activate
   ```
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

Development happens inside the `src/` directory.

## Database
The project uses SQLite for storing user data and outgoing messages. To create
the local database with some example records run:

```bash
python -m src.database
```

This will generate a `database.sqlite3` file in the project root containing the
required tables.

## Zoom configuration
Zoom credentials can be provided through the `config.json` file in the project
root or via environment variables. The file should contain at least the JWT
token used for API requests:

```json
{
  "zoom_jwt_token": "YOUR_TOKEN_HERE"
}
```

Alternatively set the `ZOOM_JWT_TOKEN` environment variable.
