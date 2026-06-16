# AGENT.md - Data Analysis Agent Configuration

## Dual-Engine Architecture

The agent supports two LLM backends:

| Engine | Default | Max Tokens | Use Case |
|--------|---------|------------|----------|
| **DeepSeek (Cloud)** | ✅ Yes | 4096 | Stable, recommended for demos |
| **Local GPU (llama.cpp)** | Optional | 1024 | Offline, data privacy |

## Setup

### 1. Environment Configuration

```bash
cd data_agent_project
cp .env.example .env
```

Edit `.env` and fill in your DeepSeek API key:

```env
DEEPSEEK_API_KEY=sk-your-key-here
```

### 2. Initialize Database

```bash
python3 scripts/init_db.py
```

### 3. Start Web UI

```bash
streamlit run app.py
```

Open `http://localhost:8501`. Use the sidebar radio button to switch engines.

## Local GPU Mode (Optional)

If you want to use the local llama.cpp server instead of DeepSeek:

```bash
# Start the GPU server in a separate terminal:
LD_LIBRARY_PATH=/usr/local/cuda-12.6/lib64:/tmp/llama-cuda-build/build/bin \
  /tmp/llama-cuda-build/build/bin/llama-server \
  --model ~/models/Qwen3VL-4B-Instruct-Q4_K_M.gguf \
  --mmproj ~/models/mmproj-Qwen3VL-4B-Instruct-Q8_0.gguf \
  --host 127.0.0.1 --port 8080 --ctx-size 4096 -ngl 99
```

Then select "Local GPU (llama.cpp)" in the UI sidebar.

## CLI Usage

```bash
# DeepSeek (default)
python3 scripts/data_agent.py -q "What are the top 5 skills?"

# Local GPU
python3 scripts/data_agent.py -q "What are the top 5 skills?" -e local
```
