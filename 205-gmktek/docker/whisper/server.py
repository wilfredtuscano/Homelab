"""Whisper large-v3 transcription service for jarvis (Strix Halo, ROCm).

POST /transcribe takes one audio file and returns segments with word times.
Silence handling copies the Mac reference script
(transcribe_local.py): Silero VAD spans, padded and merged, a loudness gate,
then one whisper call per span with condition_on_previous_text=False, and
segments dropped when no_speech_prob >= 0.6 or the text has no letters.
Without that, large-v3 invents text over silence.

openai-whisper is the engine because mlx-whisper (the Mac side) is a port of
it: same decoding, same no_speech_prob, same word-timestamp alignment, so the
two produce comparable output.
"""

from __future__ import annotations

import asyncio
import gc
import os
import shutil
import tempfile
import threading
import time

import numpy as np
import torch
import whisper
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from silero_vad import get_speech_timestamps, load_silero_vad
from whisper.audio import load_audio

SR = 16000
PAD = 0.3        # seconds kept either side of each speech span
MERGE_GAP = 1.0  # merge spans closer than this, so sentences are not split

MODEL_NAME = os.environ.get("WHISPER_MODEL", "large-v3")
MODEL_DIR = os.environ.get("WHISPER_MODEL_DIR", "/models")
KEEP_ALIVE = float(os.environ.get("WHISPER_KEEP_ALIVE", "600"))  # seconds idle before unload
MAX_UPLOAD = int(os.environ.get("WHISPER_MAX_UPLOAD_MB", "1024")) * 2**20
MAX_QUEUE = int(os.environ.get("WHISPER_MAX_QUEUE", "4"))  # running + waiting

app = FastAPI(title="whisper")
vad = load_silero_vad()  # small, runs on CPU like the Mac reference
_model = None
_model_lock = threading.Lock()
_job_lock = asyncio.Lock()  # one transcription at a time: they would only share the GPU
_queued = 0
_last_used = time.monotonic()


def get_model():
    global _model, _last_used
    with _model_lock:
        if _model is None:
            _model = whisper.load_model(MODEL_NAME, device="cuda", download_root=MODEL_DIR)
        _last_used = time.monotonic()
        return _model


def unload_idle() -> None:
    # Ollama shares this GPU memory; hold the ~3 GB model only while in use.
    global _model
    while True:
        time.sleep(30)
        with _model_lock:
            if _model is not None and _queued == 0 and time.monotonic() - _last_used > KEEP_ALIVE:
                _model = None
                gc.collect()
                torch.cuda.empty_cache()


threading.Thread(target=unload_idle, daemon=True).start()


def rms_dbfs(x: np.ndarray) -> float:
    return 20 * np.log10(float(np.sqrt(np.mean(x ** 2))) + 1e-12)


def has_letters(text: str) -> bool:
    # Real speech always has a letter; stray combining marks and comma runs do not.
    return any(c.isalpha() for c in text)


def speech_spans(audio: np.ndarray, min_dbfs: float) -> list[tuple[float, float]]:
    spans = get_speech_timestamps(torch.from_numpy(audio), vad,
                                  sampling_rate=SR, return_seconds=True)
    total = len(audio) / SR
    merged: list[tuple[float, float]] = []
    for sp in spans:
        start, end = max(0.0, sp["start"] - PAD), min(total, sp["end"] + PAD)
        if merged and start - merged[-1][1] < MERGE_GAP:
            merged[-1] = (merged[-1][0], end)
        else:
            merged.append((start, end))
    return [(a, b) for a, b in merged if rms_dbfs(audio[int(a * SR):int(b * SR)]) >= min_dbfs]


def transcribe(path: str, language: str, min_dbfs: float) -> dict:
    t0 = time.time()
    audio = load_audio(path, sr=SR)  # ffmpeg: any format, resampled to 16 kHz mono float32
    spans = speech_spans(audio, min_dbfs)
    model = get_model()
    segments = []
    for a, b in spans:
        result = model.transcribe(
            audio[int(a * SR):int(b * SR)],
            language=language,
            condition_on_previous_text=False,  # stops one bad segment cascading
            word_timestamps=True,
        )
        segments += [
            {"start": round(a + sg["start"], 2), "end": round(min(b, a + sg["end"]), 2),
             "text": sg["text"].strip(),
             "words": [{"w": w["word"].strip(), "start": round(a + w["start"], 2),
                        "end": round(a + w["end"], 2)} for w in sg.get("words", [])]}
            for sg in result["segments"]
            if has_letters(sg["text"]) and sg.get("no_speech_prob", 0) < 0.6
        ]
    global _last_used
    _last_used = time.monotonic()
    # Hand PyTorch's cached activations back (peak ~11 GB on a 2 h file), keeping
    # only the weights resident between requests.
    torch.cuda.empty_cache()
    return {"language": language, "segments": segments,
            "info": {"model": MODEL_NAME, "device": torch.cuda.get_device_name(0),
                     "audio_s": round(len(audio) / SR, 1), "spans": len(spans),
                     "speech_s": round(sum(b - a for a, b in spans), 1),
                     "wall_s": round(time.time() - t0, 1)}}


@app.get("/health")
def health() -> dict:
    return {"ok": torch.cuda.is_available(), "device": torch.cuda.get_device_name(0),
            "model": MODEL_NAME, "loaded": _model is not None, "queued": _queued}


@app.post("/transcribe")
async def transcribe_endpoint(file: UploadFile = File(...), language: str = Form(...),
                              min_dbfs: float = Form(-45.0)) -> dict:
    # language is required on purpose: "en" on Hindi speech translates rather
    # than transcribes, so there is no safe default.
    global _queued
    if language not in whisper.tokenizer.LANGUAGES:
        raise HTTPException(400, f"unknown language: {language}")
    if _queued >= MAX_QUEUE:
        raise HTTPException(429, "busy, retry later")
    _queued += 1
    tmp = tempfile.NamedTemporaryFile(delete=False, dir=os.environ.get("TMPDIR", "/tmp"))
    try:
        size = 0
        while chunk := await file.read(2**20):
            size += len(chunk)
            if size > MAX_UPLOAD:
                raise HTTPException(413, f"file over {MAX_UPLOAD // 2**20} MB")
            tmp.write(chunk)
        tmp.close()
        async with _job_lock:
            return await asyncio.to_thread(transcribe, tmp.name, language, min_dbfs)
    finally:
        _queued -= 1
        tmp.close()
        os.unlink(tmp.name)
