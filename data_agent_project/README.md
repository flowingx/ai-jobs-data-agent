# AI Jobs Market Data Analysis Agent

Natural language analysis of 2025-2026 AI job market data using LangChain + SQLite + LLM.

## Features

- Natural language SQL queries (English or Chinese)
- Dual-engine: DeepSeek (Cloud) or Local GPU (llama.cpp)
- Auto visualization (bar/pie charts)
- AI-powered summaries
- 1,500 real AI job postings from Kaggle

## Quick Start

```bash
cd data_agent_project

# 1. Install dependencies
pip install -r requirements.txt

# 2. Configure environment
cp .env.example .env
# Edit .env and add your DeepSeek API key

# 3. Initialize database
python3 scripts/init_db.py

# 4. Start web UI
streamlit run app.py
```

Open `http://localhost:8501` in your browser.

## How to Configure

1. Copy `.env.example` to `.env`:
   ```bash
   cp .env.example .env
   ```

2. Edit `.env` and fill in your API key:
   ```env
   DEEPSEEK_API_KEY=sk-your-key-here
   ```

3. Get a DeepSeek API key at: https://platform.deepseek.com/

## Dual-Engine Setup

### DeepSeek (Cloud) - Default

- Stable, recommended for demos
- Requires internet and API key
- Max tokens: 4096

### Local GPU (llama.cpp) - Optional

- Offline, data stays private
- Requires GPU and local server

Start the GPU server in a separate terminal:

```bash
LD_LIBRARY_PATH=/usr/local/cuda-12.6/lib64:/tmp/llama-cuda-build/build/bin \
  /tmp/llama-cuda-build/build/bin/llama-server \
  --model ~/models/Qwen3VL-4B-Instruct-Q4_K_M.gguf \
  --mmproj ~/models/mmproj-Qwen3VL-4B-Instruct-Q8_0.gguf \
  --host 127.0.0.1 --port 8080 --ctx-size 4096 -ngl 99
```

Then select "Local GPU" in the UI sidebar.

## CLI Usage

```bash
# DeepSeek (default)
python3 scripts/data_agent.py -q "What are the top 5 skills?"

# Local GPU
python3 scripts/data_agent.py -q "What are the top 5 skills?" -e local
```

## Project Structure

```
data_agent_project/
├── .env.example          # Environment config template
├── .gitignore            # Git ignore rules
├── AGENT.md              # Technical developer docs
├── README.md             # This file
├── requirements.txt      # Python dependencies
├── db/ai_jobs.db         # SQLite database (generated)
├── data/
│   └── ai_jobs_market_2025_2026.csv  # Source dataset
├── scripts/
│   ├── init_db.py        # Data ingestion
│   └── data_agent.py     # SQL Agent with fallback
└── app.py                # Streamlit web UI
```

## Database Schema

| Table | Rows | Description |
|-------|------|-------------|
| job_postings | 1,500 | Job listings with salary, skills, location |
| job_skills | 9,548 | Normalized skill records |
| job_categories | 12 | Aggregated stats by category |
| experience_levels | 4 | Aggregated stats by experience |
| location_summary | 20 | Aggregated stats by location |

## License

Apache-2.0
