set dotenv-load

# List available commands
default:
    just --list --unsorted

# Run app in dev mode
dev:
    uv run src/agents_play/main.py

# Lint code
lint:
    uv run ruff check .

# Lint and fix any issues that can be fixed automatically
lint-fix:
    uv run ruff check . --fix

# Type check
type-check:
    uv run mypy .

# Format code
format:
    uv run ruff format .

# Quality checks
quality: lint type-check format

# Set up dev container. This step runs after building the dev container
post-dev-container-create:
    just .devcontainer/post-create
