# AGENTS.md

## What this is

Streamlit app that converts natural language to SQL queries against an SQLite database of AI job market data. Uses LangChain + DeepSeek API (or local llama.cpp) for LLM inference.

## Setup

```bash
pip install -r requirements.txt
cp .env.example .env   # then set DEEPSEEK_API_KEY
python scripts/init_db.py   # requires data/ai_jobs_market_2025_2026.csv
```

The CSV is from Kaggle and is included in the course submission package for reproducibility. If missing, download:
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
- `scripts/init_db.py` = CSV → SQLite ingestion (idempotent by default; use `--force` to rebuild)

## Database

SQLite at `db/ai_jobs.db`. Tables:
- `job_postings` — main table (1,500 rows), salary/skills/location metadata
- `job_skills` — one row per skill per job (pipe-delimited `required_skills` exploded)
- `job_categories`, `experience_levels`, `location_summary` — pre-aggregated summaries

## Key gotchas

- **No lint, no typecheck** — this repo has zero CI or validation tooling
- **No OpenAI key needed** — it uses DeepSeek API via `langchain-openai` (compatible OpenAI SDK). The env var `DEEPSEEK_API_KEY` is what matters, not `OPENAI_API_KEY`
- **LLM output parsing** — `extract_sql()` strips markdown fences, comments, and truncates long OR chains. Any SQL modification should preserve these anti-hallucination guards
- **`init_db.py` is idempotent by default** — it skips rebuild when `ai_jobs.db` already has data; use `--force` for a full rebuild
- **Local GPU mode** requires a separate llama-server process (see README for exact command)
- **Shared code** — `scripts/llm_utils.py` is the single source of truth for LLM/SQL logic. Changes to SQL rules or LLM config go there only

## Code conventions

- Python 3, no type enforcement tooling
- `.env` loaded via `python-dotenv` at module top-level
- LangChain `ChatOpenAI` with `temperature=0`, `max_tokens=1024`
- Charts via matplotlib (Agg backend), rendered through Streamlit
- All SQL is SELECT-only, enforced both in prompt and at runtime (`validate_readonly_sql`, OR chain truncation, length limit)
- Do not include `.env` in the final RAR submission; submit `.env.example` only.
- Unit tests: `python3 -m unittest discover tests/ -v`

## Existing docs

- `README.md` — user-facing setup and usage guide
