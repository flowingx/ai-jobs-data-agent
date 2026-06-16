# AI Jobs Market Data Analysis Agent - Project Plan

## Overview
A real-world AI job market data analysis agent built on LangChain + SQLite + Qwen3-4B (local LLM). Natural language queries are converted to SQL and executed against a SQLite database of 1,500 AI job postings from the 2025-2026 market.

## Architecture
```
User Question → LLM SQL Generation → SQLite Execution → Results + Visualization
     ↓                                        ↓
  (Fallback: retry with error context)    (Charts: bar/pie/line)
     ↓                                        ↓
  Natural Language Summary ←────────────── Query Results
```

## Components
1. **Data Ingestion** (`scripts/init_db.py`): Loads CSV into SQLite with normalized tables
2. **SQL Agent** (`scripts/data_agent.py`): LLM-powered SQL generation with multi-query fallback
3. **Visualization** (`app.py`): Auto-detected charts (bar/pie/line) based on query results
4. **Web UI** (`app.py`): Streamlit app with smart query, data browser, and preset analyses

## Database Schema (5 tables)
| Table | Rows | Description |
|-------|------|-------------|
| job_postings | 1,500 | Main job listings with salary, skills, location |
| job_skills | 9,548 | Normalized skill records (one per skill per job) |
| job_categories | ~10 | Aggregated stats by job category |
| experience_levels | ~8 | Aggregated stats by experience level |
| location_summary | ~50 | Aggregated stats by country/city |

## Tech Stack
- Python 3.10, pandas, sqlite3
- LangChain + ChatOpenAI (local llama.cpp endpoint at http://127.0.0.1:8080/v1)
- matplotlib for visualization
- Streamlit for web UI

## Dataset
- **Source**: Kaggle - `alitaqishah/ai-jobs-market-2025-2026-salaries`
- **Size**: 1,500 rows, 25 columns
- **Domain**: AI/ML job postings with salary, skills, experience, location data

## Key Features
- Multi-query fallback: retries SQL generation up to 3 times with error context
- Auto chart detection: bar, pie, or line charts based on query structure
- Skill analysis: JOIN queries for skill frequency and demand analysis
- Natural language summaries: LLM generates explanations of query results

## Status
- [x] Data ingestion and database creation
- [x] LangChain SQL Agent with fallback
- [x] Streamlit web UI with visualization
- [x] LLM server launcher script
