# AGENT.md - Technical Developer Documentation

## Architecture

```
User Question → LLM SQL Generation → SQLite Execution → Results + Visualization
     ↓                                        ↓
  (Fallback: retry with error context)    (Charts: bar/pie/line/scatter)
     ↓                                        ↓
  Natural Language Summary ←────────────── Query Results
```

## Dual-Engine Setup

| Engine | Default | Max Tokens | API Key Required |
|--------|---------|------------|------------------|
| DeepSeek (Cloud) | Yes | 1024 | Yes |
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

## Data Pipeline

1. **Source**: `data/ai_jobs_market_2025_2026.csv` (1,500 rows from Kaggle)
2. **Ingestion**: `scripts/init_db.py` → `db/ai_jobs.db`
3. **Query**: `scripts/data_agent.py` or `app.py`

## Agent Logic

- **SQL Generation**: LLM converts natural language to SQL using schema context
- **Multi-query Fallback**: Retries up to 3 times with error context
- **Visualization**: Auto-detects chart type from SQL patterns
- **Summary**: LLM generates natural language explanation
- **Token Logging**: Each LLM call prints token usage in terminal

## SQL Rules (sent to LLM)

```
- Output ONLY the SQL query. No explanations, no comments, no markdown.
- SELECT only. No CREATE/DROP/ALTER/INSERT/UPDATE/DELETE.
- Max 15 lines of SQL. Use simple WHERE, never 100+ OR chains.
- Always use LOWER() for case-insensitive search.
- Skill search: LOWER(js.skill) LIKE LOWER('%python%') or LOWER(required_skills) LIKE LOWER('%python%').
- Job category: LOWER(job_category) LIKE LOWER('%ai%').
- Use English column aliases (AS "Label") for chart readability.
```

## Anti-Hallucination Measures

- **max_tokens=1024**: Limits LLM output length
- **OR chain counter**: If >10 OR conditions, auto-truncate
- **SQL length limit**: Max 1500 characters
- **Markdown fence stripping**: Handles ```sql blocks
- **Comment stripping**: Removes -- and /* */ comments

## Data Format

| Table | Field | Format | Search Pattern |
|-------|-------|--------|----------------|
| job_skills | skill | Individual rows | `LOWER(skill) LIKE LOWER('%python%')` |
| job_postings | required_skills | Pipe-delimited (`Python\|SQL\|Cloud`) | `LOWER(required_skills) LIKE LOWER('%python%')` |

## Chart Types

| Type | Trigger | Visual |
|------|---------|--------|
| bar | GROUP BY / ORDER BY / aggregate | Horizontal bar chart |
| pie | GROUP BY + ≤8 categories | Pie chart |
| line | Year/month columns + aggregate | Line chart with fill |
| scatter | Two numeric columns | Scatter plot |

## Preset Queries (bypass LLM)

8 pre-built queries in `EXAMPLE_QUERIES` list that execute SQL directly without LLM:

1. Top 10 skills by job count
2. Average salary by experience level
3. Job count by category
4. Remote vs On-site jobs
5. Top 10 cities by job postings
6. Salary distribution by job category
7. Jobs by posting year
8. LLM vs non-LLM salary comparison

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
