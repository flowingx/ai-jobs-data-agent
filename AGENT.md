# AGENT.md - Technical Developer Documentation

## Architecture

```
User Question → LLM SQL Generation → SQLite Execution → Results + Visualization
     ↓                                        ↓
  (Fallback: retry with error context)    (Charts: bar/pie)
     ↓                                        ↓
  Natural Language Summary ←────────────── Query Results
```

## Dual-Engine Setup

| Engine | Default | Max Tokens | API Key Required |
|--------|---------|------------|------------------|
| DeepSeek (Cloud) | Yes | 4096 | Yes |
| Local GPU (llama.cpp) | Optional | 1024 | No |

## Configuration

1. Copy `.env.example` to `.env`:
   ```bash
   cp .env.example .env
   ```

2. Edit `.env` and fill in your DeepSeek API key:
   ```env
   DEEPSEEK_API_KEY=sk-your-key-here
   ```

3. Get a DeepSeek API key at: https://platform.deepseek.com/

## LLM Server Commands

### DeepSeek (Cloud)

No server needed. Just configure `.env` with your API key.

### Local GPU (llama.cpp)

```bash
LD_LIBRARY_PATH=/usr/local/cuda-12.6/lib64:/tmp/llama-cuda-build/build/bin \
  /tmp/llama-cuda-build/build/bin/llama-server \
  --model ~/models/Qwen3VL-4B-Instruct-Q4_K_M.gguf \
  --mmproj ~/models/mmproj-Qwen3VL-4B-Instruct-Q8_0.gguf \
  --host 127.0.0.1 --port 8080 --ctx-size 4096 -ngl 99
```

### Local CPU (llama.cpp)

```bash
~/llama-cpp/llama-b9616/llama-server \
  --model ~/models/Qwen3-4B-Q4_K_M.gguf \
  --host 127.0.0.1 --port 8080 --ctx-size 4096
```

## Data Pipeline

1. **Source**: `data/ai_jobs_market_2025_2026.csv` (1,500 rows from Kaggle)
2. **Ingestion**: `scripts/init_db.py` → `db/ai_jobs.db`
3. **Query**: `scripts/data_agent.py` or `app.py`

## Agent Logic

- **SQL Generation**: LLM converts natural language to SQL using schema context
- **Multi-query Fallback**: Retries up to 3 times with error context
- **Visualization**: Auto-detects chart type from SQL patterns
- **Summary**: LLM generates natural language explanation

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `DEEPSEEK_API_KEY` | (required for cloud) | DeepSeek API key |
| `DEEPSEEK_BASE_URL` | `https://api.deepseek.com` | DeepSeek API endpoint |
| `DEEPSEEK_MODEL` | `deepseek-chat` | DeepSeek model name |
| `LOCAL_LLM_URL` | `http://127.0.0.1:8080/v1` | Local llama.cpp endpoint |
| `LOCAL_MODEL` | `local-model` | Local model name |

## Dependencies

```
pandas>=1.5
langchain>=0.2
langchain-openai>=0.1
openai>=1.0
sqlalchemy>=2.0
matplotlib>=3.7
streamlit>=1.30
python-dotenv>=1.0
```
