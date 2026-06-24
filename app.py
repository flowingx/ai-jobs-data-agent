#!/usr/bin/env python3
"""AI 岗位市场数据分析智能体 - Streamlit Web UI 与可视化。"""

import json
import os
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

from scripts.llm_utils import (
    get_llm,
    generate_sql_with_llm,
    summarize_with_llm,
    validate_readonly_sql,
)

DB_PATH = Path(__file__).parent / "db" / "ai_jobs.db"

SAMPLE_QUESTIONS = {
    "薪资分析": [
        "远程与现场 AI 岗位的平均薪资分别是多少？",
        "不同经验级别的薪资有什么差异？",
        "Senior AI Engineer 岗位的薪资范围是多少？",
        "不同行业的 AI 岗位平均薪资溢价是多少？",
    ],
    "技能需求": [
        "岗位描述中出现频率最高的技能有哪些？",
        "有多少岗位要求 Python 技能？",
        "当前需求最高的 AI 技能有哪些？",
    ],
    "岗位市场概览": [
        "按需求评分排名前 5 的岗位类别是什么？",
        "哪些城市的 AI 岗位数量最多？",
        "LLM 相关岗位占比是多少？",
        "数据库中一共有多少条岗位记录？",
    ],
}

EXAMPLE_QUERIES = [
    {
        "question": "岗位数量排名前 10 的技能",
        "sql": 'SELECT skill AS "Skill", COUNT(*) AS "Job Count" FROM job_skills GROUP BY skill ORDER BY COUNT(*) DESC LIMIT 10',
        "chart": "bar",
    },
    {
        "question": "不同经验级别的平均薪资",
        "sql": 'SELECT experience_level AS "Experience", ROUND(AVG(annual_salary_usd)) AS "Avg Salary" FROM job_postings GROUP BY experience_level ORDER BY AVG(annual_salary_usd) DESC',
        "chart": "bar",
    },
    {
        "question": "各岗位类别的岗位数量",
        "sql": 'SELECT job_category AS "Category", COUNT(*) AS "Count" FROM job_postings GROUP BY job_category ORDER BY COUNT(*) DESC',
        "chart": "pie",
    },
    {
        "question": "远程与现场岗位数量对比",
        "sql": 'SELECT remote_work AS "Work Type", COUNT(*) AS "Count" FROM job_postings GROUP BY remote_work ORDER BY COUNT(*) DESC',
        "chart": "pie",
    },
    {
        "question": "岗位数量排名前 10 的城市",
        "sql": 'SELECT city AS "City", COUNT(*) AS "Count" FROM job_postings WHERE city != "" GROUP BY city ORDER BY COUNT(*) DESC LIMIT 10',
        "chart": "bar",
    },
    {
        "question": "各岗位类别的薪资分布",
        "sql": 'SELECT job_category AS "Category", ROUND(AVG(annual_salary_usd)) AS "Avg Salary", ROUND(MIN(annual_salary_usd)) AS "Min", ROUND(MAX(annual_salary_usd)) AS "Max" FROM job_postings GROUP BY job_category ORDER BY AVG(annual_salary_usd) DESC',
        "chart": "bar",
    },
    {
        "question": "不同发布年份的岗位数量",
        "sql": 'SELECT posting_year AS "Year", COUNT(*) AS "Count" FROM job_postings GROUP BY posting_year ORDER BY posting_year',
        "chart": "line",
    },
    {
        "question": "LLM 与非 LLM 岗位薪资对比",
        "sql": 'SELECT CASE WHEN is_llm_role = 1 THEN "LLM Role" ELSE "Non-LLM" END AS "Role Type", ROUND(AVG(annual_salary_usd)) AS "Avg Salary" FROM job_postings GROUP BY is_llm_role',
        "chart": "bar",
    },
]

PLACEHOLDER_TEXT = [q["question"] for q in EXAMPLE_QUERIES]

DATA_BROWSER_VISUALIZATIONS = {
    "job_categories": {
        "title": "各岗位类别的岗位数量",
        "sql": 'SELECT category AS "Category", job_count AS "Job Count" FROM job_categories ORDER BY job_count DESC',
        "chart": "bar",
    },
    "experience_levels": {
        "title": "不同经验级别的平均薪资",
        "sql": 'SELECT level AS "Experience Level", avg_salary AS "Avg Salary" FROM experience_levels ORDER BY avg_salary DESC',
        "chart": "bar",
    },
    "location_summary": {
        "title": "岗位数量排名前 10 的城市",
        "sql": 'SELECT city AS "City", SUM(job_count) AS "Job Count" FROM location_summary WHERE city != "" GROUP BY city ORDER BY SUM(job_count) DESC LIMIT 10',
        "chart": "bar",
    },
    "job_skills": {
        "title": "需求排名前 15 的技能",
        "sql": 'SELECT skill AS "Skill", COUNT(*) AS "Job Count" FROM job_skills GROUP BY skill ORDER BY COUNT(*) DESC LIMIT 15',
        "chart": "bar",
    },
}

CHART_PALETTE = ["#0f766e", "#2f5f8f", "#b86b18", "#b54764", "#5b6b7a", "#7c6a42", "#3f7d5d", "#6d6a9f"]
CHART_TEXT = "#202936"
CHART_MUTED = "#667085"
CHART_GRID = "#d8dee6"


def execute_sql(sql: str) -> tuple[list, list, Optional[str]]:
    conn = None
    try:
        validate_readonly_sql(sql)
        db_uri = f"file:{DB_PATH.resolve().as_posix()}?mode=ro"
        conn = sqlite3.connect(db_uri, uri=True)
        conn.execute("PRAGMA query_only=ON")
        cursor = conn.execute(sql)
        columns = [desc[0] for desc in cursor.description] if cursor.description else []
        rows = cursor.fetchall()
        return columns, rows, None
    except Exception as e:
        return [], [], str(e)
    finally:
        if conn:
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


def render_metric_card(rows: list, columns: list):
    if len(rows) != 1 or len(columns) < 2:
        return
    row = rows[0]
    for i in range(1, len(columns)):
        label = columns[i]
        value = row[i]
        if isinstance(value, float):
            value = f"{value:,.2f}"
        elif isinstance(value, int):
            value = f"{value:,}"
        st.metric(label=label, value=value)


def auto_detect_chart(sql: str, columns: list, rows: list) -> str:
    sql_upper = sql.upper()
    column_names = [str(c).lower() for c in columns]

    if len(rows) <= 1:
        return None

    has_temporal = any(kw in sql_upper for kw in ["YEAR", "MONTH", "POSTING_YEAR", "POSTING_MONTH"])

    if has_temporal:
        has_year_col = any("year" in c for c in column_names)
        has_group_col = any(k in c for c in column_names for k in ["skill", "technology", "tech"])
        if has_year_col and has_group_col and len(columns) >= 4:
            return "grouped_trend"

        salary_kw = ["SALARY", "COMPENSATION", "PAY", "WAGE", "INCOME", "EARN"]
        count_kw = ["COUNT", "JOB", "DEMAND", "OPENING", "NUMBER"]
        has_salary = any(k in sql_upper for k in salary_kw)
        has_count = any(k in sql_upper for k in count_kw)
        if has_salary and has_count:
            return "dual_axis"
        return "trend"

    if "GROUP BY" in sql_upper and "COUNT" in sql_upper:
        return "pie" if len(rows) <= 8 else "bar"

    if any(fn in sql_upper for fn in ["AVG", "SUM", "MIN", "MAX"]):
        return "bar"

    if "ORDER BY" in sql_upper and len(rows) <= 20:
        return "bar"

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


def _setup_font():
    plt.rcParams["font.family"] = "sans-serif"
    plt.rcParams["font.sans-serif"] = [
        "Microsoft YaHei",
        "SimHei",
        "Noto Sans CJK SC",
        "Source Han Sans SC",
        "WenQuanYi Micro Hei",
        "Arial Unicode MS",
        "DejaVu Sans",
    ]
    plt.rcParams["axes.unicode_minus"] = False
    plt.rcParams["figure.facecolor"] = "#ffffff"
    plt.rcParams["axes.facecolor"] = "#ffffff"
    plt.rcParams["text.color"] = CHART_TEXT
    plt.rcParams["axes.labelcolor"] = CHART_MUTED
    plt.rcParams["xtick.color"] = CHART_MUTED
    plt.rcParams["ytick.color"] = CHART_MUTED


def _style_chart(fig, ax, title: str):
    fig.patch.set_facecolor("#ffffff")
    ax.set_facecolor("#ffffff")
    ax.set_title(title, loc="left", fontsize=13, fontweight="bold", color=CHART_TEXT, pad=14)
    ax.tick_params(labelsize=9, colors=CHART_MUTED)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_color(CHART_GRID)
    ax.spines["bottom"].set_color(CHART_GRID)


def _find_col(columns: list, keywords: list[str]) -> str | None:
    for c in columns:
        if any(k in c.lower() for k in keywords):
            return c
    return None


def draw_dual_axis_trend(df: pd.DataFrame, columns: list, title: str):
    x_col = columns[0]
    d = df.sort_values(x_col).copy()
    d[x_col] = d[x_col].astype(str)

    count_col = _find_col(columns[1:], ["count", "job", "demand", "opening", "number"])
    salary_col = _find_col(columns[1:], ["salary", "compensation", "pay", "wage", "income"])

    if not count_col:
        numeric_cols = [c for c in columns[1:] if pd.api.types.is_numeric_dtype(df[c])]
        count_col = numeric_cols[0] if numeric_cols else columns[1]
    if not salary_col:
        numeric_cols = [c for c in columns[1:] if pd.api.types.is_numeric_dtype(df[c])]
        salary_col = [c for c in numeric_cols if c != count_col][0] if len(numeric_cols) > 1 else None

    count_vals = pd.to_numeric(d[count_col], errors="coerce").fillna(0).values.astype(float)

    fig, ax1 = plt.subplots(figsize=(10, 5))
    x_pos = range(len(d))
    ax1.bar(x_pos, count_vals, color=CHART_PALETTE[1], alpha=0.82, label=count_col)
    ax1.set_xlabel(columns[0], fontsize=10, color=CHART_MUTED)
    ax1.set_ylabel(count_col, fontsize=10, color=CHART_PALETTE[1])
    ax1.set_xticks(list(x_pos))
    ax1.set_xticklabels(d[x_col].values, rotation=45, ha="right")
    ax1.tick_params(axis="y", labelcolor=CHART_MUTED)
    ax1.grid(axis="y", color=CHART_GRID, alpha=0.55, linewidth=0.8)
    ax1.spines["top"].set_visible(False)

    if salary_col:
        salary_vals = pd.to_numeric(d[salary_col], errors="coerce").fillna(0).values.astype(float)
        ax2 = ax1.twinx()
        ax2.plot(list(x_pos), salary_vals, color=CHART_PALETTE[2], marker="o", linewidth=2.2, markersize=5, label=salary_col)
        ax2.set_ylabel(salary_col, fontsize=10, color=CHART_PALETTE[2])
        ax2.tick_params(axis="y", labelcolor=CHART_MUTED)
        ax2.spines["top"].set_visible(False)
        ax2.spines["right"].set_color(CHART_GRID)
        lines1, labels1 = ax1.get_legend_handles_labels()
        lines2, labels2 = ax2.get_legend_handles_labels()
        ax1.legend(lines1 + lines2, labels1 + labels2, loc="upper left", frameon=False, fontsize=9)
    else:
        ax1.legend(frameon=False, fontsize=9)

    _style_chart(fig, ax1, title)
    fig.tight_layout()
    return fig


def draw_pure_trend(df: pd.DataFrame, columns: list, title: str):
    x_col = columns[0]
    d = df.sort_values(x_col).copy()
    d[x_col] = d[x_col].astype(str)

    numeric_cols = [c for c in columns[1:] if pd.api.types.is_numeric_dtype(df[c])]

    fig, ax = plt.subplots(figsize=(10, 5))
    for i, y_col in enumerate(numeric_cols):
        vals = pd.to_numeric(d[y_col], errors="coerce").fillna(0).values.astype(float)
        ax.plot(d[x_col].values, vals, marker="o", linewidth=2, markersize=6,
                color=CHART_PALETTE[i % len(CHART_PALETTE)], label=y_col)
    if len(numeric_cols) > 1:
        ax.legend(frameon=False, fontsize=9)
    ax.set_xlabel(x_col, fontsize=10, color=CHART_MUTED)
    ax.set_ylabel(numeric_cols[0] if numeric_cols else "", fontsize=10, color=CHART_MUTED)
    ax.grid(axis="y", color=CHART_GRID, alpha=0.55, linewidth=0.8)
    _style_chart(fig, ax, title)
    plt.xticks(rotation=45, ha="right")
    fig.tight_layout()
    return fig


def draw_grouped_trend(df: pd.DataFrame, columns: list, title: str):
    x_col = _find_col(columns, ["year", "month"]) or columns[0]
    group_col = _find_col(columns, ["skill", "technology", "tech", "category", "type", "level"]) or columns[1]
    count_col = _find_col(columns, ["count", "job", "demand", "opening", "number"])
    salary_col = _find_col(columns, ["salary", "compensation", "pay", "wage", "income"])

    d = df.copy()
    d[x_col] = d[x_col].astype(str)
    if not count_col:
        numeric_cols = [c for c in columns if c not in {x_col, group_col} and pd.api.types.is_numeric_dtype(df[c])]
        count_col = numeric_cols[0] if numeric_cols else columns[2]

    pivot_count = d.pivot(index=x_col, columns=group_col, values=count_col).sort_index()

    fig, ax1 = plt.subplots(figsize=(10, 5))
    pivot_count.plot(kind="bar", ax=ax1, color=CHART_PALETTE[: len(pivot_count.columns)], width=0.68)
    ax1.set_xlabel(x_col, fontsize=10, color=CHART_MUTED)
    ax1.set_ylabel(count_col, fontsize=10, color=CHART_PALETTE[1])
    ax1.tick_params(axis="x", rotation=0)
    ax1.grid(axis="y", color=CHART_GRID, alpha=0.55, linewidth=0.8)

    handles, labels = ax1.get_legend_handles_labels()
    legend_title = group_col

    if salary_col:
        ax2 = ax1.twinx()
        for i, (skill, skill_df) in enumerate(d.groupby(group_col)):
            skill_df = skill_df.sort_values(x_col)
            ax2.plot(
                skill_df[x_col].astype(str).values,
                pd.to_numeric(skill_df[salary_col], errors="coerce").values.astype(float),
                color=CHART_PALETTE[(i + 2) % len(CHART_PALETTE)],
                marker="o",
                linewidth=2,
                markersize=5,
                linestyle="--",
                label=f"{skill} {salary_col}",
            )
        ax2.set_ylabel(salary_col, fontsize=10, color=CHART_PALETTE[2])
        ax2.tick_params(axis="y", labelcolor=CHART_MUTED)
        ax2.spines["top"].set_visible(False)
        ax2.spines["right"].set_color(CHART_GRID)
        line_handles, line_labels = ax2.get_legend_handles_labels()
        handles += line_handles
        labels += line_labels
        legend_title = None

    _style_chart(fig, ax1, title)
    ax1.legend(handles, labels, title=legend_title, frameon=False, fontsize=9, title_fontsize=9, loc="upper left")
    fig.tight_layout()
    return fig


def draw_categorical_bar(df: pd.DataFrame, columns: list, title: str, chart_type: str):
    x_col = columns[0]
    d = df.head(25).copy()
    d[x_col] = d[x_col].astype(str).str[:30]
    numeric_cols = [c for c in columns[1:] if pd.api.types.is_numeric_dtype(df[c])]

    if chart_type == "pie" and len(numeric_cols) == 1 and len(d) <= 10:
        fig, ax = plt.subplots(figsize=(9, 5.2))
        vals = pd.to_numeric(d[numeric_cols[0]], errors="coerce").fillna(0).values.astype(float)
        colors = [CHART_PALETTE[i % len(CHART_PALETTE)] for i in range(len(d))]
        wedges, _ = ax.pie(
            vals,
            labels=None,
            startangle=90,
            colors=colors,
            counterclock=False,
            wedgeprops={"width": 0.42, "edgecolor": "#ffffff", "linewidth": 2},
        )
        total = vals.sum()
        legend_labels = [
            f"{label}  {value / total:.1%}" if total else f"{label}  0.0%"
            for label, value in zip(d[x_col].values, vals)
        ]
        ax.text(0, 0, numeric_cols[0], ha="center", va="center", fontsize=10, color=CHART_MUTED)
        ax.set_title(title, loc="left", fontsize=13, fontweight="bold", color=CHART_TEXT, pad=14)
        ax.legend(
            wedges,
            legend_labels,
            loc="center left",
            bbox_to_anchor=(1.02, 0.5),
            frameon=False,
            fontsize=10,
            labelspacing=1.05,
            handlelength=1.1,
        )
        fig.tight_layout(rect=(0, 0, 0.78, 1))
        return fig

    y_col = numeric_cols[0] if numeric_cols else columns[1]
    vals = pd.to_numeric(d[y_col], errors="coerce").fillna(0).values.astype(float)

    fig, ax = plt.subplots(figsize=(10, max(4, len(d) * 0.4)))
    colors = [CHART_PALETTE[i % len(CHART_PALETTE)] for i in range(len(d))]
    ax.barh(d[x_col].values, vals, color=colors)
    ax.set_xlabel(y_col, fontsize=10, color=CHART_MUTED)
    ax.invert_yaxis()
    ax.grid(axis="x", color=CHART_GRID, alpha=0.55, linewidth=0.8)
    _style_chart(fig, ax, title)
    fig.tight_layout()
    return fig


def render_chart(chart_type: str, columns: list, rows: list, title: str, sql: str = ""):
    if not rows or not columns:
        return
    plt.close("all")
    _setup_font()
    df = pd.DataFrame(rows, columns=columns)

    fig = None

    if chart_type == "grouped_trend" and len(columns) >= 4:
        fig = draw_grouped_trend(df, columns, title)

    elif chart_type == "dual_axis" and len(columns) >= 3:
        fig = draw_dual_axis_trend(df, columns, title)

    elif chart_type == "trend" and len(columns) >= 2:
        fig = draw_pure_trend(df, columns, title)

    elif chart_type in ("bar", "pie") and len(columns) >= 2:
        fig = draw_categorical_bar(df, columns, title, chart_type)

    elif chart_type == "scatter" and len(columns) >= 2:
        x_col, y_col = columns[0], columns[1]
        d = df.head(50).copy()
        d[x_col] = pd.to_numeric(d[x_col], errors="coerce")
        d[y_col] = pd.to_numeric(d[y_col], errors="coerce")
        fig, ax = plt.subplots(figsize=(8, 6))
        ax.scatter(d[x_col].values, d[y_col].values, alpha=0.78, s=52, c=CHART_PALETTE[1], edgecolors="white", linewidth=0.7)
        ax.set_xlabel(x_col, fontsize=10, color=CHART_MUTED)
        ax.set_ylabel(y_col, fontsize=10, color=CHART_MUTED)
        ax.grid(color=CHART_GRID, alpha=0.45, linewidth=0.8)
        _style_chart(fig, ax, title)
        fig.tight_layout()

    if fig:
        st.pyplot(fig)
        plt.close(fig)


def main():
    st.set_page_config(page_title="AI 岗位市场分析智能体", page_icon="chart_with_upwards_trend", layout="wide")

    st.markdown("""
    <style>
    :root {
        --page-bg: #f4f6f8;
        --panel-bg: #ffffff;
        --ink: #202936;
        --muted: #667085;
        --line: #d8dee6;
        --teal: #0f766e;
        --teal-dark: #115e59;
        --blue: #2f5f8f;
        --amber: #b86b18;
        --rose: #b54764;
        --soft-teal: #e6f3ef;
        --soft-blue: #e9f0f7;
        --shadow: 0 14px 34px rgba(32, 41, 54, 0.08);
    }

    .stApp {
        background: var(--page-bg);
        color: var(--ink);
    }

    .block-container {
        max-width: 1180px;
        padding-top: 1.35rem;
        padding-bottom: 1.8rem;
    }

    .app-hero {
        background: var(--panel-bg);
        border: 1px solid var(--line);
        border-left: 5px solid var(--teal);
        border-radius: 8px;
        box-shadow: var(--shadow);
        padding: 1rem 1.25rem;
        margin-bottom: 1.35rem;
    }

    .app-eyebrow {
        color: var(--teal-dark);
        font-size: 0.76rem;
        font-weight: 800;
        letter-spacing: 0;
        margin-bottom: 0.3rem;
    }

    .app-title {
        color: var(--ink);
        font-size: 2rem;
        font-weight: 800;
        letter-spacing: 0 !important;
        line-height: 1.18;
        margin: 0;
    }

    h2, h3 {
        color: var(--ink);
        letter-spacing: 0 !important;
        font-weight: 760 !important;
    }

    section[data-testid="stSidebar"] {
        background: #edf1f4;
        border-right: 1px solid var(--line);
    }

    section[data-testid="stSidebar"] h2,
    section[data-testid="stSidebar"] h3 {
        font-size: 1rem !important;
        color: var(--ink);
    }

    section[data-testid="stSidebar"] [data-testid="stMetric"] {
        background: rgba(255, 255, 255, 0.82);
        border: 1px solid rgba(216, 222, 230, 0.9);
        border-radius: 6px;
        padding: 0.55rem 0.65rem;
    }

    div[data-testid="stForm"] {
        position: sticky;
        top: 0;
        z-index: 999;
        background: rgba(244, 246, 248, 0.96);
        padding: 0.9rem 0 1rem;
        border-bottom: 1px solid var(--line);
        backdrop-filter: blur(8px);
    }

    div[data-testid="stForm"] input {
        border-radius: 6px;
        border-color: var(--line);
    }

    div[data-testid="stForm"] input:focus {
        border-color: var(--teal);
        box-shadow: 0 0 0 1px var(--teal);
    }

    div[data-testid="stButton"] > button,
    div[data-testid="stFormSubmitButton"] > button {
        border-radius: 6px;
        border: 1px solid rgba(15, 118, 110, 0.24);
        background: var(--panel-bg);
        color: var(--teal-dark);
        font-weight: 650;
        min-height: 2.35rem;
        box-shadow: 0 1px 2px rgba(32, 41, 54, 0.04);
    }

    div[data-testid="stFormSubmitButton"] > button[kind="primary"],
    div[data-testid="stButton"] > button:hover,
    div[data-testid="stFormSubmitButton"] > button:hover {
        background: var(--teal);
        color: #ffffff;
        border-color: var(--teal);
    }

    div[data-testid="stTabs"] [role="tablist"] {
        display: grid;
        grid-template-columns: repeat(3, minmax(0, 1fr));
        gap: 0.55rem;
        background: #e8edf1;
        border: 1px solid var(--line);
        border-radius: 8px;
        padding: 0.35rem;
        margin-bottom: 1rem;
    }

    button[data-baseweb="tab"] {
        width: 100%;
        min-height: 2.75rem;
        justify-content: center;
        background: transparent;
        border-radius: 6px;
        color: var(--muted);
        font-weight: 760;
        border: 1px solid transparent;
        margin: 0;
    }

    button[data-baseweb="tab"][aria-selected="true"] {
        color: var(--teal-dark);
        background: #ffffff;
        border-color: var(--line);
        box-shadow: 0 6px 16px rgba(32, 41, 54, 0.08);
    }

    div[data-testid="stDataFrame"],
    div[data-testid="stStatus"],
    div[data-testid="stExpander"] {
        border-radius: 6px;
    }

    div[data-testid="stStatus"] {
        border: 1px solid var(--line);
        background: #ffffff;
    }

    .stAlert {
        border-radius: 6px;
    }

    div[data-testid="stExpander"] {
        border: 1px solid var(--line);
        background: #ffffff;
    }

    div[data-testid="stDataFrame"] {
        border: 1px solid var(--line);
        box-shadow: 0 8px 22px rgba(32, 41, 54, 0.05);
    }

    div[data-testid="stMarkdownContainer"] code {
        border-radius: 4px;
    }

    .app-footer {
        margin: 2.6rem auto 0;
        padding-top: 1rem;
        border-top: 1px solid var(--line);
        color: var(--muted);
        text-align: center;
        font-size: 0.78rem;
        line-height: 1.7;
    }

    @media (max-width: 900px) {
        .app-title {
            font-size: 1.6rem;
        }
    }
    </style>
    """, unsafe_allow_html=True)

    table_info = get_table_info() if DB_PATH.exists() else {}

    st.markdown(
        """
        <section class="app-hero">
            <div class="app-eyebrow">AI 岗位市场 · 数据工作台</div>
            <div class="app-title">AI 岗位市场数据分析智能体</div>
        </section>
        """,
        unsafe_allow_html=True,
    )

    with st.sidebar:
        st.header("大模型引擎")
        engine = st.radio("选择推理引擎：", ["DeepSeek（云端）", "本地 GPU（llama.cpp）"], index=0)
        engine_key = "deepseek" if "DeepSeek" in engine else "local"

        if engine_key == "deepseek":
            api_key = st.text_input("DeepSeek API Key", value=os.getenv("DEEPSEEK_API_KEY", ""), type="password")
            if api_key:
                os.environ["DEEPSEEK_API_KEY"] = api_key
            st.caption("默认模型：通过 api.deepseek.com 调用 deepseek-chat")
        else:
            local_url = st.text_input("本地 LLM 地址", value=os.getenv("LOCAL_LLM_URL", "http://127.0.0.1:8080/v1"))
            st.caption("请确认本地 llama-server 已启动（见 AGENTS.md）")

        st.divider()
        st.header("数据库概览")
        if DB_PATH.exists():
            for table, count in table_info.items():
                st.metric(table, f"{count:,} 行")
        else:
            st.error("未找到数据库。请先运行：`python3 scripts/init_db.py`")

    tab1, tab2, tab3 = st.tabs(["智能问答", "数据浏览", "预置分析"])

    with tab1:
        # Input at top — always visible
        if "form_key" not in st.session_state:
            st.session_state.form_key = 0

        with st.form(key=f"query_form_{st.session_state.form_key}", clear_on_submit=False):
            question = st.text_input("请输入关于 AI 岗位市场的问题：", placeholder="例如：需求最高的 10 项技能是什么？")
            submitted = st.form_submit_button("搜索", type="primary")

        if submitted and question:
            status = st.status(f"正在分析：{question}...", expanded=True)
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
                    status.update(label="查询失败", state="error")
                    st.error(f"SQL 错误：{error}")
                    if sql:
                        st.code(sql, language="sql")
                else:
                    status.update(label="分析完成", state="complete")
                    st.code(sql, language="sql")
                    df = pd.DataFrame(rows, columns=columns)
                    st.dataframe(df, use_container_width=True)
                    chart_type = auto_detect_chart(sql, columns, rows)
                    if chart_type and rows:
                        st.subheader("可视化")
                        render_chart(chart_type, columns, rows, make_chart_title(sql, columns), sql)
                    elif len(rows) == 1:
                        render_metric_card(rows, columns)
                    if rows:
                        st.subheader("AI 总结")
                        st.markdown(summarize_with_llm(llm, question, sql, columns, rows))
            except Exception as e:
                status.update(label="发生错误", state="error")
                st.error(f"错误：{str(e)}")
                if engine_key == "local":
                    st.info("请确认本地 LLM 服务已启动（见 AGENTS.md）")
                else:
                    st.info("请检查 DeepSeek API Key 和网络连接")

        # Example buttons below input
        st.divider()
        st.caption("快捷示例：点击后直接运行")
        cols = st.columns(4)
        for i, eq in enumerate(EXAMPLE_QUERIES[:4]):
            with cols[i]:
                if st.button(eq["question"], key=f"example_{i}"):
                    st.session_state.selected_example = i
                    st.session_state.form_key += 1
                    st.rerun()

        # Handle example selection
        if "selected_example" in st.session_state:
            idx = st.session_state.pop("selected_example")
            eq = EXAMPLE_QUERIES[idx]
            status = st.status(f"正在运行：{eq['question']}...", expanded=True)
            try:
                columns, rows, error = execute_sql(eq["sql"])
                if error:
                    status.update(label="查询失败", state="error")
                    st.error(f"SQL 错误：{error}")
                else:
                    status.update(label="运行完成", state="complete")
                    st.code(eq["sql"], language="sql")
                    df = pd.DataFrame(rows, columns=columns)
                    st.dataframe(df, use_container_width=True)
                    if eq.get("chart") and rows:
                        st.subheader("可视化")
                        render_chart(eq["chart"], columns, rows, eq["question"], eq["sql"])
            except Exception as e:
                status.update(label="发生错误", state="error")
                st.error(f"错误：{str(e)}")

    with tab2:
        st.subheader("数据浏览")
        if DB_PATH.exists():
            tables = list(table_info.keys())
            selected = st.selectbox("选择数据表", tables)
            if selected:
                df = get_table_dataframe(selected, limit=200)
                st.dataframe(df, use_container_width=True)
                st.caption(f"最多显示 200 行，共 {table_info[selected]:,} 行")
                viz = DATA_BROWSER_VISUALIZATIONS.get(selected)
                if viz:
                    columns, rows, error = execute_sql(viz["sql"])
                    if error:
                        st.error(f"可视化查询失败：{error}")
                    elif rows:
                        st.subheader(viz["title"])
                        render_chart(viz["chart"], columns, rows, viz["title"], viz["sql"])

    with tab3:
        st.subheader("预置分析场景")
        for category, questions in SAMPLE_QUESTIONS.items():
            with st.expander(f"{category}", expanded=False):
                for q in questions:
                    if st.button(q, key=f"preset_{q}"):
                        with st.spinner("正在查询..."):
                            try:
                                llm = get_llm(engine_key)
                                sql = generate_sql_with_llm(llm, q)
                                columns, rows, error = execute_sql(sql)
                                if not error and rows:
                                    st.markdown(f"**问题：** {q}")
                                    st.code(sql, language="sql")
                                    st.dataframe(pd.DataFrame(rows, columns=columns), use_container_width=True)
                                    chart_type = auto_detect_chart(sql, columns, rows)
                                    if chart_type:
                                        render_chart(chart_type, columns, rows, make_chart_title(sql, columns), sql)
                                    elif len(rows) == 1:
                                        render_metric_card(rows, columns)
                                    st.markdown(f"**回答：** {summarize_with_llm(llm, q, sql, columns, rows)}")
                                else:
                                    st.error(f"错误：{error}" if error else "没有查询结果")
                            except Exception as e:
                                st.error(f"错误：{str(e)}")

    st.markdown(
        '<div class="app-footer">基于 LangChain、SQLite 与大语言模型，对 2025-2026 年 AI 岗位市场数据进行自然语言分析。</div>',
        unsafe_allow_html=True,
    )


if __name__ == "__main__":
    main()
