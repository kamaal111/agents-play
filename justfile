set dotenv-load

# List available commands
default:
    just --list --unsorted

# Run app in dev mode
dev: prepare
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

# Prepare to run project
prepare: install-modules

# Install modules
install-modules:
    uv sync

# Bootstrap project
bootstrap: prepare setup-pre-commit

# Set up dev container. This step runs after building the dev container
post-dev-container-create:
    just bootstrap

[private]
setup-pre-commit:
    #!/bin/zsh

    . .venv/bin/activate
    pre-commit install
