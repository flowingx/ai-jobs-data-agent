#!/bin/bash
# Kill any existing server
pkill -9 -f "llama_cpp.server" 2>/dev/null
sleep 2

cd /home/flow/ai-jobs-data-agent

nohup python3 -m llama_cpp.server \
    --model /home/flow/models/Qwen3-4B-Q4_K_M.gguf \
    --host 0.0.0.0 \
    --port 8080 \
    --n_gpu_layers 99 \
    --n_ctx 4096 \
    > /tmp/llm_server.log 2>&1 &

echo $! > /tmp/llm_server.pid
echo "Server started with PID $(cat /tmp/llm_server.pid)"
