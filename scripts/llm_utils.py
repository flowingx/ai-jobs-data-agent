"""Shared LLM and SQL utilities used by both app.py and scripts/data_agent.py."""

import os
import re
from typing import Optional

from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage

SCHEMA_HINT = """Tables and columns:

job_postings: job_id, job_title, job_category, experience_level, years_of_experience, education_required, annual_salary_usd, salary_min_usd, salary_max_usd, city, country, remote_work, company_size, industry, required_skills, ai_salary_premium_pct, demand_score, demand_growth_yoy_pct, benefits_score_10, posting_year, posting_month, is_senior, is_remote_friendly, is_llm_role, salary_tier

job_skills: id, job_id, skill

job_categories: category, job_count, avg_salary, avg_demand_score

experience_levels: level, job_count, avg_salary, avg_years_experience

location_summary: country, city, job_count, avg_salary"""

SQL_RULES = """CRITICAL RULES:
- Output ONLY the SQL query. No explanations, no comments, no markdown.
- SELECT only. No CREATE/DROP/ALTER/INSERT/UPDATE/DELETE.
- Max 15 lines of SQL. Use simple WHERE, never 100+ OR chains.
- Always use LOWER() for case-insensitive search: LOWER(col) LIKE LOWER('%keyword%').
- Skill search: LOWER(js.skill) LIKE LOWER('%python%') or LOWER(required_skills) LIKE LOWER('%python%').
- Use English column aliases (AS "Label") for chart readability.
- CRITICAL: When user asks about trends, popularity, or technology comparisons (e.g., 'Is X still popular?', 'Compare X and Y'), the generated SQL MUST use GROUP BY to break down the metrics by temporal or categorical dimensions (such as posting_year, experience_level, or specific technology keywords using CASE WHEN or LIKE). NEVER return a single aggregated value or single row for comparison queries."""

MAX_SQL_LENGTH = 1500
MAX_OR_CHAINS = 10


def clean_llm_output(text: str) -> str:
    text = re.sub(r'<think>.*?</think>', '', text, flags=re.DOTALL)
    text = re.sub(r'<think>.*', '', text, flags=re.DOTALL)
    text = re.sub(r'.*</think>', '', text, flags=re.DOTALL)
    return text.strip()


def extract_sql(text: str) -> str:
    text = clean_llm_output(text)
    m = re.search(r'```(?:sql)?\s*\n?(.*?)```', text, re.DOTALL)
    if m:
        text = m.group(1)
    else:
        m2 = re.search(r'(WITH\s|SELECT\s)', text, re.IGNORECASE)
        if m2:
            text = text[m2.start():]
    text = re.sub(r'--[^\n]*', '', text)
    text = re.sub(r'/\*.*?\*/', '', text, flags=re.DOTALL)
    or_count = len(re.findall(r'\bOR\b', text, re.IGNORECASE))
    if or_count > MAX_OR_CHAINS:
        parts = re.split(r'\bOR\b', text, flags=re.IGNORECASE)
        if len(parts) > MAX_OR_CHAINS:
            text = " OR ".join(parts[:MAX_OR_CHAINS])
            if "WHERE" in text.upper():
                text += "\n    LIMIT 50"
    if len(text) > MAX_SQL_LENGTH:
        text = text[:MAX_SQL_LENGTH]
    return text.strip().rstrip(";")


def log_usage(tag: str, response):
    usage = getattr(response, "usage_metadata", None)
    if usage:
        inp = usage.get("input_tokens", 0) or 0
        out = usage.get("output_tokens", 0) or 0
        total = usage.get("total_tokens", 0) or (inp + out)
        print(f"  [{tag}] tokens: in={inp} out={out} total={total}")


def get_llm(engine: str = "deepseek"):
    if engine == "deepseek":
        return ChatOpenAI(
            model=os.getenv("DEEPSEEK_MODEL", "deepseek-chat"),
            base_url=os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com"),
            api_key=os.getenv("DEEPSEEK_API_KEY", ""),
            temperature=0,
            max_tokens=1024,
        )
    else:
        return ChatOpenAI(
            model=os.getenv("LOCAL_MODEL", "local-model"),
            base_url=os.getenv("LOCAL_LLM_URL", "http://127.0.0.1:8080/v1"),
            api_key="not-needed",
            temperature=0,
            max_tokens=1024,
        )


def generate_sql_with_llm(llm, question: str, error_hint: str = "") -> str:
    error_section = f"\nPrevious SQL failed: {error_hint}\nGenerate a DIFFERENT valid SQL query." if error_hint else ""
    messages = [
        SystemMessage(content=f"You are a SQLite expert.\n\n{SCHEMA_HINT}\n\n{SQL_RULES}\n{error_section}"),
        HumanMessage(content=f"Question: {question}")
    ]
    response = llm.invoke(messages)
    log_usage("SQL", response)
    raw = response.content if hasattr(response, "content") else str(response)
    return extract_sql(raw)


def summarize_with_llm(llm, question: str, sql: str, columns: list, rows: list) -> str:
    rows_sample = rows[:15]
    import json
    messages = [
        SystemMessage(content="请用中文对以下数据进行简明扼要的商业分析总结。CRITICAL: You MUST write the entire summary in Chinese (中文). Never output the analysis in English. Do not use any backticks (`) or inline code syntax for numbers or financial figures. Return numbers as plain text (e.g., 212782 or 212,782) without any Markdown highlighting."),
        HumanMessage(content=f"Question: {question}\nSQL: {sql}\nColumns: {columns}\nResults: {json.dumps(rows_sample, default=str, ensure_ascii=False)}")
    ]
    response = llm.invoke(messages)
    log_usage("Summary", response)
    raw = response.content if hasattr(response, "content") else str(response)
    summary_text = clean_llm_output(raw)
    summary_text = summary_text.replace("`", "")
    return summary_text
