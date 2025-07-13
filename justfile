set dotenv-load

# List available commands
default:
    just --list --unsorted

# Run server in dev mode
dev-server: prepare-server
    uv run server/agents_play/main.py

# Run frontend in dev mode
dev-fe: prepare-fe
    pnpm dev

# Lint code
lint: lint-server lint-fe

# Lint server code
lint-server:
    uv run ruff check .

# Lint frontend code
lint-fe:
    pnpm lint

# Lint and fix any issues that can be fixed automatically
lint-fix: lint-fix-server lint-fix-fe

# Lint and fix any server issues that can be fixed automatically
lint-fix-server:
    uv run ruff check . --fix

# Lint and fix any frontend issues that can be fixed automatically
lint-fix-fe:
    pnpm lint:fix

# Type check
type-check: type-check-server

# Type check server
type-check-server:
    uv run mypy .

# Type check frontend
type-check-fe:
    pnpm type-check

# Format code
format: format-server format-fe

# Format server code
format-server:
    uv run ruff format .

# Format frontend code
format-fe:
    pnpm format

# Format frontend code
format-check-fe:
    pnpm format:check

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
