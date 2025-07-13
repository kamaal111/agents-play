ARG UV_VERSION="0.7.20"
ARG NODE_VERSION="24"

FROM debian:bookworm-slim

# Install general packages to make this dev container work
RUN apt update && apt install -y zsh curl git vim httpie jq unzip bash sudo

# Install UV
RUN curl -LsSf https://astral.sh/uv/${UV_VERSION}/install.sh | sh

# Oh My Zsh
RUN sh -c "$(curl -fsSL https://raw.githubusercontent.com/ohmyzsh/ohmyzsh/master/tools/install.sh)" "" --unattended
RUN git clone https://github.com/zsh-users/zsh-autosuggestions ~/.oh-my-zsh/custom/plugins/zsh-autosuggestions
RUN git clone https://github.com/zsh-users/zsh-syntax-highlighting.git ~/.oh-my-zsh/custom/plugins/zsh-syntax-highlighting
RUN git clone https://github.com/zsh-users/zsh-completions ~/.oh-my-zsh/custom/plugins/zsh-completions

# Copy custom zsh configuration
COPY .devcontainer/.zshrc /root/.zshrc

# Install Rust up for cargo tools
RUN curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y

# Install Dev tools
RUN . ~/.cargo/env && cargo install atuin
RUN . ~/.cargo/env && cargo install eza
RUN . ~/.cargo/env && cargo install fnm
