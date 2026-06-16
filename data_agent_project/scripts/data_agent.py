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

SCHEMA_HINT = """You have these SQLite tables:

job_postings(job_id TEXT PRIMARY KEY, job_title TEXT, job_category TEXT, experience_level TEXT,
  years_of_experience INTEGER, education_required TEXT, annual_salary_usd INTEGER,
  salary_min_usd INTEGER, salary_max_usd INTEGER, city TEXT, country TEXT,
  remote_work TEXT, company_size TEXT, industry TEXT, required_skills TEXT,
  ai_salary_premium_pct REAL, demand_score INTEGER, demand_growth_yoy_pct REAL,
  benefits_score_10 REAL, posting_year INTEGER, posting_month INTEGER,
  is_senior INTEGER, is_remote_friendly INTEGER, is_llm_role INTEGER, salary_tier TEXT)

job_skills(id INTEGER PRIMARY KEY, job_id TEXT, skill TEXT)

job_categories(category TEXT, job_count INTEGER, avg_salary REAL, avg_demand_score REAL)

experience_levels(level TEXT, job_count INTEGER, avg_salary REAL, avg_years_experience REAL)

location_summary(country TEXT, city TEXT, job_count INTEGER, avg_salary REAL)"""

SQL_RULES = """SECURITY: You are FORBIDDEN from generating CREATE TABLE, DROP TABLE, ALTER TABLE, INSERT, UPDATE, or DELETE. Output ONLY SELECT queries. The database must remain 100% Read-Only.

ADVANCED SQL RULES:

1. MANDATORY CTE FOR DYNAMIC FEATURES: If the user asks for a categorization, grouping, or flag that does not exist in the base tables (e.g., classifying "Senior" vs "Junior" based on years_of_experience, or grouping specific tech stacks), you MUST use a Common Table Expression (WITH clause) to create a virtual table in memory.

   Template:
   WITH DynamicCategorization AS (
       SELECT *,
           CASE
               WHEN LOWER(required_skills) LIKE '%python%' THEN 'Python Stack'
               ELSE 'Other'
           END AS custom_category
       FROM job_postings
   )
   SELECT custom_category, AVG(annual_salary_usd) FROM DynamicCategorization GROUP BY custom_category;

2. FUZZY TEXT MATCHING: Always use LOWER(column) LIKE LOWER('%keyword%') for text searches instead of exact = matching.

3. SKILL ANALYSIS: JOIN job_postings jp ON jp.job_id = js.job_id with job_skills js. Use GROUP BY with ORDER BY for aggregations.

4. AGGREGATIONS: Use GROUP BY with ORDER BY. annual_salary_usd is in USD. remote_work values: 'On-site', 'Hybrid', 'Fully Remote'.

5. Output ONLY the SQL query, nothing else. No explanation, no markdown, no thinking tags."""


def get_llm():
    return ChatOpenAI(
        model=LLM_MODEL,
        base_url=LLM_BASE_URL,
        api_key=LLM_API_KEY,
        temperature=0,
        max_tokens=512,
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
    return text.strip().rstrip(";")


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
