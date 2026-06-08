# Mac Laptop Setup

Personal MacBook setup — software installed via Homebrew, grouped by purpose.

## Prerequisites

Install Homebrew first:

```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

## Terminal & Shell

```bash
brew install --cask iterm2
brew install --cask font-caskaydia-cove-nerd-font
brew install neovim
brew install tmux
brew install fzf
brew install bat
brew install eza
brew install zoxide
brew install --cask sublime-text
```

## Development

```bash
# Node.js
brew install node
brew install nvm

# Python
brew install python@3.12

# Claude
brew install --cask claude
brew install --cask claude-code
```

## Homelab Clients

Software used to interact with the homelab:

```bash
# Remote access to homelab over Tailscale
brew install tailscale

# VPN
brew install --cask surfshark

# Media playback (Plex / direct file)
brew install --cask vlc

# Torrent client (also runs on starr VM — local for testing)
brew install --cask qbittorrent
```

## Media & Streaming

```bash
brew install --cask obs
brew install --cask elgato-capture-device-utility
brew install --cask astro-command-center
```

## Finance

```bash
brew install --cask webull
```

## One-liner — install everything

```bash
brew install \
  neovim tmux fzf bat eza zoxide \
  node nvm python@3.12 \
  tailscale

brew install --cask \
  iterm2 font-caskaydia-cove-nerd-font sublime-text \
  claude claude-code \
  surfshark vlc qbittorrent \
  obs elgato-capture-device-utility astro-command-center \
  webull
```
