set dotenv-load

PORT := "8000"

UV := "uv"
UVR := UV + " run"

PN := "pnpm"
PNR := PN + " run"

# List available commands
default:
    just --list --unsorted

# Run server in dev mode
dev-server: prepare-server
    {{ UVR }} uvicorn server.agents_play.main:app --reload --host 0.0.0.0 --port {{ PORT }}

# Run frontend in dev mode
dev-fe: prepare-fe
    {{ PNR }} dev

# Lint code
lint: lint-server lint-fe

# Lint server code
lint-server:
    {{ UVR }} ruff check .

# Lint frontend code
lint-fe:
    {{ PNR }} lint

# Lint and fix any issues that can be fixed automatically
lint-fix: lint-fix-server lint-fix-fe

# Lint and fix any server issues that can be fixed automatically
lint-fix-server:
    {{ UVR }} ruff check . --fix

# Lint and fix any frontend issues that can be fixed automatically
lint-fix-fe:
    {{ PNR }} lint:fix

# Type check
type-check: type-check-server

# Type check server
type-check-server:
    {{ UVR }} mypy .

# Type check frontend
type-check-fe:
    {{ PNR }} type-check

# Format code
format: format-server format-fe

# Format server code
format-server:
    {{ UVR }} ruff format .

# Format frontend code
format-fe:
    {{ PNR }} format

# Format frontend code
format-check-fe:
    {{ PNR }} format:check

# Quality checks
quality: quality-server quality-fe

# Quality server checks
quality-server: lint-server type-check-server format-server

# Quality frontend checks
quality-fe: lint-fe type-check-fe format-check-fe

# Prepare to run project
prepare: prepare-server prepare-fe

# Prepare server
prepare-server: install-python-modules

# Prepare frontend
prepare-fe: install-node-modules

# Install modules
install-modules: install-python-modules install-node-modules

# Install Node modules
install-node-modules:
    #!/bin/zsh

    . ~/.zshrc

    echo "Y" | pnpm i

# Install Python modules
install-python-modules:
    uv sync

# Bootstrap project
bootstrap: install-node install-pnpm prepare setup-pre-commit

# Set up dev container. This step runs after building the dev container
post-dev-container-create: bootstrap

[private]
install-pnpm:
    #!/bin/zsh

    . ~/.zshrc

    corepack enable pnpm

[private]
install-node:
    #!/bin/zsh

    . ~/.zshrc

    fnm completions --shell zsh
    fnm install

[private]
setup-pre-commit:
    #!/bin/zsh

    . .venv/bin/activate
    pre-commit install
