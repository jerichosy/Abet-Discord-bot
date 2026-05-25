# Copilot Cloud Agent Instructions

## Project overview
- Python 3.10 Discord bot; entry point is `main.py`.
- Bot features live in `cogs/`; database models in `models/`; DB helpers/migrations in `database/`.
- Docker-first workflow exists (see `Dockerfile` and `docker-compose.yml`).

## Repository layout
- `main.py`: bot startup, session setup, cog loading, and DB table creation.
- `cogs/`: command implementations and utilities.
- `models/`: SQLAlchemy models and engine setup.
- `database/`: migration/maintenance scripts.
- `scripts/`: helper shell scripts for docker compose (`attachdocker.sh`, `logsdocker.sh`, `restart.sh`).

## Environment & configuration
- Python version: use the version in `.python-version` (3.10.x).
- Dependency manager: **uv** with `pyproject.toml` + `uv.lock`.
- Secrets/config:
  - Copy `.env.template` to `.env` and fill values (BOT_TOKEN, DB_URI, API keys, etc.).
  - `config.py` is expected at runtime (mounted by docker-compose) but is **not** in the repo; create it locally when needed.

## Common commands
- Install deps (CI-style): `uv sync --locked --all-extras --dev`
- Run locally: `uv run python main.py` (or activate `.venv` and run `python main.py`)
- Lint (matches CI):
  - `uvx flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics`
  - `uvx flake8 . --count --exit-zero --max-complexity=10 --max-line-length=127 --statistics`
- Docker build: `docker build . --file Dockerfile --tag abet-discord-bot:<tag>`
- Docker compose: `docker compose up -d` (requires `.env` + `config.py`)

## CI workflows
- **python-lint.yml**: flake8 via `uvx` (syntax checks + exit-zero report).
- **python-app.yml**: `uv sync --locked --all-extras --dev` then `uv tree`.
- **docker-image.yml**: builds the Docker image.
- There are no automated tests beyond linting at the moment.

## Conventions (from CONTRIBUTING)
- Reject user input that is too long; do **not** truncate it.
- URL host variables should **not** include a trailing slash; put the slash at the start of the path.
- Reuse the existing `aiohttp.ClientSession` (via `ctx.session` or `bot.session`); do **not** create one per request.
- Prefer lazy initialization for clients/APIs when practical (exceptions: DB and `aiohttp.ClientSession`).
- Use timezone-aware datetimes; avoid naive `datetime` objects.

## Dev container note
- The devcontainer extends the same `bot` service from `docker-compose.yml`. Starting the devcontainer will stop any running prod container and rebuild the image; switching environments requires a rebuild.

## Errors encountered & workarounds
- `uvx` was missing in the environment. Workaround: install uv locally with `python -m pip install uv`.
- `uvx flake8 .` can fail after `uv sync` because `.venv` is created and gets linted. Workaround: run flake8 before `uv sync`, or remove `.venv` before linting.

## Commit style
- Always use Conventional Commits.
- Format: `<type>(<scope>): <summary>`.
- Use `dotfiles` as default scope.
