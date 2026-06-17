# AGENTS.md

## What this is

Streamlit app that converts natural language to SQL queries against an SQLite database of AI job market data. Uses LangChain + DeepSeek API (or local llama.cpp) for LLM inference.

## Setup

```bash
pip install -r requirements.txt
cp .env.example .env   # then set DEEPSEEK_API_KEY
python3 scripts/init_db.py   # requires data/ai_jobs_market_2025_2026.csv
```

The CSV is from Kaggle — not checked in. If missing, download:
```bash
kaggle datasets download -d alitaqishah/ai-jobs-market-2025-2026-salaries -p data --unzip
```

## Run

- **Web UI**: `streamlit run app.py` → http://localhost:8501
- **CLI**: `python3 scripts/data_agent.py -q "What are the top 5 skills?"`
- **CLI (local GPU)**: `python3 scripts/data_agent.py -q "..." -e local`
- **CLI (interactive)**: `python3 scripts/data_agent.py -i`

## Architecture

```
app.py (Streamlit) ──┐
                     ├─→ LLM generates SQL → SQLite → results + charts + AI summary
data_agent.py (CLI) ─┘
```

- `app.py` = full web UI with tabs (Smart Query, Data Browser, Preset Analysis)
- `scripts/data_agent.py` = CLI version with retry logic
- `scripts/init_db.py` = CSV → SQLite ingestion (destructive: deletes and rebuilds DB)

## Database

SQLite at `db/ai_jobs.db`. Tables:
- `job_postings` — main table (1,500 rows), salary/skills/location metadata
- `job_skills` — one row per skill per job (pipe-delimited `required_skills` exploded)
- `job_categories`, `experience_levels`, `location_summary` — pre-aggregated summaries

## Key gotchas

- **No tests, no lint, no typecheck** — this repo has zero CI or validation tooling
- **No OpenAI key needed** — it uses DeepSeek API via `langchain-openai` (compatible OpenAI SDK). The env var `DEEPSEEK_API_KEY` is what matters, not `OPENAI_API_KEY`
- **LLM output parsing** — `extract_sql()` in both files strips markdown fences, comments, and truncates long OR chains. Any SQL modification should preserve these anti-hallucination guards
- **`init_db.py` is destructive** — it deletes and rebuilds `ai_jobs.db` from scratch
- **Local GPU mode** requires a separate llama-server process (see README for exact command)
- **`careers.db`** in `db/` appears unused by app.py or data_agent.py
- **Two duplicate codebases** — `app.py` and `scripts/data_agent.py` share nearly identical LLM/SQL logic. Changes to SQL rules or LLM config must be applied to both files

## Code conventions

- Python 3, no type enforcement tooling
- `.env` loaded via `python-dotenv` at module top-level
- LangChain `ChatOpenAI` with `temperature=0`, `max_tokens=1024`
- Charts via matplotlib (Agg backend), rendered through Streamlit
- All SQL is SELECT-only, enforced both in prompt and at runtime (OR chain truncation, length limit)

## Existing docs

- `AGENT.md` — detailed technical reference (architecture, SQL rules, chart types, env vars)
- `README.md` — user-facing setup and usage guide
