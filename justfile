set dotenv-load

# List available commands
default:
    just --list --unsorted

# Run app in dev mode
dev:
    uv run src/agents_play/main.py

# Set up dev container. This step runs after building the dev container
post-dev-container-create:
    just .devcontainer/post-create
