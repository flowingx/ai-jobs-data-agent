# AGENT.md - Data Analysis Agent Configuration

## LLM Server (User-Managed)

**CRITICAL: The LLM server is managed by the user in a separate terminal. Do NOT start, stop, or test it.**

The server runs at `http://127.0.0.1:8080/v1` and is always assumed to be alive.

### Startup Command (WSL/Linux - GPU mode)

```bash
LD_LIBRARY_PATH=/usr/local/cuda-12.6/lib64:/tmp/llama-cuda-build/build/bin \
  /tmp/llama-cuda-build/build/bin/llama-server \
  --model ~/models/Qwen3VL-4B-Instruct-Q4_K_M.gguf \
  --mmproj ~/models/mmproj-Qwen3VL-4B-Instruct-Q8_0.gguf \
  --host 127.0.0.1 --port 8080 --ctx-size 4096 -ngl 99
```

## Configuration

| Setting | Value |
|---------|-------|
| LLM Endpoint | `http://127.0.0.1:8080/v1` |
| Model | `Qwen3VL-4B-Instruct-Q4_K_M.gguf` |
| API Key | `not-needed` (local server) |
| Database | `db/ai_jobs.db` (SQLite) |

## Running the Agent

```bash
# Initialize database
python3 scripts/init_db.py

# Run agent with a question
python3 scripts/data_agent.py -q "What are the top 5 skills?"

# Start web UI
streamlit run app.py
```
