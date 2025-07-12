# List available commands
default:
    just --list --unsorted

# Set up dev container. This step runs after building the dev container
post-dev-container-create:
    just .devcontainer/post-create
