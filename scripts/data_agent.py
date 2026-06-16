#!/usr/bin/env python3
"""AI Jobs Market Data Analysis Agent - LangChain SQL Agent with multi-query fallback."""

import json
import os
import re
import sqlite3
import sys
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv
load_dotenv(Path(__file__).parent.parent / ".env")

from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage

DB_PATH = Path(__file__).parent.parent / "db" / "ai_jobs.db"

MAX_RETRIES = 3

SCHEMA_HINT = """Tables and columns:

job_postings: job_id, job_title, job_category, experience_level, years_of_experience, education_required, annual_salary_usd, salary_min_usd, salary_max_usd, city, country, remote_work, company_size, industry, required_skills, ai_salary_premium_pct, demand_score, demand_growth_yoy_pct, benefits_score_10, posting_year, posting_month, is_senior, is_remote_friendly, is_llm_role, salary_tier

job_skills: id, job_id, skill

job_categories: category, job_count, avg_salary, avg_demand_score

experience_levels: level, job_count, avg_salary, avg_years_experience

location_summary: country, city, job_count, avg_salary"""

SQL_RULES = """RULES:
- SELECT only. No CREATE/DROP/ALTER/INSERT/UPDATE/DELETE.
- Use WITH CTE for dynamic categorization/grouping.
- Use LOWER(col) LIKE LOWER('%keyword%') for text search.
- JOIN job_skills js ON jp.job_id = js.job_id for skill analysis.
- Use English aliases for columns (AS "English Label") so chart labels are readable.
- Keep SQL SHORT. Max 30 lines. Use simple WHERE conditions, not 100+ OR chains.
- Do NOT include comments or explanations. Output ONLY the SQL query.
- Do NOT wrap in markdown code blocks."""


def get_llm(engine: str = "deepseek"):
    if engine == "deepseek":
        return ChatOpenAI(
            model=os.getenv("DEEPSEEK_MODEL", "deepseek-chat"),
            base_url=os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com"),
            api_key=os.getenv("DEEPSEEK_API_KEY", ""),
            temperature=0,
            max_tokens=4096,
        )
    else:
        return ChatOpenAI(
            model=os.getenv("LOCAL_MODEL", "local-model"),
            base_url=os.getenv("LOCAL_LLM_URL", "http://127.0.0.1:8080/v1"),
            api_key="not-needed",
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


MAX_SQL_LENGTH = 2000


def clean_llm_output(text: str) -> str:
    text = re.sub(r'<think>.*?</think>', '', text, flags=re.DOTALL)
    text = re.sub(r'<think>.*', '', text, flags=re.DOTALL)
    text = re.sub(r'.*</think>', '', text, flags=re.DOTALL)
    return text.strip()


def extract_sql(text: str) -> str:
    text = clean_llm_output(text)
    # Try to extract from markdown code block
    m = re.search(r'```(?:sql)?\s*\n?(.*?)```', text, re.DOTALL)
    if m:
        text = m.group(1)
    else:
        # No closing fence — take from first SQL keyword to end
        m2 = re.search(r'(WITH\s|SELECT\s)', text, re.IGNORECASE)
        if m2:
            text = text[m2.start():]
    # Strip comments
    text = re.sub(r'--[^\n]*', '', text)
    text = re.sub(r'/\*.*?\*/', '', text, flags=re.DOTALL)
    # Truncate if too long
    if len(text) > MAX_SQL_LENGTH:
        text = text[:MAX_SQL_LENGTH]
    return text.strip().rstrip(";")


def generate_sql_with_llm(llm, question: str, error_hint: str = "") -> str:
    error_section = f"\nPrevious SQL failed: {error_hint}\nGenerate a DIFFERENT valid SQL query." if error_hint else ""
    messages = [
        SystemMessage(content=f"You are a SQLite expert.\n\n{SCHEMA_HINT}\n\n{SQL_RULES}\n{error_section}"),
        HumanMessage(content=f"Question: {question}")
    ]
    response = llm.invoke(messages)
    raw = response.content if hasattr(response, "content") else str(response)
    return extract_sql(raw)


def summarize_with_llm(llm, question: str, sql: str, columns: list, rows: list) -> str:
    rows_sample = rows[:15]
    messages = [
        SystemMessage(content="Summarize the SQL results in 1-2 sentences. Be concise."),
        HumanMessage(content=f"Question: {question}\nSQL: {sql}\nColumns: {columns}\nResults: {json.dumps(rows_sample, default=str, ensure_ascii=False)}")
    ]
    response = llm.invoke(messages)
    raw = response.content if hasattr(response, "content") else str(response)
    return clean_llm_output(raw)


def query_agent(question: str, engine: str = "deepseek", verbose: bool = True) -> dict:
    llm = get_llm(engine)
    result = {"question": question, "sql": None, "columns": [], "rows": [], "error": None, "answer": None, "retries": 0}
    error_hint = ""

    for attempt in range(MAX_RETRIES):
        sql = generate_sql_with_llm(llm, question, error_hint)
        result["sql"] = sql
        result["retries"] = attempt
        if verbose:
            print(f"[{attempt+1}] SQL: {sql}")

        columns, rows, error = execute_sql(sql) if sql else ([], [], "Empty SQL")
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
    parser.add_argument("--engine", "-e", choices=["deepseek", "local"], default="deepseek")
    args = parser.parse_args()

    print("=" * 60)
    print("AI Jobs Market Data Analysis Agent")
    print("=" * 60)

    if args.question:
        result = query_agent(args.question, engine=args.engine)
    elif args.interactive:
        print("Interactive mode. Type 'quit' to exit.")
        while True:
            q = input("\nQuestion: ").strip()
            if q.lower() in ("quit", "exit", "q"):
                break
            if q:
                query_agent(q, engine=args.engine)
    else:
        for q in SAMPLE_QUESTIONS[:2]:
            result = query_agent(q, engine=args.engine)
            print()


if __name__ == "__main__":
    main()
