# Ollama

Local LLM inference server. Runs large language models entirely on-device using the Jarvis machine's GPU/CPU.

## Access

| Interface | URL |
|-----------|-----|
| API | `http://192.168.1.205:11434` |

## Notes

- Models are downloaded with `ollama pull <model>` (e.g. `ollama pull llama3`)
- Open WebUI (separate stack) connects to Ollama at `http://host.docker.internal:11434`
- Downloaded models are stored in the container volume — pull models after first start
