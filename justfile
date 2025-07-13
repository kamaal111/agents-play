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
