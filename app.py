#!/usr/bin/env python3
"""AI Jobs Market Data Analysis Agent - Streamlit Web UI with Visualization."""

import json
import os
import re
import sqlite3
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv
load_dotenv(Path(__file__).parent / ".env")

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
import streamlit as st
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage

DB_PATH = Path(__file__).parent / "db" / "ai_jobs.db"

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
- For skill search: use `js.skill = 'python'` or `js.skill LIKE '%python%'`, not OR chains.
- For job category: use `job_category = 'AI'`, not OR chains matching title words.
- Use English column aliases (AS "Label") for chart readability.
- NEVER repeat the same pattern with different values. Use a subquery or IN clause instead."""

SAMPLE_QUESTIONS = {
    "Salary Analysis": [
        "What is the average salary for remote vs on-site AI jobs?",
        "How does salary vary by experience level?",
        "What is the salary range for Senior AI Engineer positions?",
        "What is the average salary premium for AI roles by industry?",
    ],
    "Skill Demand": [
        "Which skills appear most frequently in job postings?",
        "How many jobs require Python skills?",
        "What are the most in-demand AI skills?",
    ],
    "Job Market Overview": [
        "What are the top 5 job categories by demand score?",
        "Which cities have the most AI job openings?",
        "What percentage of jobs are LLM-related roles?",
        "How many total job postings are there?",
    ],
}


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


def get_table_info() -> dict:
    info = {}
    with sqlite3.connect(str(DB_PATH)) as conn:
        cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
        for row in cursor.fetchall():
            count = conn.execute(f"SELECT COUNT(*) FROM [{row[0]}]").fetchone()[0]
            info[row[0]] = count
    return info


def get_table_dataframe(table_name: str, limit: int = 100) -> pd.DataFrame:
    with sqlite3.connect(str(DB_PATH)) as conn:
        return pd.read_sql_query(f"SELECT * FROM [{table_name}] LIMIT {limit}", conn)


MAX_SQL_LENGTH = 1500
MAX_OR_CHAINS = 10


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
    # Count OR chains — if too many, the LLM is hallucinating
    or_count = len(re.findall(r'\bOR\b', text, re.IGNORECASE))
    if or_count > MAX_OR_CHAINS:
        # Truncate at the Nth OR and close the WHERE clause
        parts = re.split(r'\bOR\b', text, flags=re.IGNORECASE)
        if len(parts) > MAX_OR_CHAINS:
            text = " OR ".join(parts[:MAX_OR_CHAINS])
            # Try to close the WHERE clause
            if "WHERE" in text.upper():
                text += "\n    LIMIT 50"
    # Truncate if too long
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
    messages = [
        SystemMessage(content="Summarize the SQL results in 1-2 sentences. Be concise."),
        HumanMessage(content=f"Question: {question}\nSQL: {sql}\nColumns: {columns}\nResults: {json.dumps(rows_sample, default=str, ensure_ascii=False)}")
    ]
    response = llm.invoke(messages)
    log_usage("Summary", response)
    raw = response.content if hasattr(response, "content") else str(response)
    return clean_llm_output(raw)


def auto_detect_chart(sql: str, columns: list, rows: list) -> str:
    sql_upper = sql.upper()

    # Time series: year/month columns with aggregate → line
    if any(kw in sql_upper for kw in ["YEAR", "MONTH", "POSTING_YEAR", "POSTING_MONTH"]):
        if any(fn in sql_upper for fn in ["AVG", "SUM", "COUNT", "MIN", "MAX"]):
            return "line"

    # Two numeric columns → scatter
    if len(columns) >= 2:
        numeric_count = 0
        for row in rows[:20]:
            if row and len(row) >= 2:
                try:
                    float(row[0])
                    float(row[1])
                    numeric_count += 1
                except (ValueError, TypeError):
                    pass
        if numeric_count >= len(rows[:20]) * 0.8 and len(rows) >= 5:
            return "scatter"

    # GROUP BY with COUNT and few categories → pie
    if "GROUP BY" in sql_upper and "COUNT" in sql_upper:
        if len(rows) <= 8:
            return "pie"
        return "bar"

    # Aggregate functions → bar
    if any(fn in sql_upper for fn in ["AVG", "SUM", "MIN", "MAX"]):
        return "bar"

    # ORDER BY with limited rows → bar
    if "ORDER BY" in sql_upper and len(rows) <= 20:
        return "bar"

    # Default: if 2+ columns with text + numeric, use bar
    if len(columns) >= 2 and len(rows) <= 30:
        return "bar"

    return None


def make_chart_title(sql: str, columns: list) -> str:
    sql_upper = sql.upper()
    if len(columns) >= 2:
        y_col = columns[1]
        if "GROUP BY" in sql_upper:
            return f"{y_col} by {columns[0]}"
        if "ORDER BY" in sql_upper:
            return f"{y_col} ranked by {columns[0]}"
        return f"{y_col} vs {columns[0]}"
    return columns[0] if columns else "Query Results"


def render_chart(chart_type: str, columns: list, rows: list, title: str, sql: str = ""):
    if not rows or not columns:
        return
    plt.rcParams["font.sans-serif"] = ["SimHei", "Microsoft YaHei", "WenQuanYi Micro Hei", "DejaVu Sans"]
    plt.rcParams["axes.unicode_minus"] = False
    df = pd.DataFrame(rows, columns=columns)

    fig = None

    if chart_type == "bar" and len(columns) >= 2:
        fig, ax = plt.subplots(figsize=(10, max(4, len(rows) * 0.4)))
        x_col, y_col = columns[0], columns[1]
        try:
            df[y_col] = pd.to_numeric(df[y_col])
        except (ValueError, TypeError):
            pass
        d = df.head(25).copy()
        d[x_col] = d[x_col].astype(str).str[:30]
        colors = plt.cm.viridis([i / len(d) for i in range(len(d))])
        ax.barh(d[x_col], d[y_col], color=colors)
        ax.set_xlabel(y_col, fontsize=10)
        ax.set_title(title, fontsize=12, fontweight="bold")
        ax.invert_yaxis()
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)

    elif chart_type == "pie" and len(columns) >= 2:
        fig, ax = plt.subplots(figsize=(8, 8))
        x_col, y_col = columns[0], columns[1]
        try:
            df[y_col] = pd.to_numeric(df[y_col])
        except (ValueError, TypeError):
            pass
        d = df.head(10).copy()
        colors = plt.cm.Set3([i / len(d) for i in range(len(d))])
        wedges, texts, autotexts = ax.pie(
            d[y_col], labels=d[x_col], autopct="%1.1f%%",
            startangle=90, colors=colors, pctdistance=0.85
        )
        for text in texts:
            text.set_fontsize(9)
        for autotext in autotexts:
            autotext.set_fontsize(8)
        ax.set_title(title, fontsize=12, fontweight="bold", pad=20)

    elif chart_type == "line" and len(columns) >= 2:
        fig, ax = plt.subplots(figsize=(10, 5))
        x_col, y_col = columns[0], columns[1]
        try:
            df[y_col] = pd.to_numeric(df[y_col])
        except (ValueError, TypeError):
            pass
        d = df.head(30).copy()
        d[x_col] = d[x_col].astype(str).str[:20]
        ax.plot(d[x_col], d[y_col], marker="o", linewidth=2, markersize=6, color="#4C78A8")
        ax.fill_between(range(len(d)), d[y_col], alpha=0.1, color="#4C78A8")
        ax.set_xlabel(x_col, fontsize=10)
        ax.set_ylabel(y_col, fontsize=10)
        ax.set_title(title, fontsize=12, fontweight="bold")
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        plt.xticks(rotation=45, ha="right")

    elif chart_type == "scatter" and len(columns) >= 2:
        fig, ax = plt.subplots(figsize=(8, 6))
        x_col, y_col = columns[0], columns[1]
        try:
            df[x_col] = pd.to_numeric(df[x_col])
            df[y_col] = pd.to_numeric(df[y_col])
        except (ValueError, TypeError):
            pass
        d = df.head(50).copy()
        ax.scatter(d[x_col], d[y_col], alpha=0.6, s=50, c="#4C78A8", edgecolors="white", linewidth=0.5)
        ax.set_xlabel(x_col, fontsize=10)
        ax.set_ylabel(y_col, fontsize=10)
        ax.set_title(title, fontsize=12, fontweight="bold")
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)

    if fig:
        plt.tight_layout()
        st.pyplot(fig)
        plt.close(fig)


def main():
    st.set_page_config(page_title="AI Jobs Market Analysis Agent", page_icon="chart_with_upwards_trend", layout="wide")
    st.title("AI Jobs Market Data Analysis Agent")
    st.markdown("Natural language analysis of 2025-2026 AI job market data using LangChain + SQLite + LLM")

    with st.sidebar:
        st.header("LLM Engine")
        engine = st.radio("Select engine:", ["DeepSeek (Cloud)", "Local GPU (llama.cpp)"], index=0)
        engine_key = "deepseek" if "DeepSeek" in engine else "local"

        if engine_key == "deepseek":
            api_key = st.text_input("DeepSeek API Key", value=os.getenv("DEEPSEEK_API_KEY", ""), type="password")
            if api_key:
                os.environ["DEEPSEEK_API_KEY"] = api_key
            st.caption("Default: deepseek-chat via api.deepseek.com")
        else:
            local_url = st.text_input("Local LLM URL", value=os.getenv("LOCAL_LLM_URL", "http://127.0.0.1:8080/v1"))
            st.caption("Ensure local llama-server is running (see AGENT.md)")

        st.divider()
        st.header("Database Overview")
        if DB_PATH.exists():
            for table, count in get_table_info().items():
                st.metric(table, f"{count:,} rows")
        else:
            st.error("Database not found. Run: `python3 scripts/init_db.py`")

    tab1, tab2, tab3 = st.tabs(["Smart Query", "Data Browser", "Preset Analysis"])

    with tab1:
        st.subheader("Natural Language Query")
        with st.form("query_form", clear_on_submit=False):
            question = st.text_input("Enter your question:", placeholder="e.g., What is the average salary for remote vs on-site AI jobs?")
            submitted = st.form_submit_button("Search", type="primary")

        if submitted and not question:
            st.warning("Please enter a question before searching.")

        if submitted and question:
            status = st.status(f"Analyzing with {engine}...", expanded=True)
            try:
                llm = get_llm(engine_key)
                sql, columns, rows, error = None, [], [], None
                for attempt in range(3):
                    error_hint = f"\nPrevious SQL failed: {error}\nGenerate a DIFFERENT valid SQL query." if error else ""
                    sql = generate_sql_with_llm(llm, question, error_hint)
                    columns, rows, error = execute_sql(sql) if sql else ([], [], "Empty SQL generated")
                    if not error:
                        break

                if error:
                    status.update(label="Query failed", state="error")
                    st.error(f"SQL Error: {error}")
                    if sql:
                        st.code(sql, language="sql")
                else:
                    status.update(label="Query complete", state="complete")
                    st.code(sql, language="sql")
                    df = pd.DataFrame(rows, columns=columns)
                    st.dataframe(df, use_container_width=True)
                    chart_type = auto_detect_chart(sql, columns, rows)
                    if chart_type and rows:
                        st.subheader("Visualization")
                        render_chart(chart_type, columns, rows, make_chart_title(sql, columns), sql)
                    if rows:
                        st.subheader("AI Summary")
                        st.markdown(summarize_with_llm(llm, question, sql, columns, rows))
            except Exception as e:
                status.update(label="Error", state="error")
                st.error(f"Error: {str(e)}")
                if engine_key == "local":
                    st.info("Ensure the local LLM server is running (see AGENT.md)")
                else:
                    st.info("Check your DeepSeek API key and network connection")

    with tab2:
        st.subheader("Data Browser")
        if DB_PATH.exists():
            tables = list(get_table_info().keys())
            selected = st.selectbox("Select table", tables)
            if selected:
                df = get_table_dataframe(selected, limit=200)
                st.dataframe(df, use_container_width=True)
                st.caption(f"Showing up to 200 of {get_table_info()[selected]:,} rows")

    with tab3:
        st.subheader("Preset Analysis Scenarios")
        for category, questions in SAMPLE_QUESTIONS.items():
            with st.expander(f"{category}", expanded=False):
                for q in questions:
                    if st.button(q, key=f"preset_{q}"):
                        with st.spinner("Querying..."):
                            try:
                                llm = get_llm(engine_key)
                                sql = generate_sql_with_llm(llm, q)
                                columns, rows, error = execute_sql(sql)
                                if not error and rows:
                                    st.markdown(f"**Question:** {q}")
                                    st.code(sql, language="sql")
                                    st.dataframe(pd.DataFrame(rows, columns=columns), use_container_width=True)
                                    chart_type = auto_detect_chart(sql, columns, rows)
                                    if chart_type:
                                        render_chart(chart_type, columns, rows, make_chart_title(sql, columns), sql)
                                    st.markdown(f"**Answer:** {summarize_with_llm(llm, q, sql, columns, rows)}")
                                else:
                                    st.error(f"Error: {error}" if error else "No results")
                            except Exception as e:
                                st.error(f"Error: {str(e)}")


if __name__ == "__main__":
    main()
