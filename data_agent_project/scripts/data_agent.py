#!/usr/bin/env python3
"""AI Jobs Market Data Analysis Agent - LangChain SQL Agent with multi-query fallback."""

import json
import os
import re
import sqlite3
import sys
from pathlib import Path
from typing import Optional

from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage

DB_PATH = Path(__file__).parent.parent / "db" / "ai_jobs.db"
LLM_BASE_URL = os.getenv("LLM_BASE_URL", "http://127.0.0.1:8080/v1")
LLM_MODEL = os.getenv("LLM_MODEL", "local-model")
LLM_API_KEY = os.getenv("LLM_API_KEY", "not-needed")

MAX_RETRIES = 3

VALID_COLUMNS = {
    "job_postings": {"job_id", "job_title", "job_category", "experience_level", "years_of_experience", "education_required", "annual_salary_usd", "salary_min_usd", "salary_max_usd", "city", "country", "remote_work", "company_size", "industry", "required_skills", "ai_salary_premium_pct", "demand_score", "demand_growth_yoy_pct", "benefits_score_10", "posting_year", "posting_month", "is_senior", "is_remote_friendly", "is_llm_role", "salary_tier"},
    "job_skills": {"id", "job_id", "skill"},
    "job_categories": {"category", "job_count", "avg_salary", "avg_demand_score"},
    "experience_levels": {"level", "job_count", "avg_salary", "avg_years_experience"},
    "location_summary": {"country", "city", "job_count", "avg_salary"},
}

SCHEMA_HINT = """EXACT COLUMNS YOU CAN USE (no others exist):

job_postings: job_id, job_title, job_category, experience_level, years_of_experience, education_required, annual_salary_usd, salary_min_usd, salary_max_usd, city, country, remote_work, company_size, industry, required_skills, ai_salary_premium_pct, demand_score, demand_growth_yoy_pct, benefits_score_10, posting_year, posting_month, is_senior, is_remote_friendly, is_llm_role, salary_tier

job_skills: id, job_id, skill

job_categories: category, job_count, avg_salary, avg_demand_score

experience_levels: level, job_count, avg_salary, avg_years_experience

location_summary: country, city, job_count, avg_salary"""

SQL_RULES = """SECURITY: You are STRICTLY FORBIDDEN from generating CREATE TABLE, DROP TABLE, ALTER TABLE, INSERT, UPDATE, or DELETE. Output ONLY SELECT queries. The database must remain 100% Read-Only.

ADVANCED SQL RULES:

1. CTE IS REQUIRED (MANDATORY) FOR DYNAMIC FEATURES: Whenever the user asks for a categorization, grouping, or flag that does not exist as a column in the base tables (e.g., classifying "Senior" vs "Junior" based on years_of_experience, or grouping specific tech stacks), you MUST use a Common Table Expression (WITH clause) to create a virtual table in memory. DO NOT skip CTEs for these cases — they are mandatory.

2. CRITICAL CTE SYNTAX RULE: If you use a CTE, you MUST start the query with the WITH keyword, followed by the CTE name, the AS keyword, and an opening parenthesis (. NEVER output a closing parenthesis ) without starting with WITH ... AS (. EXACT TEMPLATE:
   WITH VirtualTableName AS (
       SELECT virtual_col1, virtual_col2 FROM source_table WHERE condition
   )
   SELECT * FROM VirtualTableName;

3. FUZZY TEXT MATCHING: Always use LOWER(column) LIKE LOWER('%keyword%') for text searches instead of exact = matching.

4. SKILL ANALYSIS: JOIN job_postings jp ON jp.job_id = js.job_id with job_skills js. Use GROUP BY with ORDER BY for aggregations.

5. AGGREGATIONS: Use GROUP BY with ORDER BY. annual_salary_usd is in USD. remote_work values: 'On-site', 'Hybrid', 'Fully Remote'.

6. Output ONLY the SQL query, nothing else. No explanation, no markdown, no thinking tags.

7. For non-English questions (Chinese, etc.): Ignore the language of the question. Focus on the MEANING and generate SQL using the English column names from the schema. The database stores English data regardless of the question language."""


def get_llm():
    return ChatOpenAI(
        model=LLM_MODEL,
        base_url=LLM_BASE_URL,
        api_key=LLM_API_KEY,
        temperature=0,
        max_tokens=1024,
    )


def execute_sql(sql: str) -> tuple[list, list, Optional[str]]:
    conn = sqlite3.connect(str(DB_PATH))
    try:
        cursor = conn.execute(sql)
        columns = [desc[0] for desc in cursor.description] if cursor.description else []
        rows = cursor.fetchall()
        return columns, rows, None
    except Exception as e:
        return [], [], str(e)
    finally:
        conn.close()


def clean_llm_output(text: str) -> str:
    """Remove thinking tags and markdown artifacts from LLM output."""
    text = re.sub(r'<think>.*?</think>', '', text, flags=re.DOTALL)
    text = re.sub(r'<think>.*', '', text, flags=re.DOTALL)
    text = re.sub(r'.*</think>', '', text, flags=re.DOTALL)
    return text.strip()


def extract_sql(text: str) -> str:
    """Extract SQL from LLM response."""
    text = clean_llm_output(text)
    # Remove markdown code blocks
    for prefix in ["```sql", "```"]:
        if text.startswith(prefix):
            text = text[len(prefix):]
    if text.endswith("```"):
        text = text[:-3]
    text = text.strip()
    # Take first SELECT statement
    upper = text.upper()
    if "SELECT" in upper:
        idx = upper.index("SELECT")
        text = text[idx:]
        # Find end of statement
        for end in [";", "\n\n", "\n--"]:
            end_idx = text.find(end)
            if end_idx > 0:
                text = text[:end_idx]
                break
    text = text.strip().rstrip(";")
    # Validate CTE syntax: if ) appears without WITH ... AS (, fix it
    if ")" in text and "WITH" not in text.upper():
        text = text.split(")")[0].strip()
    # Truncation guard: if SQL ends mid-expression, return empty
    if text:
        stripped = text.rstrip()
        # Check for incomplete expressions
        incomplete_indicators = (
            not stripped.endswith(";") and
            not stripped.endswith(")") and
            not stripped.endswith("'") and
            not stripped.endswith('"')
        )
        if incomplete_indicators:
            last_token = stripped.split()[-1].upper() if stripped.split() else ""
            # Ends with operator/keyword with nothing after
            if last_token in ("LIKE", "AND", "OR", "ON", "WHERE", "SET", "VALUES", "THEN", "ELSE", "WHEN", "IN", "BETWEEN", "IS", "AS"):
                text = ""
            # Ends with table.column (e.g. jp.required_skills) — missing operator
            elif re.match(r'\w+\.\w+$', stripped):
                text = ""
            # Ends with just a column name — missing operator
            elif re.match(r'^\w+$', stripped) and stripped.upper() not in ("SELECT", "FROM", "WHERE", "AND", "OR", "ON", "GROUP", "ORDER", "LIMIT", "HAVING", "AS", "CASE", "WHEN", "THEN", "ELSE", "END", "DISTINCT", "JOIN", "LEFT", "RIGHT", "INNER", "OUTER", "UNION", "ALL", "EXISTS", "NOT", "IN", "LIKE", "BETWEEN", "IS", "NULL", "TRUE", "FALSE"):
                text = ""
    return text


def validate_sql_columns(sql: str):
    """Reject SQL with columns that don't exist in the schema."""
    import re as _re
    refs = _re.findall(r'(\w+)\.(\w+)', sql)
    for table, col in refs:
        table_lower = table.lower()
        col_lower = col.lower()
        if table_lower in VALID_COLUMNS and col_lower not in VALID_COLUMNS[table_lower]:
            return f"Column '{col}' does not exist in table '{table}'"
    return None


def generate_sql_with_llm(llm, question: str, error_hint: str = "") -> str:
    error_section = f"\nPrevious SQL failed: {error_hint}\nGenerate a DIFFERENT valid SQL query." if error_hint else ""
    messages = [
        SystemMessage(content=f"""You are a SQLite expert.

{SCHEMA_HINT}

{SQL_RULES}
{error_section}"""),
        HumanMessage(content=f"Question: {question}")
    ]
    response = llm.invoke(messages)
    raw = response.content if hasattr(response, "content") else str(response)
    return extract_sql(raw)


def summarize_with_llm(llm, question: str, sql: str, columns: list, rows: list) -> str:
    rows_sample = rows[:15]
    messages = [
        SystemMessage(content="Summarize the SQL results in 1-2 sentences. Be concise. No thinking tags."),
        HumanMessage(content=f"Question: {question}\nSQL: {sql}\nColumns: {columns}\nResults: {json.dumps(rows_sample, default=str, ensure_ascii=False)}")
    ]
    response = llm.invoke(messages)
    raw = response.content if hasattr(response, "content") else str(response)
    return clean_llm_output(raw)


def query_agent(question: str, verbose: bool = True) -> dict:
    llm = get_llm()
    result = {"question": question, "sql": None, "columns": [], "rows": [], "error": None, "answer": None, "retries": 0}
    error_hint = ""

    for attempt in range(MAX_RETRIES):
        sql = generate_sql_with_llm(llm, question, error_hint)
        result["sql"] = sql
        result["retries"] = attempt
        if verbose:
            print(f"[{attempt+1}] SQL: {sql}")

        # Validate columns before execution
        col_error = validate_sql_columns(sql) if sql else "Empty SQL"
        if col_error:
            if verbose:
                print(f"    Validation: {col_error}")
            error_hint = col_error
            result["error"] = col_error
            continue

        columns, rows, error = execute_sql(sql)
        if error:
            if verbose:
                print(f"    Error: {error}")
            error_hint = error
            result["error"] = error
            continue

        result["columns"] = columns
        result["rows"] = rows
        result["error"] = None
        if rows:
            result["answer"] = summarize_with_llm(llm, question, sql, columns, rows)
            if verbose:
                print(f"    Answer: {result['answer']}")
        return result

    result["answer"] = f"Failed after {MAX_RETRIES} attempts."
    return result


SAMPLE_QUESTIONS = [
    "What is the average salary for remote vs on-site AI jobs?",
    "Which skills appear most frequently in job postings?",
    "What are the top 5 job categories by demand score?",
    "How does salary vary by experience level?",
    "Which cities have the most AI job openings?",
]


def main():
    import argparse
    parser = argparse.ArgumentParser(description="AI Jobs Market Data Analysis Agent")
    parser.add_argument("--question", "-q", type=str)
    parser.add_argument("--interactive", "-i", action="store_true")
    args = parser.parse_args()

    print("=" * 60)
    print("AI Jobs Market Data Analysis Agent")
    print("=" * 60)

    if args.question:
        result = query_agent(args.question)
    elif args.interactive:
        print("Interactive mode. Type 'quit' to exit.")
        while True:
            q = input("\nQuestion: ").strip()
            if q.lower() in ("quit", "exit", "q"):
                break
            if q:
                query_agent(q)
    else:
        for q in SAMPLE_QUESTIONS[:2]:
            result = query_agent(q)
            print()


if __name__ == "__main__":
    main()
