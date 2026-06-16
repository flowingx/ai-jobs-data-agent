#!/usr/bin/env python3
"""Start llama.cpp server with Qwen3-4B model (OpenAI-compatible API)."""

import os
import sys
import time
import signal
import subprocess
from pathlib import Path

MODEL_PATH = os.getenv(
    "LLM_MODEL_PATH",
    str(Path(__file__).parent.parent.parent / "models" / "Qwen3-4B-Q4_K_M.gguf"),
)
HOST = os.getenv("LLM_HOST", "0.0.0.0")
PORT = int(os.getenv("LLM_PORT", "8080"))
N_GPU_LAYERS = int(os.getenv("LLM_N_GPU_LAYERS", "99"))
N_CTX = int(os.getenv("LLM_N_CTX", "4096"))


def main():
    if not Path(MODEL_PATH).exists():
        print(f"ERROR: Model not found at {MODEL_PATH}")
        print("Set LLM_MODEL_PATH environment variable to your GGUF model path.")
        sys.exit(1)

    cmd = [
        sys.executable, "-m", "llama_cpp.server",
        "--model", MODEL_PATH,
        "--host", HOST,
        "--port", str(PORT),
        "--n_gpu_layers", str(N_GPU_LAYERS),
        "--n_ctx", str(N_CTX),
    ]

    print("=" * 60)
    print("Starting LLM Server")
    print(f"  Model: {MODEL_PATH}")
    print(f"  Address: http://{HOST}:{PORT}")
    print(f"  GPU Layers: {N_GPU_LAYERS}")
    print(f"  Context: {N_CTX}")
    print("=" * 60)

    proc = subprocess.Popen(cmd, stdout=sys.stdout, stderr=sys.stderr)

    def shutdown(sig, frame):
        print("\nShutting down server...")
        proc.terminate()
        proc.wait()
        sys.exit(0)

    signal.signal(signal.SIGINT, shutdown)
    signal.signal(signal.SIGTERM, shutdown)

    print("Waiting for server to be ready...")
    import urllib.request
    for i in range(120):
        time.sleep(2)
        try:
            urllib.request.urlopen(f"http://localhost:{PORT}/v1/models", timeout=2)
            print(f"\nServer ready at http://localhost:{PORT}")
            print("Press Ctrl+C to stop.")
            proc.wait()
            return
        except Exception:
            if i % 5 == 0:
                print(f"  Waiting... ({i * 2}s)")

    print("ERROR: Server failed to start within 240 seconds.")
    proc.terminate()
    sys.exit(1)


if __name__ == "__main__":
    main()
