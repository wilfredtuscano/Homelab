# ROCm build of PyTorch matching the host's ROCm (7.2.4), which has gfx1151 kernels.
FROM rocm/pytorch:rocm7.2.4_ubuntu24.04_py3.12_pytorch_release_2.10.0

RUN apt-get update && apt-get install -y --no-install-recommends ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# --no-deps on whisper and silero-vad: their requirements pull the CUDA torch
# and triton wheels from PyPI, which would replace the ROCm builds in the image.
RUN pip install --no-cache-dir \
        fastapi==0.165.0 uvicorn==0.54.0 python-multipart==0.0.34 \
        tiktoken==0.14.0 numba==0.68.1 more-itertools tqdm \
    && pip install --no-cache-dir --no-deps openai-whisper==20250625 silero-vad==6.2.3

COPY server.py /app/server.py
WORKDIR /app
CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "9000", "--timeout-keep-alive", "75"]
