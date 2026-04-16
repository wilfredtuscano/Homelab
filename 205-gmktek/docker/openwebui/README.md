# Open WebUI

ChatGPT-style web interface for interacting with Ollama models running locally on Jarvis.

## Access

| Interface | URL |
|-----------|-----|
| Web UI | `http://192.168.1.205:3000` |

## Notes

- Connects to Ollama via `host.docker.internal:11434` — Ollama must be running on the same host
- Data (user accounts, chat history, settings) persisted in `./data/`
- Create an admin account on first visit
