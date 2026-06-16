#!/bin/bash
# start_llm_server.sh - Launch llama.cpp server with GPU offloading
# Usage: ./start_llm_server.sh [model_name]

set -e

LLAMA_SERVER=~/llama-cpp/llama-b9616/llama-server
MODEL_DIR=~/models

# Default model: Qwen3-4B Q4_K_M
DEFAULT_MODEL="Qwen3-4B-Q4_K_M.gguf"
MODEL_NAME="${1:-$DEFAULT_MODEL}"
MODEL_PATH="${MODEL_DIR}/${MODEL_NAME}"

HOST="${LLM_HOST:-0.0.0.0}"
PORT="${LLM_PORT:-8080}"
N_GPU_LAYERS="${N_GPU_LAYERS:-99}"
N_CTX="${N_CTX:-4096}"

echo "================================================"
echo "  Starting llama.cpp LLM Server"
echo "================================================"
echo "  Model:   ${MODEL_PATH}"
echo "  Server:  ${LLAMA_SERVER}"
echo "  Address: http://${HOST}:${PORT}"
echo "  GPU Layers: ${N_GPU_LAYERS}"
echo "  Context: ${N_CTX}"
echo "================================================"

if [ ! -f "$LLAMA_SERVER" ]; then
    echo "ERROR: llama-server not found at $LLAMA_SERVER"
    echo "Make sure llama.cpp is compiled at ~/llama-cpp"
    exit 1
fi

if [ ! -f "$MODEL_PATH" ]; then
    echo "ERROR: Model not found at $MODEL_PATH"
    echo "Available models in $MODEL_DIR:"
    ls -1 "$MODEL_DIR"/*.gguf 2>/dev/null || echo "  (no .gguf files found)"
    exit 1
fi

exec "$LLAMA_SERVER" \
    --model "$MODEL_PATH" \
    --host "$HOST" \
    --port "$PORT" \
    --n-gpu-layers "$N_GPU_LAYERS" \
    --ctx-size "$N_CTX" \
    --chat-template chatml
