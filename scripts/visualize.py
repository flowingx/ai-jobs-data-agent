import sqlite3
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

DB_PATH = Path(__file__).parent.parent / "db" / "careers.db"
OUTPUT_DIR = Path(__file__).parent.parent / "data" / "charts"

plt.rcParams["font.sans-serif"] = ["SimHei", "Microsoft YaHei", "DejaVu Sans"]
plt.rcParams["axes.unicode_minus"] = False


def get_data(sql):
    conn = sqlite3.connect(str(DB_PATH))
    df = pd.read_sql_query(sql, conn)
    conn.close()
    return df


def chart_skill_demand():
    df = get_data("""
        SELECT skill, COUNT(DISTINCT job_id) as job_count
        FROM job_skill_map
        GROUP BY skill
        ORDER BY job_count DESC
        LIMIT 15
    """)
    fig, ax = plt.subplots(figsize=(12, 6))
    colors = plt.cm.viridis(range(len(df)))
    bars = ax.barh(df["skill"], df["job_count"], color=colors)
    ax.set_xlabel("Job Count")
    ax.set_title("Top 15 Skills by Job Demand")
    ax.invert_yaxis()
    for bar, val in zip(bars, df["job_count"]):
        ax.text(bar.get_width() + 0.5, bar.get_y() + bar.get_height() / 2, str(val), va="center", fontsize=9)
    plt.tight_layout()
    path = OUTPUT_DIR / "skill_demand.png"
    fig.savefig(path, dpi=150)
    plt.close(fig)
    print(f"Saved: {path}")


def chart_skill_trends():
    df = get_data("SELECT skill, trend_score, signal FROM skill_trends ORDER BY trend_score DESC")
    fig, ax = plt.subplots(figsize=(12, 6))
    colors = ["#FF6B6B" if s == "上升" else "#4ECDC4" for s in df["signal"]]
    bars = ax.barh(df["skill"], df["trend_score"], color=colors)
    ax.set_xlabel("Trend Score")
    ax.set_title("Skill Trend Scores")
    ax.invert_yaxis()
    ax.set_xlim(0, 100)
    for bar, val, sig in zip(bars, df["trend_score"], df["signal"]):
        ax.text(bar.get_width() + 1, bar.get_y() + bar.get_height() / 2, f"{val} ({sig})", va="center", fontsize=9)
    plt.tight_layout()
    path = OUTPUT_DIR / "skill_trends.png"
    fig.savefig(path, dpi=150)
    plt.close(fig)
    print(f"Saved: {path}")


def chart_category_distribution():
    df = get_data("SELECT category, COUNT(*) as cnt FROM raw_jobs GROUP BY category ORDER BY cnt DESC")
    fig, ax = plt.subplots(figsize=(10, 6))
    colors = plt.cm.Set3(range(len(df)))
    wedges, texts, autotexts = ax.pie(df["cnt"], labels=df["category"], autopct="%1.1f%%", colors=colors, startangle=90)
    ax.set_title("Job Category Distribution")
    plt.tight_layout()
    path = OUTPUT_DIR / "category_distribution.png"
    fig.savefig(path, dpi=150)
    plt.close(fig)
    print(f"Saved: {path}")


def chart_province_jobs():
    df = get_data("SELECT province, COUNT(*) as cnt FROM raw_jobs GROUP BY province ORDER BY cnt DESC")
    fig, ax = plt.subplots(figsize=(10, 6))
    colors = plt.cm.Paired(range(len(df)))
    bars = ax.bar(df["province"], df["cnt"], color=colors)
    ax.set_xlabel("Province")
    ax.set_ylabel("Job Count")
    ax.set_title("Jobs by Province")
    for bar, val in zip(bars, df["cnt"]):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.5, str(val), ha="center", fontsize=10)
    plt.tight_layout()
    path = OUTPUT_DIR / "province_jobs.png"
    fig.savefig(path, dpi=150)
    plt.close(fig)
    print(f"Saved: {path}")


def chart_salary_by_category():
    df = get_data("""
        SELECT category, AVG(salary_floor_k) as avg_salary
        FROM raw_jobs WHERE salary_floor_k IS NOT NULL
        GROUP BY category ORDER BY avg_salary DESC
    """)
    fig, ax = plt.subplots(figsize=(10, 6))
    colors = plt.cm.RdYlGn(range(len(df)))
    bars = ax.barh(df["category"], df["avg_salary"], color=colors)
    ax.set_xlabel("Average Salary (K)")
    ax.set_title("Average Salary by Category")
    ax.invert_yaxis()
    for bar, val in zip(bars, df["avg_salary"]):
        ax.text(bar.get_width() + 0.2, bar.get_y() + bar.get_height() / 2, f"{val:.1f}K", va="center", fontsize=10)
    plt.tight_layout()
    path = OUTPUT_DIR / "salary_by_category.png"
    fig.savefig(path, dpi=150)
    plt.close(fig)
    print(f"Saved: {path}")


def chart_finance_distribution():
    df = get_data("SELECT job_finance, COUNT(*) as cnt FROM raw_jobs GROUP BY job_finance ORDER BY cnt DESC")
    fig, ax = plt.subplots(figsize=(10, 6))
    colors = plt.cm.Pastel1(range(len(df)))
    wedges, texts, autotexts = ax.pie(df["cnt"], labels=df["job_finance"], autopct="%1.1f%%", colors=colors, startangle=90)
    ax.set_title("Company Finance Stage Distribution")
    plt.tight_layout()
    path = OUTPUT_DIR / "finance_distribution.png"
    fig.savefig(path, dpi=150)
    plt.close(fig)
    print(f"Saved: {path}")


def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    print("=" * 60)
    print("Generating Job Market Visualization Charts")
    print("=" * 60)
    chart_skill_demand()
    chart_skill_trends()
    chart_category_distribution()
    chart_province_jobs()
    chart_salary_by_category()
    chart_finance_distribution()
    print("\nAll charts generated!")


if __name__ == "__main__":
    main()
