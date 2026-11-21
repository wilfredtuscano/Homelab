# whisper

Whisper large-v3 transcription over HTTP on jarvis's GPU, for a recording-transcription workflow.
`https://whisper.local.wilfredtuscano.com` (Traefik on dnspi) or `http://192.168.1.205:9000`.

## Engine

[openai-whisper](https://github.com/openai/whisper) on the ROCm build of PyTorch
(`rocm/pytorch`, ROCm 7.2.4, same as the host). The Mac fallback runs
mlx-whisper, which is a port of openai-whisper, so both sides share the decoder, the
`no_speech_prob` estimate and the word-timestamp alignment. Output is comparable line
for line.

Considered and not used:

- **whisper.cpp** (HIP or Vulkan): fast, but its word times come from token
  timestamps or its own DTW, not the alignment the Mac uses, and its VAD is a
  different implementation.
- **faster-whisper**: its CTranslate2 backend targets CUDA; on gfx1151 it would be another
  custom ROCm build to keep alive, like the Ollama patch. Speed is not the constraint here.

## Silence handling

Server-side, with the same parameters as the Mac reference script, so clients just
upload a file:

1. Silero VAD speech spans, padded 0.3 s each side, merged across gaps under 1 s.
2. Spans quieter than `min_dbfs` dropped (mic `-45`, game `-60`).
3. One whisper call per span, `condition_on_previous_text=False`, word timestamps on.
4. Segments dropped when `no_speech_prob >= 0.6` or the text has no letters.

Times are absolute seconds from file start.

## API

`POST /transcribe` (multipart):

| Field | Required | Notes |
|---|---|---|
| `file` | yes | any format ffmpeg reads; 16 kHz mono WAV is the usual input |
| `language` | yes | `hi`, `en`, ... No default: `en` on Hindi speech translates instead of transcribing |
| `min_dbfs` | no | loudness gate, default `-45` |

```sh
curl -sS --max-time 3600 https://whisper.local.wilfredtuscano.com/transcribe \
  -F file=@clip.wav -F language=hi -F min_dbfs=-45
```

Response:

```json
{"language": "hi",
 "segments": [{"start": 2.1, "end": 3.9, "text": "...",
               "words": [{"w": "...", "start": 2.36, "end": 2.8}]}],
 "info": {"model": "large-v3", "device": "...", "audio_s": 45.0, "spans": 6,
          "speech_s": 20.1, "wall_s": 9.8}}
```

`GET /health` reports the device, whether the model is loaded and the queue length.

## Limits

- Upload: 1024 MB (`WHISPER_MAX_UPLOAD_MB`). A 2 h 16 kHz mono WAV is about 230 MB.
- One transcription at a time; up to 4 requests running or waiting (`WHISPER_MAX_QUEUE`),
  then `429`.
- Synchronous: the response arrives when the file is done. Set a client timeout well
  above the expected wall time.
- A client that disconnects does not cancel its job: the server finishes it anyway.
- The model loads on first request (~10 s) and unloads after 10 min idle
  (`WHISPER_KEEP_ALIVE`), so it only holds GPU memory while in use.
  openai-whisper keeps the weights in fp32 (about 6 GB); `.half()` on the model fails in
  its layers, so that saving is not available.
- Through Traefik a 15-minute response comes back fine (measured below). Its default 60 s
  `readTimeout` applies to the upload, which takes about a second on the LAN.

## Measured (2026-11-21, ROCm 7.2.4, Radeon 8060S)

| Test | Result |
|---|---|
| 2 h mic track (21 min of speech after VAD) | 886 s wall, Mac M1 Max mlx-whisper 539 s; GPU ~96% busy |
| Same file, output vs Mac | 520 vs 521 segments; 10-line spot check matches (one word differs) |
| Hindi test clip | text and all 48 word times identical to the Mac |
| Voice-cue clip | all seven "जर्विस" word times identical to the Mac |
| GPU memory | 0.5 GB with the model unloaded, 7 GB loaded between requests, ~11 GB peak during one |
| With gpt-oss:120b loaded (60 GiB) | both fit; Ollama mid-transcription ran at 25 tok/s vs 36 alone, no reload |
| End to end over HTTPS (Traefik), 2 h file, gpt-oss loaded | HTTP 200 after 887 s; upload 230 MB in under a second on the LAN |

`TORCH_ROCM_AOTRITON_ENABLE_EXPERIMENTAL=1` turns on ROCm flash attention: about 40% faster
on the test clips with identical output.

Ollama does not see this service's memory as its own: `OLLAMA_MAX_LOADED_MODELS` only counts
Ollama's models, and its scheduler sizes loads from free GPU memory, so it simply has ~11 GB
less while a transcription runs.

## Deploy

```sh
cd ~/docker/whisper && docker compose up -d --build
```

The first request downloads large-v3 (~3 GB) into the `whisper-models` volume.
