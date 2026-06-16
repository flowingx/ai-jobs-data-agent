# AI Jobs Market Data Analysis Agent

Natural language analysis of 2025-2026 AI job market data using LangChain + SQLite + Qwen3-4B (local LLM).

## Features

- **Natural Language Query**: Ask questions in English, get SQL-generated answers
- **Multi-Query Fallback**: Retries SQL generation up to 3 times with error context
- **Auto Visualization**: Bar charts, pie charts, or line charts based on query results
- **AI Summaries**: LLM generates natural language explanations of results
- **Data Browser**: Browse all database tables in the web UI
- **Preset Analysis**: 12+ pre-configured analysis scenarios

## Quick Start

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Download dataset (if not already done)
kaggle datasets download -d alitaqishah/ai-jobs-market-2025-2026-salaries -p data --unzip

# 3. Initialize database
python3 scripts/init_db.py

# 4. Start LLM server (in a separate terminal - see AGENT.md for exact command)
# The server must be running at http://127.0.0.1:8080/v1

# 5. Start web interface
streamlit run app.py
```

## Database Schema

| Table | Rows | Description |
|-------|------|-------------|
| job_postings | 1,500 | Job listings with salary, skills, location |
| job_skills | 9,548 | Normalized skill records |
| job_categories | ~10 | Aggregated stats by category |
| experience_levels | ~8 | Aggregated stats by experience |
| location_summary | ~50 | Aggregated stats by location |

## Project Structure

```
data_agent_project/
├── db/ai_jobs.db                  # SQLite database
├── data/
│   └── ai_jobs_market_2025_2026.csv  # Source dataset
├── scripts/
│   ├── init_db.py                 # Data ingestion (CSV → SQLite)
│   └── data_agent.py              # SQL Agent with fallback
├── app.py                         # Streamlit web UI
├── AGENT.md                       # LLM server config (user-managed)
├── requirements.txt               # Dependencies
├── PROJECT_PLAN.md                # Architecture docs
└── README.md                      # This file
```

## Agent Architecture

1. **SQL Generation**: LLM converts natural language to SQL using database schema
2. **Execution**: SQL executed against SQLite
3. **Fallback**: If SQL fails, retry with error context (up to 3 attempts)
4. **Visualization**: Auto-detect chart type (bar/pie/line) based on query
5. **Summary**: LLM generates natural language explanation

## Configuration

Environment variables:
- `LLM_BASE_URL`: LLM API URL (default: `http://127.0.0.1:8080/v1`)
- `LLM_MODEL`: Model name (default: `local-model`)
- `LLM_API_KEY`: API key (default: `not-needed` for local)

**Note:** The LLM server is managed by the user in a separate terminal. See `AGENT.md` for startup command.

## License

Apache-2.0
