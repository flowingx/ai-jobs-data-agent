#!/usr/bin/env python3
"""AI Jobs Market Data Analysis Agent - LangChain SQL Agent with multi-query fallback."""

import json
import os
import sqlite3
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv
load_dotenv(Path(__file__).parent.parent / ".env")

from scripts.llm_utils import (
    clean_llm_output,
    extract_sql,
    get_llm,
    generate_sql_with_llm,
    summarize_with_llm,
)

DB_PATH = Path(__file__).parent.parent / "db" / "ai_jobs.db"

MAX_RETRIES = 3


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
